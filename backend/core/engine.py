"""
The run engine: seven stage functions plus run / approve / regenerate / skip.

THE ONE ARCHITECTURAL POINT

Every stage reads its inputs from the ARTIFACT STORE, never from a local
variable. That is the whole reason this can pause.

AUX's run_pipeline is a single async generator holding `requirements`, `spec`,
`placements`, `ts_code`, `js_code` and `token` in locals
(aux_web_version/backend/pipeline.py:381-802). A generator cannot be suspended
across HTTP requests, so a human gate is impossible inside it — which is why
Phase 2 is an orchestration rewrite rather than a UI feature.

THE GATE SITS BEFORE THE WRITE

A stage function produces two things: the artifact the dialog displays, and a
`commit` callable that performs the QAD writes. Running a stage does NOT write.
Approving is what calls `commit`. So the dialog always shows the exact payload
that is about to be sent, and dry-run renders identically to live — the only
difference is whether the request leaves the process.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from pathlib import Path

import qad_client
from core import config, llm, stages, store
from core.logging_setup import get_logger
from builders import event_handler_builder as ehb
from builders import lookup_builder as lkb
from builders import naming
from builders.bc_builder import build_bc_payload, patch_dropdown_fields
from builders.embedded_builder import build_embedded_entity_payload
from builders.deploy_builder import build_deploy_payload
from builders.form_builder import build_form_payload
from builders.identity import AppIdentity
from builders.view_builder import build_view_payload

logger = get_logger("adaptive.engine")


class StageError(RuntimeError):
    """A stage could not produce its artifact. Message is user-facing."""


@dataclass
class StageResult:
    """What running a stage produces, before anything is written."""
    artifact: Dict[str, Any]
    # async (dry_run: bool) -> list[QadResult]. None means the stage writes nothing.
    commit: Optional[Callable[[bool], Awaitable[List[Any]]]] = None
    skip: bool = False
    skip_reason: str = ""
    warnings: List[str] = dc_field(default_factory=list)


# ── Context: what earlier stages left behind ─────────────────────────────────
async def context(run_id: str, **db) -> Dict[str, Any]:
    """Assemble the approved outputs of every prior stage.

    Reads the LATEST attempt of each, which is what regeneration is for: a
    re-run of an upstream stage is picked up here automatically by everything
    downstream.
    """
    # Carried so a stage that must record a call while RENDERING (the deploy
    # warnings check) writes to the same database the caller is using.
    ctx: Dict[str, Any] = {"run_id": run_id, "_db": dict(db)}
    run = await store.get_run(run_id, **db)
    if not run:
        raise StageError(f"No run '{run_id}'.")
    ctx["run"] = run
    ctx["mode"] = run.get("mode") or "standard"
    ctx["user_input"] = run["user_input"]
    ctx["dry_run"] = run["dry_run"]
    for stage in stages.stage_list(ctx["mode"]):
        row = await store.get_stage(run_id, stage.id, **db)
        if row and row["artifact"]:
            ctx[stage.id] = row["artifact"]
    return ctx


def _docs_bundle(name: str) -> str:
    """Grounding docs for a prompt, wrapped with the heading prompts expect.

    Returns "" when the bundle is empty, so an absent bundle leaves no dangling
    heading behind. Whether a bundle is actually grounded is reported by
    `docs_loader.diagnose()` rather than left to be inferred from bad output.
    """
    from core.docs_loader import docs_loader
    return docs_loader.as_prompt_context(name)


def _need(ctx: Dict[str, Any], stage_id: str, what: str) -> Any:
    art = ctx.get(stage_id)
    if not art or what not in art:
        raise StageError(
            f"Stage '{stage_id}' has not produced '{what}' yet. Run and approve it first."
        )
    return art[what]


def _abl_grounding(text: str) -> Optional[Dict[str, Any]]:
    """Parse pasted ABL source out of the user's input, when there is any.

    Deterministic and side-effect free. Returns the parse result or None; a
    missing parser module degrades to None rather than an error, so the app
    still runs while the parser port is landing.
    """
    try:
        from core import progress_parser as pp
    except ImportError:
        return None
    if not text or not pp.looks_like_abl(text):
        return None
    parsed = pp.parse_abl(text)
    return parsed if parsed.get("tables") else None


def _abl_prompt_block(parsed: Optional[Dict[str, Any]]) -> str:
    import json as _json
    if not parsed:
        return ""
    return (
        "PARSED ABL SCHEMA (deterministic, extracted from the source the user "
        "pasted - treat as the authoritative field list):\n"
        + _json.dumps(parsed["tables"], indent=1)
    )


# ── Stage 1: requirements ────────────────────────────────────────────────────
async def stage_requirements(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    from agents import prompts

    user = ctx["user_input"]
    abl = _abl_grounding(ctx["user_input"])
    if abl:
        user = f"{_abl_prompt_block(abl)}\n\n{user}"
    if instruction:
        user = f"{user}\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    text = await llm.complete(prompts.render(prompts.REQUIREMENTS_GATHERING),
                              user, role="planning")
    if not text.strip():
        raise StageError("The model returned an empty requirements summary.")

    return StageResult(artifact={
        "text": text.strip(),
        "source": "llm+abl" if abl else "llm",
        "abl_tables": (abl or {}).get("tables") or [],
        # Drives whether stage 4 runs at all. None means undetermined, and the
        # handler stage then proposes rather than skipping.
        "handler_hint": _handler_hint(text),
    })


def _handler_hint(requirements_text: str) -> Optional[bool]:
    """Read the HANDLER_NEEDED line the requirements prompt asks for.

    Returns True/False when the model answered, None when it did not. None is
    NOT treated as False: silently skipping the handler stage because a model
    forgot a line would lose real work without telling anyone.
    """
    import re as _re
    m = _re.search(r"HANDLER_NEEDED\s*:\s*(yes|no)", requirements_text, _re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower() == "yes"


# ── Stage 2: fields ──────────────────────────────────────────────────────────
async def stage_fields(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    from agents import prompts

    requirements = _need(ctx, "requirements", "text")
    user = requirements
    if instruction:
        user = f"{requirements}\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    parsed = llm.parse_json(
        await llm.complete(prompts.render(prompts.FIELD_CREATOR), user,
                          role="generation", json_mode=True)
    )
    spec = parsed.get("spec") if isinstance(parsed, dict) else None
    if not spec:
        raise StageError("The model did not return a `spec` object.")

    problems = naming.validate_spec(spec)
    if problems:
        raise StageError("The field design is not valid:\n  - " + "\n  - ".join(problems))

    ident = AppIdentity.from_config()
    built = build_bc_payload(spec, ident)

    # Surface every SQL-safe rename. Asking for `status` and silently getting a
    # column called `statusCode` is exactly the kind of surprise a gate exists
    # to prevent.
    renames = [
        {"asked_for": f["code"], "actual_column": naming.sql_safe(f["code"])}
        for f in spec["fields"] if naming.sql_safe(f["code"]) != f["code"]
    ]

    async def commit(dry_run: bool) -> List[Any]:
        results = []
        create = await qad_client.call("bc.create", payload=built["payload"], dry_run=dry_run)
        results.append(("bc.create", create))
        if not create.ok:
            return results

        # Dropdown wiring: QAD's Entity Builder needs a second save. GET the
        # enriched metadata, point each dropdown at its list, POST it back.
        if built["field_list_map"]:
            params = {"entity_uri": built["entity_uri"]}
            got = await qad_client.call("bc.metadata.read", params=params, dry_run=dry_run)
            results.append(("bc.metadata.read", got))
            if got.ok and not dry_run:
                body = got.data.get("data") if isinstance(got.data.get("data"), dict) else got.data
                if not body.get("entityMetadatas"):
                    return results
                patch_dropdown_fields(body, built["field_list_map"])
                wired = await qad_client.call("bc.metadata.write", payload=body,
                                              params=params, dry_run=dry_run)
                results.append(("bc.metadata.write", wired))
            elif dry_run:
                # Nothing was really read, so show what the second save would carry.
                preview = {"entityMetadatas": [{"entityFields": [
                    {"entityFieldCode": code, **info}
                    for code, info in built["field_list_map"].items()
                ]}]}
                wired = await qad_client.call("bc.metadata.write", payload=preview,
                                              params=params, dry_run=True)
                results.append(("bc.metadata.write", wired))
        return results

    return StageResult(
        artifact={
            "spec": spec,
            "bc_pascal": spec["bc_pascal"],
            "field_count": len(spec["fields"]),
            "renamed_fields": renames,
            "entity_uri": built["entity_uri"],
            "payload_preview": built["payload"],
            "summary": built["summary"],
        },
        commit=commit,
        warnings=[
            f"'{r['asked_for']}' is a SQL reserved word - the QAD column will be "
            f"'{r['actual_column']}'." for r in renames
        ],
    )


# ── Stage 3: form ────────────────────────────────────────────────────────────
async def stage_form(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    from agents import prompts
    import json as _json

    spec = _need(ctx, "fields", "spec")
    codes = [str(f["code"]) for f in spec["fields"]]

    plan = await llm.complete(prompts.render(prompts.FORM_PLANNER),
                              _json.dumps(spec["fields"]), role="planning")
    user = plan
    if instruction:
        user = f"{plan}\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    placements = _placements_from(
        llm.parse_json(await llm.complete(prompts.render(prompts.FORM_FIELD_BUILDER),
                                          user, role="generation", json_mode=True))
    )
    missing = [c for c in codes
               if c.strip().lower() not in {str(p.get("fieldName", "")).strip().lower()
                                            for p in placements}]
    if missing:
        # One corrective retry naming exactly what was dropped, as AUX does -
        # the model intermittently returns only the first field under json mode.
        retry = (
            f"{plan}\n\nCORRECTION - your previous answer was INCOMPLETE: it omitted "
            f"{', '.join(missing)}. Return ALL {len(codes)} fields: {', '.join(codes)}"
        )
        placements = _placements_from(
            llm.parse_json(await llm.complete(prompts.render(prompts.FORM_FIELD_BUILDER),
                                              retry, role="generation", json_mode=True))
        )

    ident = AppIdentity.from_config()
    built = build_form_payload(placements, spec, ident)  # raises if still incomplete

    async def commit(dry_run: bool) -> List[Any]:
        return [("form.save", await qad_client.call("form.save", payload=built["payload"],
                                                    dry_run=dry_run))]

    return StageResult(
        artifact={
            "plan": plan,
            "placements": placements,
            "panels": built["summary"]["panels"],
            "payload_preview": built["payload"],
            "summary": built["summary"],
        },
        commit=commit,
    )


def _placements_from(parsed: Any) -> List[Dict[str, Any]]:
    """Coerce the form-field builder's output into a flat placement list.

    json_mode forces a top-level OBJECT, so the model does not return the bare
    array the prompt asks for. Handles the shapes AUX documents observing
    (aux_web_version/backend/pipeline.py:256-351).
    """
    def flatten(panels: List[Any]) -> List[Dict[str, Any]]:
        out = []
        for i, panel in enumerate(panels, start=1):
            if not isinstance(panel, dict):
                continue
            pname = panel.get("panelName") or panel.get("name") or f"Panel {i}"
            pnum = panel.get("panel", i)
            for f in panel.get("fields", []) or []:
                if isinstance(f, dict):
                    out.append({
                        "fieldName": f.get("fieldName") or f.get("name"),
                        "panel": f.get("panel", pnum),
                        "panelName": f.get("panelName", pname),
                        "gridColumn": f.get("gridColumn", 0),
                        "gridRow": f.get("gridRow", 0),
                    })
        return out

    def is_panels(lst: Any) -> bool:
        return isinstance(lst, list) and bool(lst) and all(
            isinstance(x, dict) and "fields" in x for x in lst)

    def is_flat(lst: Any) -> bool:
        return isinstance(lst, list) and bool(lst) and all(
            isinstance(x, dict) and "fieldName" in x and "panel" in x for x in lst)

    if is_panels(parsed):
        return flatten(parsed)
    if is_flat(parsed):
        return parsed
    if isinstance(parsed, dict):
        for v in parsed.values():
            if is_panels(v):
                return flatten(v)
        for v in parsed.values():
            if is_flat(v):
                return v
    raise StageError(
        "The form-field builder did not return a usable placement list "
        f"(got {type(parsed).__name__})."
    )


# ── Stage 4: event handler (conditional) ─────────────────────────────────────
async def stage_handler(ctx: Dict[str, Any], instruction: str = "",
                        browse_uris: Optional[Dict[str, str]] = None) -> StageResult:
    from agents import prompts
    import json as _json

    spec = _need(ctx, "fields", "spec")
    placements = _need(ctx, "form", "placements")

    # Asks the same function the rail asks, so "will this stage run?" cannot be
    # answered one way in the UI and another here.
    if stages.applies("handler", ctx) is False:
        return StageResult(
            artifact={"needed": False},
            skip=True,
            skip_reason=("The requirements show no validation or event logic to port, so there "
                         "is nothing to write. An empty handler would only add noise in QAD."),
        )

    bc = spec["bc_pascal"]
    docs = _docs_bundle("client_extension_event_handler")
    plan = await llm.complete(
        prompts.render(prompts.EVENT_HANDLER_PLANNER, docs_context=docs),
        f"BC Name: {bc}\nDescription: {spec.get('description','')}\n"
        f"Fields: {_json.dumps(spec['fields'])}",
        role="planning",
    )

    user = (f"BC Name: {bc}\n\nEvent Handler Plan:\n{plan}\n\n"
            f"Field placements:\n{_json.dumps(placements)}")
    if instruction:
        user += f"\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    ts_raw = ehb.strip_fences(await llm.complete(
        prompts.render(prompts.TS_CODE_WRITER, docs_context=docs),
        user, role="generation"))
    placeholders = ehb.extract_placeholders(ts_raw)

    resolved = ehb.substitute_placeholders(ts_raw, browse_uris or {})
    ts_code = resolved["code"]

    artifact = {
        "plan": plan,
        "typescript": ts_code,
        "typescript_raw": ts_raw,
        "browse_placeholders": [p.to_dict() for p in placeholders],
        "browse_uris_supplied": browse_uris or {},
        "filled": resolved["filled"],
        "skipped": resolved["skipped"],
        "fully_resolved": resolved["fully_resolved"],
    }

    # Unfilled placeholders are not an error - the user may deliberately skip
    # them, exactly as AUX does by commenting the call out. They just cannot be
    # sent as-is, so the gate shows them and commit resolves them first.
    async def commit(dry_run: bool) -> List[Any]:
        js = await llm.complete(prompts.render(prompts.TS_COMPILER),
                                f"Compile this TypeScript to ES5 JavaScript:\n\n{ts_code}",
                                role="planning")
        built = ehb.build_event_handler_payload(bc, ts_code, js, timing="BEFORE",
                                                identity=AppIdentity.from_config())
        return [("eventhandler.register",
                 await qad_client.call("eventhandler.register",
                                       payload=built["payload"], dry_run=dry_run))]

    return StageResult(
        artifact=artifact,
        commit=commit,
        warnings=([f"No Browse URI supplied for {', '.join(resolved['skipped'])} - "
                   f"those lines are commented out, as AUX does."]
                  if resolved["skipped"] else []),
    )


# ── Stage 5: view (ungated, deterministic) ───────────────────────────────────
async def stage_view(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    spec = _need(ctx, "fields", "spec")
    built = build_view_payload(spec, AppIdentity.from_config())

    async def commit(dry_run: bool) -> List[Any]:
        return [("view.register", await qad_client.call("view.register",
                                                        payload=built["payload"],
                                                        dry_run=dry_run))]

    return StageResult(
        artifact={"summary": built["summary"], "payload_preview": built["payload"]},
        commit=commit,
    )


# ── Stage 6: lookups (conditional) ───────────────────────────────────────────
async def _browse_fields(browse_uri: str) -> List[Dict[str, Any]]:
    """The fields QAD says a browse offers, straight from its own picker."""
    if not browse_uri.strip():
        return []
    r = await qad_client.call("lookup.browse_fields", params={"browse_uri": browse_uri})
    return (r.data or {}).get("data") or [] if r.ok else []


def _resolve_field(supplied: str, offered: List[Dict[str, Any]], browse_uri: str) -> str:
    """Match what the user typed to a field QAD actually offers.

    Accepts the full dotted value, or just the column ('testCode'), or the
    label ('Test Code'). Returns QAD's exact string so the payload carries a
    value QAD authored rather than one we spelled.
    """
    want = (supplied or "").strip()
    if not want:
        raise StageError(f"No result field chosen for browse '{browse_uri}'.")
    if not offered:
        # The picker gave us nothing - pass the input through rather than block,
        # and let QAD have the final word.
        return want

    lowered = want.lower()
    for f in offered:
        if str(f.get("field", "")).lower() == lowered:
            return f["field"]
    for f in offered:
        column = str(f.get("field", "")).split(".", 1)[-1]
        if column.lower() == lowered or str(f.get("fieldLabel", "")).lower() == lowered:
            return f["field"]

    raise StageError(
        f"'{want}' is not a field on that browse. QAD offers: "
        + ", ".join(f"{f.get('field')} ({f.get('fieldLabel')})" for f in offered)
    )


async def stage_lookups(ctx: Dict[str, Any], instruction: str = "",
                        configs: Optional[List[Dict[str, Any]]] = None) -> StageResult:
    spec = _need(ctx, "fields", "spec")
    bc_payload = _need(ctx, "fields", "payload_preview")
    placements = _need(ctx, "form", "placements")
    ident = AppIdentity.from_config()

    wanted = [f for f in spec["fields"] if f.get("needsLookup") is True]
    if stages.applies("lookups", ctx) is False and not configs:
        return StageResult(
            artifact={"lookups": []},
            skip=True,
            skip_reason="No field was marked as needing a lookup at the field stage.",
        )

    uris = lkb.field_uris_from_bc_payload(bc_payload)
    bc = spec["bc_pascal"]

    # Until configured, offer the choices rather than guessing: which fields
    # want lookups, and what each could auto-populate.
    if not configs:
        return StageResult(artifact={
            "awaiting_configuration": True,
            "fields": [{
                "code": f["code"],
                "label": naming.to_display_label(f["code"]),
                "auto_populate_options": lkb.auto_populate_targets(
                    placements, bc, exclude_field=f["code"]),
            } for f in wanted],
            "hint": ("Point a lookup at a business component we created and the Browse URI, "
                     "Result Field and Search Field are all derived. Pointing at a standard "
                     "QAD component needs its Browse URI."),
        })

    built = []
    for cfg in configs:
        browse_uri = cfg.get("browse_uri", "")
        # ASK QAD WHICH FIELDS THAT BROWSE OFFERS, rather than deriving them.
        #
        # A live POST was rejected with "Invalid URI" because we built the
        # result field from the browse URI's last segment - 'digsmoketest' -
        # while QAD's own picker returns 'digSmokeTest.testCode', camelCase.
        # No naming rule was going to recover that reliably; QAD's list is the
        # only authority, so the user's input is RESOLVED against it.
        #
        # NOT on dry runs: a rehearsal is fully offline (found 2026-08-12 when
        # the network dropped mid-test and the "zero network calls" suite made
        # one). Inputs pass through unresolved and the artifact says so.
        offered = [] if ctx["dry_run"] else await _browse_fields(browse_uri)
        result_field = _resolve_field(cfg.get("result_field", ""), offered, browse_uri)
        search_field = _resolve_field(cfg.get("search_field", "") or cfg.get("result_field", ""),
                                      offered, browse_uri)
        browse = lkb.BrowseTarget(
            uri=browse_uri,
            label=cfg.get("browse_label", ""),
            entity=cfg.get("browse_entity", ""),
            result_field=result_field,
            search_field=search_field,
        )
        # Each fill's SOURCE column gets the same resolution as the result
        # field. Before 2026-08-12 the frontend defaulted every fill's source
        # to the main result field, which would have filled Order Date with a
        # test code; now it sends a per-fill column and QAD's list corrects
        # its case here.
        additional = [
            {"field": _resolve_field(str(r.get("field", "")), offered, browse_uri),
             "target": str(r.get("target", ""))}
            for r in cfg.get("additional_results", [])
        ]
        built.append(lkb.build_lookup_payload(
            lkb.LookupSpec(
                field_code=cfg["field_code"],
                browse=browse,
                additional_results=additional,
            ),
            spec, uris, ident))

    async def commit(dry_run: bool) -> List[Any]:
        out = []
        for b in built:
            out.append(("lookup.create",
                        await qad_client.call("lookup.create", payload=b["payload"],
                                              dry_run=dry_run)))
        return out

    return StageResult(
        artifact={
            "lookups": [b["summary"] for b in built],
            "payload_preview": [b["payload"] for b in built],
        },
        commit=commit,
        warnings=sorted({u for b in built for u in b["unverified"]})
        + (["Dry run: field names were not resolved against QAD's picker; a "
            "live run corrects their case before sending."]
           if ctx["dry_run"] else []),
    )


# ── Stage 7: deploy (terminal) ───────────────────────────────────────────────
async def stage_deploy(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    spec = _need(ctx, "fields", "spec")
    bc = spec["bc_pascal"]
    built = build_deploy_payload(bc, AppIdentity.from_config())
    dry_run = ctx["dry_run"]

    # Run the warnings check NOW so the gate can show what QAD actually said.
    # AUX fires this and throws the response away (pipeline.py:739).
    #
    # Audited but NON-LOCKING: this fires when the dialog is merely OPENED, not
    # when it is approved. Treating it as a locking write would freeze the whole
    # run the moment the user looked at the deploy screen.
    warn = await qad_client.call("deploy.check_warnings",
                                 payload=built["check_warnings"], dry_run=dry_run)
    await store.record_write(ctx["run_id"], "deploy", "deploy.check_warnings",
                             ok=warn.ok, dry_run=warn.dry_run, request=warn.request,
                             response=None if warn.dry_run else warn.data,
                             locking=False, **ctx.get("_db", {}))

    async def commit(inner_dry_run: bool) -> List[Any]:
        return [("deploy.business_entity",
                 await qad_client.call("deploy.business_entity", payload=built["deploy"],
                                       dry_run=inner_dry_run))]

    return StageResult(
        artifact={
            "bc_pascal": bc,
            "entity_uri": built["summary"]["entity_uri"],
            "warnings_response": warn.to_dict(),
            "payload_preview": built["deploy"],
            "terminal": True,
        },
        commit=commit,
        warnings=(["QAD's deployment warnings check did not succeed - read the response "
                   "before approving."] if not warn.ok else []),
    )


# ── Case 2: the embedded stages ──────────────────────────────────────────────
# Payload authority is captures/2026-08-12_embedded_EmbeddedExmpl2.md. The
# flow is deliberately smaller than Case 1: child BC + one relation + deploy,
# with a conditional experimental view. See PHASE3_CASE2_BUILD_PLAN.md.

def _e_requirements_artifact(req: Dict[str, Any],
                             abl: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    from core import parent_registry as pr

    key = str(req.get("parent_entity_key") or "")
    try:
        parent = pr.get(key)
    except KeyError:
        parent = None
    if parent is None or not parent.offerable:
        offered = ", ".join(p.key for p in pr.offerable())
        why = parent.not_offerable_because if parent else "it is not in the registry"
        raise StageError(
            f"'{key or '(none)'}' cannot be the parent - {why}. "
            f"Pick one of: {offered}. Regenerate with a steer, or choose a parent "
            f"in this dialog.")

    return {
        "requirements": req,
        "parent": parent.to_dict(),
        # The gate renders this as a picker: the LLM proposes, the human
        # disposes. AUX gave the user no say at all (discovery, Stale #10).
        "parent_options": [p.to_dict() for p in pr.offerable()],
        "abl_tables": (abl or {}).get("tables") or [],
    }


async def stage_e_requirements(ctx: Dict[str, Any], instruction: str = "",
                               parent_key: Optional[str] = None) -> StageResult:
    from agents import prompts
    from core import parent_registry as pr

    abl = _abl_grounding(ctx["user_input"])

    # A parent override from the gate is a deterministic swap, not a reason to
    # re-roll the whole requirements JSON.
    prev = (ctx.get("requirements") or {}).get("requirements")
    if parent_key and prev:
        req = dict(prev)
        req["parent_entity_key"] = parent_key
        return StageResult(artifact=_e_requirements_artifact(req, abl))

    # A bare re-run (no steer, no override) reuses what was shown. This is what
    # keeps a cold-cache approve honest: approve rebuilds through this path
    # after a process restart, and re-rolling the LLM here would approve an
    # artifact the user never saw - losing any parent override with it.
    if prev and not instruction:
        return StageResult(artifact=_e_requirements_artifact(dict(prev), abl))

    user = ctx["user_input"]
    if instruction:
        user = f"{user}\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    raw = await llm.complete(
        prompts.render(prompts.EMBEDDED_REQUIREMENTS_GATHERING,
                       docs_context=_docs_bundle("business_component"),
                       tokens={"ENTITY_MENU": pr.entity_menu_for_prompt(),
                               "ABL_SCHEMA": _abl_prompt_block(abl)}),
        user, role="planning", json_mode=True)
    req = llm.parse_json(raw)
    if not isinstance(req, dict) or not req.get("bc_pascal"):
        raise StageError("The model did not return a usable requirements object.")
    if parent_key:
        req["parent_entity_key"] = parent_key
    return StageResult(artifact=_e_requirements_artifact(req, abl))


def _mirror_parent_pks(spec_fields: List[Dict[str, Any]], pk_fields: List[Dict[str, str]],
                       child_pk: Dict[str, Any], bc: str
                       ) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Enforce the PK trio deterministically, whatever the model returned.

    The structure is platform law (the relation must map every parent PK, and
    the child PK must sit outside the FK), so it is not left to prompt
    compliance: mirrors + child PK are REBUILT here and the model's output only
    contributes the custom fields. Returns (fields, warnings).

    Fields carry BOTH PK spellings - `primaryKey` (ordinal, what the embedded
    payload sends) and `isPrimary` (boolean, what the shared view and form
    builders key off) - because two consumers with two conventions reading one
    spec was exactly how the embedded view stage crashed in review.
    """
    warns: List[str] = []

    # Every code entering the spec passes sql_safe HERE, once, and every
    # consumer (entity payload, data lists, relation, view) reads the spec
    # verbatim afterwards. It matters most for the domain mirror: QAD reserves
    # 'DomainCode' (sql_safe renames it domainCd), which is why the owner's
    # captured UI save named its mirror 'DomainCodee'. Each mirror therefore
    # records the PARENT field it maps to - the relation maps by that, never
    # by assuming child code == parent code.
    fields: List[Dict[str, Any]] = []
    for i, p in enumerate(pk_fields, start=1):
        fields.append({"code": naming.sql_safe(p["code"]), "label": p["code"],
                       "dataType": p.get("dataType", "character"),
                       "primaryKey": i, "isPrimary": True, "isRequired": True,
                       "mapsToParentField": p["code"]})

    mirror_codes = {f["code"] for f in fields}
    child_code = naming.sql_safe(
        str(child_pk.get("code") or f"{bc}Code").strip() or f"{bc}Code")
    if child_code in mirror_codes:
        child_code = f"{bc}Code"
    n = 2
    while child_code in mirror_codes:
        child_code = f"{bc}Code{n}"
        n += 1
    fields.append({"code": child_code, "label": child_code,
                   "dataType": child_pk.get("dataType", "character"),
                   "primaryKey": len(pk_fields) + 1, "isPrimary": True,
                   "isRequired": True})

    taken = {f["code"] for f in fields}
    for f in spec_fields:
        code = naming.sql_safe(str(f.get("code", "")).strip())
        if not code or code in taken:
            continue
        # A custom field the model wrongly marked primary is DEMOTED, not
        # dropped - silently losing a field the user asked for is worse than
        # carrying it as a plain column.
        if f.get("isPrimary") or f.get("primaryKey"):
            warns.append(
                f"The model marked '{code}' as a primary key; only the mirrored "
                f"parent keys and '{child_code}' may be primary, so it was kept "
                f"as a regular field.")
        taken.add(code)
        out = {"code": code, "label": f.get("label") or code,
               "dataType": f.get("dataType", "character"),
               "primaryKey": None, "isPrimary": False,
               "isRequired": bool(f.get("isRequired"))}
        if f.get("dropdownValues"):
            out["dropdownValues"] = f["dropdownValues"]
        if f.get("maxLength") is not None:
            out["maxLength"] = f["maxLength"]
        fields.append(out)
    return fields, warns


async def stage_e_fields(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    from agents import prompts
    from core import parent_registry as pr
    import json as _json

    req_art = ctx.get("requirements") or {}
    req = req_art.get("requirements")
    if not req:
        raise StageError("Run and approve the requirements stage first.")
    parent = pr.get(req_art["parent"]["key"])

    # Ask QAD for the parent's CURRENT keys; the file entry is only the menu.
    # Skipped on dry runs so a rehearsal stays fully offline, the same promise
    # every other stage keeps.
    warnings: List[str] = []
    pk_fields = parent.pk_fields
    if ctx["dry_run"]:
        live = {"live_ok": False}
        warnings.append(
            "Dry run: the parent was not re-verified against QAD; the registry "
            "entry is used as-is. A live run re-reads its keys before building.")
    else:
        live = await pr.verify_live(parent.key)
    if live.get("live_ok"):
        if live.get("do_not_extend"):
            raise StageError(
                f"QAD says '{parent.key}' is doNotExtend on this environment - it "
                f"cannot be a parent. Choose a different parent at the requirements "
                f"stage.")
        if live.get("live_pk_fields"):
            pk_fields = live["live_pk_fields"]
        warnings.extend(live.get("mismatches") or [])
    elif not ctx["dry_run"]:
        warnings.append(
            f"Could not verify '{parent.key}' live ({live.get('error', 'no detail')}); "
            f"building from the registry entry.")

    model_input = dict(req)
    model_input["parent_pk_fields"] = pk_fields
    user = _json.dumps(model_input)
    if instruction:
        user += f"\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    parsed = llm.parse_json(await llm.complete(
        prompts.render(prompts.EMBEDDED_FIELD_CREATOR,
                       docs_context=_docs_bundle("business_component")),
        user, role="generation", json_mode=True))
    spec_in = (parsed.get("spec") if isinstance(parsed, dict) else None) or {}
    bc = spec_in.get("bc_pascal") or req.get("bc_pascal")
    if not bc:
        raise StageError("The model did not return a BC name.")

    mirrored, mirror_warns = _mirror_parent_pks(spec_in.get("fields") or [], pk_fields,
                                                req.get("child_pk") or {}, bc)
    warnings.extend(mirror_warns)
    spec = {
        "bc_pascal": bc,
        "description": spec_in.get("description") or req.get("description", ""),
        "parent_key": parent.key,
        # The PK list the mirrors were actually built from - live when a live
        # read succeeded, registry otherwise. The relate stage maps THIS list,
        # never the file entry, so the relation can not disagree with the
        # entity that was really created.
        "parent_pk_fields": pk_fields,
        "fields": mirrored,
    }

    ident = AppIdentity.from_config()
    built = build_embedded_entity_payload(spec, ident)

    async def commit(dry_run: bool) -> List[Any]:
        results = []
        create = await qad_client.call("bc.create", payload=built["payload"],
                                       dry_run=dry_run)
        results.append(("bc.create", create))
        if not create.ok:
            return results
        # Dropdown wiring: identical second-save contract to Case 1.
        if built["field_list_map"]:
            params = {"entity_uri": built["entity_uri"]}
            got = await qad_client.call("bc.metadata.read", params=params, dry_run=dry_run)
            results.append(("bc.metadata.read", got))
            if got.ok and not dry_run:
                body = got.data.get("data") if isinstance(got.data.get("data"), dict) else got.data
                if not body.get("entityMetadatas"):
                    return results
                patch_dropdown_fields(body, built["field_list_map"])
                results.append(("bc.metadata.write",
                                await qad_client.call("bc.metadata.write", payload=body,
                                                      params=params, dry_run=dry_run)))
            elif dry_run:
                preview = {"entityMetadatas": [{"entityFields": [
                    {"entityFieldCode": code, **info}
                    for code, info in built["field_list_map"].items()
                ]}]}
                results.append(("bc.metadata.write",
                                await qad_client.call("bc.metadata.write", payload=preview,
                                                      params=params, dry_run=True)))
        return results

    n_pks = len(pk_fields)
    return StageResult(
        artifact={
            "spec": spec,
            "bc_pascal": bc,
            "field_count": len(spec["fields"]),
            "entity_uri": built["entity_uri"],
            "payload_preview": built["payload"],
            "summary": built["summary"],
            "pk_structure": {
                "mirrored_parent_pks": [f["code"] for f in spec["fields"][:n_pks]],
                "child_pk": spec["fields"][n_pks]["code"],
                "parent_key": parent.key,
            },
        },
        commit=commit,
        warnings=warnings,
    )


async def stage_e_relate(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    from core import parent_registry as pr
    from builders.embedded_builder import build_relation_payload

    spec = _need(ctx, "fields", "spec")
    parent = pr.get(spec["parent_key"])
    built = build_relation_payload(spec, parent, AppIdentity.from_config())

    async def commit(dry_run: bool) -> List[Any]:
        return [("relation.create",
                 await qad_client.call("relation.create", payload=built["payload"],
                                       dry_run=dry_run))]

    return StageResult(
        artifact={
            "summary": built["summary"],
            "relation_id": built["relation_id"],
            "payload_preview": built["payload"],
        },
        commit=commit,
    )


# stage_e_view is GONE, deliberately - not refactored, removed. Three live
# runs established that the platform forbids a separate menu view for an
# embedded child in either order (destroyed before deploy; duplicate-rejected
# after; locked in QAD's UI), which is what the class-3 guide meant by
# "embedded BCs are not menu-accessible". A stage that cannot succeed is not
# an experimental feature, it is a trap.


# ── Case 3: server-side Java extensions ──────────────────────────────────────
def _workspace():
    """The JEF workspace, or a StageError explaining how to set it."""
    from core import maven
    root = config.jef_workspace_dir()
    if not root:
        raise StageError(
            "JEF_WORKSPACE_DIR is not set. Point it at the Java extension project - "
            "the folder containing pom.xml, created by the VS Code plugin's "
            "'QAD Extension: Init app' and named urn_app_<fullAppName>.")
    ws = maven.Workspace(root)
    problems = ws.problems()
    if problems:
        raise StageError(" ".join(problems))
    return ws


async def _dependency_jar(ws) -> Any:
    """The dependency jar, fetched from QAD if the workspace lacks it.

    A GET whose only side effect is a local file, so it needs no gate - the
    same reasoning that lets the lookup stage read QAD's field picker while
    merely rendering.
    """
    from core import jef_deploy, maven
    jar = ws.lib / maven.DEPENDENCY_JAR_NAME
    if jar.is_file():
        return jar
    logger.info("[JEF] no dependency jar in %s; fetching from QAD", ws.lib)
    try:
        return await jef_deploy.fetch_dependency_jar(jar)
    except jef_deploy.JefDeployError as exc:
        raise StageError(
            f"{exc} The jar holds the generated Java for every business component, "
            f"so nothing can be generated without it.") from exc


async def stage_s_target(ctx: Dict[str, Any], instruction: str = "",
                         bc_name: str = "", target_class: str = "") -> StageResult:
    """Pick the component and state the rule. Reads the jar; writes nothing."""
    from agents import prompts
    from core import jar_inspector as ji, jef_deploy

    ws = _workspace()
    jar = await _dependency_jar(ws)
    db = (ctx.get("_db") or {}).get("db_path")

    # A choice made at the gate is a deterministic swap, not a reason to
    # re-roll the model and approve something the user never saw.
    prev = (ctx.get("target") or {}).get("decision")
    if prev and (bc_name or target_class or not instruction):
        decision = dict(prev)
        if bc_name:
            decision["bc_name"] = bc_name
        if target_class:
            decision["target_class"] = target_class
        return StageResult(artifact=await _s_target_artifact(decision, jar, ws, db))

    components = ji.list_components(jar)
    menu = "\n".join(
        f"{c.name} - {c.package} - {'app' if c.is_app_owned else 'QAD'}"
        for c in components)
    live = await jef_deploy.live_classes(db_path=db)
    deployed_menu = "\n".join(live) if live else "(none recorded)"

    user = ctx["user_input"]
    if instruction:
        user = f"{user}\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    raw = await llm.complete(
        prompts.render(prompts.SERVERSIDE_TARGET,
                       tokens={"COMPONENT_MENU": menu, "DEPLOYED_MENU": deployed_menu}),
        user, role="planning", json_mode=True)
    decision = llm.parse_json(raw)
    if not isinstance(decision, dict):
        raise StageError("The model did not return a usable target decision.")
    if bc_name:
        decision["bc_name"] = bc_name
    if target_class:
        decision["target_class"] = target_class
    return StageResult(artifact=await _s_target_artifact(decision, jar, ws, db))


async def _s_target_artifact(decision: Dict[str, Any], jar: Any, ws: Any,
                             db: Any = None) -> Dict[str, Any]:
    from core import jar_inspector as ji, jef_deploy

    intent = "delete" if str(decision.get("intent", "")).lower() == "delete" else "create"
    out: Dict[str, Any] = {
        "decision": decision,
        "intent": intent,
        "workspace": str(ws.root),
        "jar": str(jar),
    }

    if intent == "delete":
        live = await jef_deploy.live_classes(db_path=db)
        out["deployed"] = live or []
        out["deployed_known"] = live is not None
        out["target_class"] = decision.get("target_class") or ""
        return out

    # Create: resolve the component so the gate can show its REAL fields and
    # the save paths that will actually be guarded.
    bc = ji.inspect(jar, str(decision.get("bc_name", "")))
    out["bc"] = bc.summary()
    out["class_name"] = decision.get("class_name") or f"{bc.name}Validation"
    out["rule"] = decision.get("rule", "")
    out["message"] = decision.get("message", "")
    out["component_options"] = [
        {"name": c.name, "package": c.package, "app_owned": c.is_app_owned}
        for c in ji.list_components(jar)
    ]
    return out


async def stage_s_code(ctx: Dict[str, Any], instruction: str = "",
                       source: str = "") -> StageResult:
    """Write the class, or name the one to remove. Touches only local disk."""
    from agents import prompts
    from core import jar_inspector as ji
    from builders import extension_builder as xb

    target = ctx.get("target") or {}
    if not target:
        raise StageError("Run and approve the target stage first.")
    ws = _workspace()

    if target.get("intent") == "delete":
        wanted = target.get("target_class") or ""
        live = target.get("deployed") or []
        if wanted not in live:
            raise StageError(
                f"'{wanted or '(nothing chosen)'}' is not among the validations recorded "
                f"as deployed for this app: {', '.join(live) or '(none)'}. Choose one of "
                f"those at the target gate, or start a create instead.")
        rel = wanted.replace(".", "/") + ".java"
        present = (ws.source_root / rel).is_file()
        return StageResult(
            artifact={
                "intent": "delete",
                "class_name": wanted,
                "relative_path": rel,
                "source_present": present,
                "remaining_after": [c for c in live if c != wanted],
            },
            warnings=[] if present else [
                f"{rel} is not in the workspace, so there is no local source to remove. "
                f"The class still disappears from QAD on the next deploy, because the "
                f"jar is built from what IS in the workspace."],
        )

    bc = ji.inspect(Path(target["jar"]), target["bc"]["name"])
    class_name = target.get("class_name") or f"{bc.name}Validation"
    rel = f"{config.app_identity()['module'].replace('.', '/')}/{class_name}.java"

    if source.strip():
        # Edited by hand at the gate. Take it verbatim - editing is the point of
        # an editable gate - but it still has to compile at the next stage.
        return StageResult(
            artifact={"intent": "create", "class_name": class_name,
                      "relative_path": rel, "source": source,
                      "summary": {"bc": bc.name, "class_name": class_name,
                                  "edited_by_user": True},
                      "message": target.get("message", "")},
            warnings=["This source was edited by hand, so the generator's save-path "
                      "coverage checks no longer describe it."],
        )

    field_table = "\n".join(
        f"  {f.getter}() -> {f.simple_type}" for f in bc.fields) or "  (none)"
    user = f"Component: {bc.name}\nRule: {target.get('rule', '')}"
    if instruction:
        user += f"\n\nCORRECTION FROM THE USER, apply this:\n{instruction}"

    body = _strip_fences(await llm.complete(
        prompts.render(prompts.SERVERSIDE_VALIDATION_BODY,
                       tokens={"FIELD_TABLE": field_table,
                               "RULE": target.get("rule", ""),
                               "MESSAGE": target.get("message", "")}),
        user, role="generation"))

    built = xb.build_extension_source(bc, xb.ValidationSpec(
        class_name=class_name,
        description=target.get("rule", "") or f"Validation on {bc.name}.",
        body=body))
    return StageResult(
        artifact={
            "intent": "create",
            "class_name": class_name,
            "relative_path": built["relative_path"],
            "source": built["source"],
            "summary": built["summary"],
            "message": target.get("message", ""),
        },
        warnings=built["warnings"],
    )


def _strip_fences(text: str) -> str:
    """Models wrap code in fences however firmly they are told not to."""
    t = (text or "").strip()
    if t.startswith("```"):
        lines = t.splitlines()
        t = "\n".join(lines[1:])
        if t.rstrip().endswith("```"):
            t = t.rstrip()[: t.rstrip().rfind("```")]
    return t.strip()


async def stage_s_build(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    """Put the source in the workspace and compile it. No QAD contact at all.

    The highest-value rehearsal in the case: javac is a free and exact reviewer
    of the model's work, and it has already caught a real type error here.
    """
    from core import maven

    code = ctx.get("code") or {}
    if not code:
        raise StageError("Run and approve the code stage first.")
    ws = _workspace()

    if code.get("intent") == "delete":
        removed = maven.remove_source(ws, code["relative_path"])
    else:
        maven.write_source(ws, code["relative_path"], code["source"])
        removed = False

    result = maven.package(ws)
    if not result.ok:
        raise StageError(
            "The build failed, so there is nothing to deploy. "
            + ("; ".join(str(e) for e in result.compile_errors())
               or f"Maven exited {result.exit_code}."))

    return StageResult(artifact={
        "intent": code.get("intent"),
        "removed_source": removed,
        "sources": [str(p) for p in maven.list_sources(ws)],
        "build": result.summary(),
        "log_tail": result.log_tail[-2000:],
    })


async def stage_s_deploy(ctx: Dict[str, Any], instruction: str = "") -> StageResult:
    """Upload the jar. THE write: whole-jar replacement, no validated undo."""
    from core import jef_deploy

    build = ctx.get("build") or {}
    jar = (build.get("build") or {}).get("jar")
    if not jar:
        raise StageError("Run and approve the compile stage first - there is no jar yet.")
    db = (ctx.get("_db") or {}).get("db_path")
    plan = await jef_deploy.plan(Path(jar), db_path=db)

    async def commit(dry_run: bool) -> List[Any]:
        res = await jef_deploy.deploy(Path(jar), dry_run=dry_run,
                                      run_id=ctx["run_id"], db_path=db)
        return [("jef.deploy", _DeployResult(res))]

    return StageResult(
        artifact={
            "plan": plan.summary(),
            "erases": plan.erases,
            "intent": (ctx.get("code") or {}).get("intent"),
        },
        commit=commit,
        warnings=plan.warnings(),
    )


class _DeployResult:
    """Adapts a jef_deploy result to the shape the engine records for a write.

    jef_deploy already recorded the deploy in its own manifest; this only feeds
    the shared qad_writes audit trail and the regeneration lock.
    """

    def __init__(self, res: Dict[str, Any]):
        plan = res.get("plan") or {}
        self.ok = bool(res.get("ok"))
        self.dry_run = bool(res.get("dry_run"))
        self.data = res.get("response")
        self.error = res.get("error", "")
        self.request = {
            "method": "POST",
            "url": plan.get("url"),
            "multipart_field": plan.get("part_field_name"),
            "filename": plan.get("part_filename"),
            "classes_after_deploy": plan.get("classes_after_deploy"),
        }


RUNNERS = {
    "standard": {
        "requirements": stage_requirements,
        "fields": stage_fields,
        "form": stage_form,
        "handler": stage_handler,
        "view": stage_view,
        "lookups": stage_lookups,
        "deploy": stage_deploy,
    },
    "serverside": {
        "target": stage_s_target,
        "code": stage_s_code,
        "build": stage_s_build,
        "deploy": stage_s_deploy,
    },
    "embedded": {
        "requirements": stage_e_requirements,
        "fields": stage_e_fields,
        "relate": stage_e_relate,
        # Deploy is IDENTICAL to Case 1's: same endpoints, same payloads, same
        # warnings gate - the capture confirms the identity values.
        "deploy": stage_deploy,
    },
}


# ── Orchestration ────────────────────────────────────────────────────────────
async def run_stage(run_id: str, stage_id: str, instruction: str = "",
                    db_path=None, **kwargs) -> Dict[str, Any]:
    """Produce a stage's artifact. WRITES NOTHING - approving does that."""
    db = {"db_path": db_path} if db_path else {}
    ctx = await context(run_id, **db)
    mode = ctx["mode"]
    # A cross-mode id (form on an embedded run, relate on a standard one) is a
    # client mistake, not a server fault - surface it as a StageError so the
    # route answers 4xx instead of 500.
    try:
        stage = stages.get(stage_id, mode)
    except KeyError as exc:
        raise StageError(str(exc)) from exc
    runner = RUNNERS[mode].get(stage_id)
    if runner is None:
        raise StageError(f"Stage '{stage_id}' has no runner for mode '{mode}'.")

    # The same lock that guards /regenerate. Without it, re-running a stage
    # through the plain stage route (the parent picker, handler URIs, lookup
    # configs all use it) would silently step around the one rule that keeps
    # live writes single-shot.
    allowed, reason = await store.can_regenerate(run_id, stage_id, **db)
    if not allowed:
        raise StageError(reason)

    try:
        result = await runner(ctx, instruction=instruction, **kwargs)
    except (StageError, llm.LLMError, ValueError) as exc:
        await store.save_stage(run_id, stage_id, {"error": str(exc)},
                               status=store.STAGE_FAILED, instruction=instruction,
                               error=str(exc), **db)
        await store.update_run(run_id, status=store.RUN_FAILED, error=str(exc), **db)
        raise

    if result.skip:
        await store.save_stage(run_id, stage_id,
                               {**result.artifact, "skip_reason": result.skip_reason},
                               status=store.STAGE_SKIPPED, **db)
        await store.set_stage_status(run_id, stage_id, store.STAGE_SKIPPED, **db)
        # Advance past the skipped stage. Without this, a run whose LAST stage
        # skips itself (embedded: the conditional view) stays "running" forever.
        nxt = stages.next_after(stage_id, mode)
        await store.update_run(run_id,
                               current_stage=nxt.id if nxt else stage_id,
                               status=store.RUN_RUNNING if nxt else store.RUN_COMPLETE,
                               **db)
        logger.info("[RUN %s] stage '%s' skipped: %s", run_id, stage_id, result.skip_reason)
        return {"stage": stage_id, "skipped": True, "reason": result.skip_reason,
                "next": nxt.id if nxt else None, "complete": nxt is None}

    status = store.STAGE_AWAITING if stage.gated else store.STAGE_RUNNING
    await store.save_stage(run_id, stage_id, result.artifact, status=status,
                           instruction=instruction, **db)
    await store.update_run(run_id, current_stage=stage_id,
                           status=store.RUN_AWAITING if stage.gated else store.RUN_RUNNING,
                           **db)
    if stage_id == "fields":
        await store.update_run(run_id, bc_pascal=result.artifact.get("bc_pascal"), **db)

    _PENDING[(run_id, stage_id)] = result
    return {
        "stage": stage_id,
        "gated": stage.gated,
        "artifact": result.artifact,
        "warnings": result.warnings,
        "writes": stage.writes,
    }


# Commit callables cannot be serialised, so the most recent result per stage is
# held here. A process restart loses it, and approve() rebuilds by re-running
# the stage - which is safe precisely because running never writes.
_PENDING: Dict[Any, StageResult] = {}


async def _first_unresolved_stage(run_id: str, mode: str, **db) -> Optional[str]:
    """The first stage, in this mode's order, not yet approved or skipped.

    None means every stage is resolved. Exists to refuse an out-of-order
    approval: the stage rail lets a user OPEN any stage's gate freely (that is
    harmless, run_stage writes nothing), but firing ITS WRITE ahead of an
    earlier stage's write is a different matter. It is exactly how an embedded
    view lost its menu flag a second time - the deploy gate was left open
    un-approved while the view gate, reachable from the rail, was approved
    first. view.register hit the wire, then deploy.business_entity landed
    afterwards and replaced it, silently, same as before. Order is not merely
    cosmetic once a later stage's write can invalidate an earlier one's.
    """
    for stage in stages.stage_list(mode):
        row = await store.get_stage(run_id, stage.id, **db)
        status = row["status"] if row else None
        if status not in (store.STAGE_APPROVED, store.STAGE_SKIPPED):
            return stage.id
    return None


async def approve_stage(run_id: str, stage_id: str, db_path=None,
                        **kwargs) -> Dict[str, Any]:
    """Approve a stage: fire its writes, record them, and advance."""
    db = {"db_path": db_path} if db_path else {}
    run = await store.get_run(run_id, **db)
    if not run:
        raise StageError(f"No run '{run_id}'.")
    mode = run.get("mode") or "standard"
    try:
        stage = stages.get(stage_id, mode)  # unknown-for-this-mode raises before anything fires
    except KeyError as exc:
        raise StageError(str(exc)) from exc

    # The recovery stage is exempt: it stands in for its host ("fields") while
    # that host shows as FAILED, which is itself "unresolved" - checking would
    # permanently lock out the one path that recovers from a rejected create.
    if stage_id != stages.RECOVERY_STAGE.id:
        blocker = await _first_unresolved_stage(run_id, mode, **db)
        if blocker is not None and blocker != stage_id:
            blocker_stage = stages.get(blocker, mode)
            raise StageError(
                f"'{blocker_stage.label}' has not been approved yet. Approve stages "
                f"in order - opening a later gate from the rail does not let its "
                f"write jump ahead of an earlier one still waiting."
            )

    result = _PENDING.get((run_id, stage_id))
    if result is None:
        # Rebuilt rather than failed: running a stage has no side effects.
        await run_stage(run_id, stage_id, db_path=db_path, **kwargs)
        result = _PENDING.get((run_id, stage_id))
    if result is None:
        raise StageError(f"Stage '{stage_id}' has produced nothing to approve.")

    written = []
    if result.commit is not None:
        for endpoint_id, res in await result.commit(run["dry_run"]):
            await store.record_write(run_id, stage_id, endpoint_id, ok=res.ok,
                                     dry_run=res.dry_run, request=res.request,
                                     response=res.data if not res.dry_run else None, **db)
            written.append({"endpoint": endpoint_id, "ok": res.ok,
                            "dry_run": res.dry_run, "error": res.error})
            if not res.ok:
                await store.set_stage_status(run_id, stage_id, store.STAGE_FAILED, **db)
                await store.update_run(run_id, status=store.RUN_FAILED,
                                       error=res.error, **db)
                return {"stage": stage_id, "approved": False, "writes": written,
                        "error": res.error}

    await store.set_stage_status(run_id, stage_id, store.STAGE_APPROVED, **db)
    nxt = stages.next_after(stage_id, mode)
    await store.update_run(
        run_id,
        current_stage=nxt.id if nxt else stage_id,
        status=store.RUN_RUNNING if nxt else store.RUN_COMPLETE,
        **db)
    logger.info("[RUN %s] stage '%s' approved, %d write(s)", run_id, stage_id, len(written))
    return {"stage": stage_id, "approved": True, "writes": written,
            "next": nxt.id if nxt else None, "complete": nxt is None}


async def regenerate_stage(run_id: str, stage_id: str, instruction: str = "",
                           db_path=None, **kwargs) -> Dict[str, Any]:
    """Re-run a stage with a free-text steer, if the lock permits it."""
    db = {"db_path": db_path} if db_path else {}
    allowed, reason = await store.can_regenerate(run_id, stage_id, **db)
    if not allowed:
        raise StageError(reason)
    return await run_stage(run_id, stage_id, instruction=instruction,
                           db_path=db_path, **kwargs)


async def skip_stage(run_id: str, stage_id: str, reason: str = "",
                     db_path=None) -> Dict[str, Any]:
    """Skip a conditional stage without writing anything."""
    db = {"db_path": db_path} if db_path else {}
    run = await store.get_run(run_id, **db)
    if not run:
        raise StageError(f"No run '{run_id}'.")
    mode = run.get("mode") or "standard"
    try:
        stage = stages.get(stage_id, mode)
    except KeyError as exc:
        raise StageError(str(exc)) from exc
    if not stage.conditional_on:
        raise StageError(
            f"'{stage.label}' is not a conditional stage and cannot be skipped."
        )
    await store.save_stage(run_id, stage_id,
                           {"skipped_by_user": True, "reason": reason},
                           status=store.STAGE_SKIPPED, **db)
    await store.set_stage_status(run_id, stage_id, store.STAGE_SKIPPED, **db)
    nxt = stages.next_after(stage_id, mode)
    await store.update_run(run_id, current_stage=nxt.id if nxt else stage_id,
                           status=store.RUN_RUNNING if nxt else store.RUN_COMPLETE, **db)
    return {"stage": stage_id, "skipped": True, "next": nxt.id if nxt else None}
