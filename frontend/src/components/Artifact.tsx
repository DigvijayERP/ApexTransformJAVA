// Renders what a stage produced — the real content, not a status line.
//
// Dispatches on `artifact_kind`. An UNKNOWN kind falls through to raw JSON
// rather than rendering nothing: AUX silently drops four SSE frame types its
// frontend does not declare, and in a gated UI a frame you cannot render is a
// decision made blind.

import { useState, type ReactNode } from "react";
import type { ArtifactKind } from "../api";

type Bag = Record<string, any>;

export function Payload({ value, label = "Exact payload" }: { value: unknown; label?: string }) {
  const [open, setOpen] = useState(false);
  if (value === undefined || value === null) return null;
  return (
    <details className="payload" open={open} onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>{label}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return <section className="sect"><h4>{title}</h4>{children}</section>;
}

function Empty({ children }: { children: ReactNode }) {
  return <p className="muted">{children}</p>;
}

// Ranked guesses from QAD's own browse list, sent by the backend for one field.
// Clicking one fills the Browse URI input. They are only guesses ranked by
// name, so the copy says to check one before using it.
function BrowsePicks({ list, onPick }: { list: Bag[]; onPick: (uri: string) => void }) {
  if (!list || list.length === 0) return null;
  return (
    <div className="browse-picks">
      <span className="picks-label">Browses that may fit (click one to use it)</span>
      <ul className="plain">
        {list.map((b) => (
          <li key={b.code}>
            <button type="button" className="browse-pick" onClick={() => onPick(b.uri)}>
              <code>{b.code}</code>
              <span>{b.description}</span>
              <code className="browse-pick-uri">{b.uri}</code>
            </button>
          </li>
        ))}
      </ul>
      <p className="muted">
        Ranked by name from QAD's browse list, so check one against QAD before you use it.
      </p>
    </div>
  );
}

// ── Per-kind renderers ───────────────────────────────────────────────────────
function Text({ a }: { a: Bag }) {
  return <pre className="prose">{a.text ?? a.plan ?? JSON.stringify(a, null, 2)}</pre>;
}

function FieldSpec({ a }: { a: Bag }) {
  const fields: Bag[] = a.spec?.fields ?? [];
  const renamed: Bag[] = a.renamed_fields ?? [];
  const renamedOf = (code: string) =>
    renamed.find((r) => r.asked_for === code)?.actual_column;

  return (
    <>
      <Section title={`${a.bc_pascal}: ${fields.length} field${fields.length === 1 ? "" : "s"}`}>
        <table className="grid">
          <thead>
            <tr><th>Field</th><th>Type</th><th>Key</th><th>Required</th><th>Lookup</th><th>Values</th></tr>
          </thead>
          <tbody>
            {fields.map((f) => {
              const safe = renamedOf(f.code);
              return (
                <tr key={f.code}>
                  <td>
                    <code>{f.code}</code>
                    {/* A SQL reserved word becomes a differently-named QAD
                        column. Silent renaming is what a gate exists to catch. */}
                    {safe && <span className="rename" title="renamed, SQL reserved word">→ {safe}</span>}
                  </td>
                  <td>{f.dataType}{f.maxLength ? ` (${f.maxLength})` : ""}</td>
                  {/* Standard specs carry isPrimary booleans; embedded specs
                      carry 1-based primaryKey ordinals. Render either. */}
                  <td>{f.primaryKey ? `PK ${f.primaryKey}` : f.isPrimary ? "PK" : ""}</td>
                  <td>{f.isRequired ? "yes" : ""}</td>
                  <td>{f.needsLookup ? "yes" : ""}</td>
                  <td className="vals">
                    {(f.dropdownValues ?? []).map((v: Bag) => v.code).join(", ")}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Section>
      <p className="muted">Entity URI <code>{a.entity_uri}</code></p>
      <Payload value={a.payload_preview} label="Exact payload QAD will receive" />
    </>
  );
}

function FormLayout({ a }: { a: Bag }) {
  const placements: Bag[] = a.placements ?? [];
  const panels: Bag[] = a.panels ?? [];
  return (
    <>
      {a.plan && <Section title="Panel plan"><pre className="prose">{a.plan}</pre></Section>}
      {panels.map((p) => (
        <Section key={p.panel} title={`Panel ${p.panel}: ${p.panelName}`}>
          <table className="grid">
            <thead><tr><th>Field</th><th>Column</th><th>Row</th></tr></thead>
            <tbody>
              {placements.filter((x) => x.panel === p.panel).map((x) => (
                <tr key={x.fieldName}>
                  <td><code>{x.fieldName}</code></td>
                  <td>{x.gridColumn === 0 ? "left" : "right"}</td>
                  <td>{x.gridRow}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      ))}
      <Payload value={a.payload_preview} label="Exact payload QAD will receive" />
    </>
  );
}

function HandlerCode({ a, onBrowseUris }: { a: Bag; onBrowseUris?: (v: Record<string, string>) => void }) {
  const placeholders: Bag[] = a.browse_placeholders ?? [];
  const [uris, setUris] = useState<Record<string, string>>(a.browse_uris_supplied ?? {});

  return (
    <>
      {a.plan && <Section title="Plan"><pre className="prose">{a.plan}</pre></Section>}

      {placeholders.length > 0 && (
        <Section title="Browse URIs this handler needs">
          <p className="muted">
            Leave one blank and that line is commented out with a TODO, the same
            fallback AUX always takes. Fill it in and the call works.
          </p>
          {placeholders.map((p) => (
            <div key={p.field}>
              <label className="field">
                <span><code>{p.field}</code> <small>{p.context}</small></span>
                <input
                  value={uris[p.field] ?? ""}
                  placeholder="urn:browse:bebrowse:com.qad.erp.base.customers"
                  onChange={(e) => setUris({ ...uris, [p.field]: e.target.value })}
                />
              </label>
              <BrowsePicks
                list={p.browse_candidates ?? []}
                onPick={(uri) => setUris({ ...uris, [p.field]: uri })}
              />
            </div>
          ))}
          {onBrowseUris && (
            <button className="ghost" onClick={() => onBrowseUris(uris)}>
              Apply URIs and regenerate
            </button>
          )}
        </Section>
      )}

      <Section title="TypeScript">
        <pre className="code">{a.typescript}</pre>
      </Section>
    </>
  );
}

function ViewConfig({ a }: { a: Bag }) {
  const s: Bag = a.summary ?? {};
  return (
    <>
      <Section title="View">
        <dl className="pairs">
          <dt>Label</dt><dd>{s.view_label}</dd>
          <dt>Browse</dt><dd><code>{s.browse_uri}</code></dd>
          <dt>Hybrid browse</dt><dd><code>{s.hybrid_browse_uri}</code></dd>
          <dt>Key fields</dt><dd>{(s.pk_codes ?? []).join(", ")}</dd>
        </dl>
      </Section>
      <Payload value={a.payload_preview} label="Exact payload QAD will receive" />
    </>
  );
}

/** Browse entity = the last dotted segment of the browse URI.
 *  urn:browse:bebrowse:com.extensions.training.training -> "training", which is
 *  exactly the prefix the confirmed record's result field uses
 *  ("training.className", class 4 p.13). Falls back to the post-colon segment
 *  for mfg-style browses like urn:browse:mfg:ad057. */
function entityOf(uri: string): string {
  const s = uri.trim();
  if (!s) return "";
  const tail = s.includes(".") ? s.split(".").pop()! : s.split(":").pop()!;
  return tail.trim();
}

// One entry per field: the browse it points at, the column it returns, and
// which other form fields it should fill in. `fills` maps a form-field target
// to the browse column that supplies it; a fill without its own column would
// otherwise repeat the main result field, which is never what a fill means.
type LookupCfg = { uri: string; field: string; fills: Record<string, string> };

function LookupForm({ a, onConfigure }: { a: Bag; onConfigure?: (c: Bag[]) => void }) {
  const fields: Bag[] = a.fields ?? [];
  const [cfg, setCfg] = useState<Record<string, LookupCfg>>(
    () => Object.fromEntries(fields.map((f) => [f.code, { uri: "", field: "", fills: {} }])),
  );

  const set = (code: string, patch: Partial<LookupCfg>) =>
    setCfg((c) => ({ ...c, [code]: { ...c[code], ...patch } }));

  const ready = fields.every((f) => {
    const c = cfg[f.code];
    return c?.uri.trim() && c?.field.trim()
      && Object.values(c.fills).every((src) => src.trim());
  });

  const build = () => onConfigure?.(fields.map((f) => {
    const c = cfg[f.code];
    const entity = entityOf(c.uri);
    const dotted = `${entity}.${c.field.trim()}`;
    return {
      field_code: f.code,
      browse_uri: c.uri.trim(),
      browse_label: entity.charAt(0).toUpperCase() + entity.slice(1),
      browse_entity: entity,
      result_field: dotted,
      search_field: dotted,
      additional_results: Object.entries(c.fills).map(([target, source]) => ({
        field: `${entity}.${source.trim()}`,
        target,
      })),
    };
  }));

  return (
    <>
      <Section title="Configure each lookup">
        <p className="muted">{a.hint}</p>
      </Section>

      {fields.map((f) => {
        const c = cfg[f.code];
        const entity = entityOf(c.uri);
        const opts: Bag[] = f.auto_populate_options ?? [];
        return (
          <Section key={f.code} title={f.label ?? f.code}>
            <label className="field">
              <span>Browse URI (which records to choose from)</span>
              <input
                value={c.uri}
                placeholder="urn:browse:bebrowse:com.yash.digwish.digsmoketest"
                onChange={(e) => set(f.code, { uri: e.target.value })}
              />
            </label>

            <BrowsePicks
              list={f.browse_candidates ?? []}
              onPick={(uri) => set(f.code, { uri })}
            />

            <label className="field">
              <span>Field on that browse (the value returned)</span>
              <input
                value={c.field}
                placeholder="testCode"
                onChange={(e) => set(f.code, { field: e.target.value })}
              />
            </label>

            {entity && c.field.trim() && (
              <p className="muted">
                Result and search field → <code>{entity}.{c.field.trim()}</code>
              </p>
            )}

            {opts.length > 0 && (
              <>
                <span className="fills-label">Also fill in when a value is picked</span>
                <div className="fills">
                  {opts.map((o) => {
                    const checked = o.target in c.fills;
                    return (
                      <label key={o.target} className="dry-pill">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={(e) => {
                            const fills = { ...c.fills };
                            if (e.target.checked) fills[o.target] = "";
                            else delete fills[o.target];
                            set(f.code, { fills });
                          }}
                        />
                        {o.label}
                        {checked && (
                          <input
                            className="fill-source"
                            value={c.fills[o.target]}
                            placeholder="from which browse column?"
                            onClick={(e) => e.preventDefault()}
                            onChange={(e) => set(f.code, {
                              fills: { ...c.fills, [o.target]: e.target.value },
                            })}
                          />
                        )}
                      </label>
                    );
                  })}
                </div>
                {Object.keys(c.fills).length > 0 && (
                  <p className="muted">
                    Each ticked field needs the browse column that supplies it,
                    for example testDate. It is matched against the columns QAD
                    lists for that browse when you build.
                  </p>
                )}
              </>
            )}
          </Section>
        );
      })}

      {onConfigure && (
        <button className="primary" disabled={!ready} onClick={build}>
          Build lookup definition{fields.length === 1 ? "" : "s"}
        </button>
      )}
    </>
  );
}

function LookupConfig({ a, onConfigure }: { a: Bag; onConfigure?: (c: Bag[]) => void }) {
  if (a.awaiting_configuration) return <LookupForm a={a} onConfigure={onConfigure} />;
  const lookups: Bag[] = a.lookups ?? [];
  return (
    <>
      <Section title={`${lookups.length} lookup definition${lookups.length === 1 ? "" : "s"}`}>
        <ul className="plain">
          {lookups.map((l) => (
            <li key={l.field_code}>
              <code>{l.field_code}</code> → <code>{l.browse_uri}</code>
              {l.auto_populates?.length ? ` (fills ${l.auto_populates.join(", ")})` : ""}
            </li>
          ))}
        </ul>
      </Section>
      <Payload value={a.payload_preview} label="Exact payload QAD will receive" />
    </>
  );
}

function DeployPreview({ a }: { a: Bag }) {
  const warn = a.warnings_response ?? {};
  return (
    <>
      <Section title={`Deploy ${a.bc_pascal}`}>
        <p className="muted">
          Terminal. Nothing can be regenerated after this.<br />
          Entity <code>{a.entity_uri}</code>
        </p>
      </Section>
      <Section title="QAD's deployment warnings">
        {warn.dry_run
          ? <Empty>Dry run. The warnings check was rehearsed, not sent.</Empty>
          : <Payload value={warn.data ?? warn} label="Warnings response" />}
      </Section>
      <Payload value={a.payload_preview} label="Exact deploy payload" />
    </>
  );
}

function EmbeddedRequirements({ a, onParentKey }: {
  a: Bag; onParentKey?: (key: string) => void;
}) {
  const req: Bag = a.requirements ?? {};
  const parent: Bag = a.parent ?? {};
  const options: Bag[] = a.parent_options ?? [];
  const [choice, setChoice] = useState<string>(parent.key ?? "");
  const customs: Bag[] = req.custom_fields ?? [];

  return (
    <>
      <Section title={`${req.bc_pascal ?? "Embedded BC"}: what will be built`}>
        <p className="muted">{req.description}</p>
        <ul className="plain">
          <li>Child key: <code>{req.child_pk?.code}</code> ({req.child_pk?.dataType})</li>
          <li>
            Custom fields:{" "}
            {customs.length
              ? customs.map((f) => f.code).join(", ")
              : "none"}
          </li>
          <li>
            Where it appears: as an embedded grid and tab on the parent's own
            screen. The platform does not allow a separate menu view for an
            embedded component.
          </li>
        </ul>
      </Section>

      {(req.screen_rules ?? []).length > 0 && (
        <Section title="Validations found">
          <ul className="plain">
            {(req.screen_rules ?? []).map((r: Bag, i: number) => (
              <li key={r?.slug ?? i}>
                <code>{r?.field}</code>: {r?.message}
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Parent component it extends">
        <p className="muted">
          The model proposed <strong>{parent.label ?? parent.key}</strong>. You
          decide. Every primary key of the chosen parent is mirrored into the
          child and mapped in the relation.
        </p>
        <label className="field">
          <span>Parent</span>
          <select value={choice} onChange={(e) => setChoice(e.target.value)}>
            {options.map((o) => (
              <option key={o.key} value={o.key}>{o.label}</option>
            ))}
          </select>
        </label>
        {(() => {
          const chosen = options.find((o) => o.key === choice) ?? parent;
          return (
            <p className="muted">
              Keys to mirror:{" "}
              {(chosen.pk_fields ?? []).map((f: Bag) => f.code).join(", ")}
              {"  "}<code>{chosen.uri}</code>
            </p>
          );
        })()}
        {onParentKey && choice && choice !== parent.key && (
          <button className="ghost" onClick={() => onParentKey(choice)}>
            Use {choice} instead
          </button>
        )}
      </Section>

      {(a.abl_tables ?? []).length > 0 && (
        <Section title="Parsed from your ABL source">
          <ul className="plain">
            {a.abl_tables.map((t: Bag) => (
              <li key={t.name}>
                <code>{t.name}</code>: {(t.fields ?? []).length} field{(t.fields ?? []).length === 1 ? "" : "s"}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}

function RelationConfig({ a }: { a: Bag }) {
  const s: Bag = a.summary ?? {};
  const maps: Bag[] = s.mappings ?? [];
  return (
    <>
      <Section title={`Relate ${s.bc_pascal} to ${s.parent_key}`}>
        <p className="muted">
          Cardinality {s.cardinality}: many child rows per parent record, shown
          as an embedded grid on the parent's form after deploy.<br />
          Parent <code>{s.parent_uri}</code>
        </p>
        <table className="grid">
          <thead><tr><th>Child field</th><th>Maps to parent field</th></tr></thead>
          <tbody>
            {maps.map((m) => (
              <tr key={m.child}>
                <td><code>{m.child}</code></td>
                <td><code>{m.parent}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      <Payload value={a.payload_preview} label="Exact payload QAD will receive" />
    </>
  );
}

/** Case 4 — validation rules merged into the parent screen's event handler.
 *
 * The gate shows three things apart: the code that was already there (kept
 * exactly as it is), the marked blocks being added, and the compile verdict.
 * Everything is optional-chained: an older backend, or a field the model
 * missed, must degrade to a blank cell rather than a crash. */
function ScreenRuleGate({ a }: { a: Bag }) {
  const rules: Bag[] = a?.rules ?? [];
  const kept: string[] = a?.kept_rules ?? [];
  const compile: Bag = a?.compile ?? {};
  const errors: string[] = compile?.errors ?? [];
  const create = a?.action === "create";
  const switchesOn = create || a?.was_active === false;

  return (
    <>
      <Section title="Handler">
        <dl className="pairs">
          <dt>Screen</dt><dd>{a?.view_label} <code>{a?.view_uri}</code></dd>
          <dt>Action</dt>
          <dd>{create ? "Create a new handler" : "Update the existing handler"}</dd>
        </dl>
        {switchesOn && <p className="muted">The handler will be switched on.</p>}
      </Section>

      <Section title={`${rules.length} rule${rules.length === 1 ? "" : "s"}`}>
        <table className="grid">
          <thead><tr><th>Field</th><th>Check</th><th>Message</th></tr></thead>
          <tbody>
            {rules.map((r, i) => (
              <tr key={r?.slug ?? i}>
                <td><code>{r?.resolved_field ?? r?.field}</code></td>
                <td>{r?.check}</td>
                <td>{r?.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {kept.length > 0 && (
          <p className="muted">Rules kept from before: {kept.join(", ")}</p>
        )}
      </Section>

      <Section title="What gets added">
        <pre className="code">{a?.added_ts_blocks}</pre>
      </Section>

      <details className="payload">
        <summary>Your existing code (unchanged)</summary>
        <pre>{a?.existing_ts}</pre>
      </details>

      <Section title="Compile check">
        {compile?.ok
          ? <p className="ok">The merged handler compiles.</p>
          : (
            <ul className="plain">
              {errors.map((e, i) => <li key={i} className="warn">{e}</li>)}
            </ul>
          )}
        {compile?.checker === "stub-fallback" && (
          <p className="muted">
            Checked with simplified types only. Install the QAD compile kit
            for the full check.
          </p>
        )}
      </Section>
    </>
  );
}

// ── Dispatch ─────────────────────────────────────────────────────────────────
export function Artifact({ kind, artifact, onBrowseUris, onConfigure, onParentKey,
                          onServersidePick }: {
  kind: ArtifactKind | undefined;
  artifact: Bag;
  onBrowseUris?: (v: Record<string, string>) => void;
  onConfigure?: (c: Bag[]) => void;
  onParentKey?: (key: string) => void;
  onServersidePick?: (v: { bc_name?: string; target_class?: string; instruction?: string }) => void;
}) {
  switch (kind) {
    case "text":            return <Text a={artifact} />;
    case "field_spec":
    case "field_spec_diff": return <FieldSpec a={artifact} />;
    case "form_layout":     return <FormLayout a={artifact} />;
    case "handler_code":    return <HandlerCode a={artifact} onBrowseUris={onBrowseUris} />;
    case "view_config":     return <ViewConfig a={artifact} />;
    case "lookup_config":   return <LookupConfig a={artifact} onConfigure={onConfigure} />;
    case "deploy_preview":  return <DeployPreview a={artifact} />;
    case "embedded_requirements":
      {/* Keyed by the proposed parent so a regeneration that changes it
          remounts the picker - otherwise the stale `choice` state shows one
          parent while Approve approves another. */}
      return <EmbeddedRequirements key={artifact?.parent?.key ?? ""} a={artifact} onParentKey={onParentKey} />;
    case "relation_config": return <RelationConfig a={artifact} />;
    case "screen_rule":     return <ScreenRuleGate a={artifact} />;
    case "serverside_target":
      // Keyed by the chosen component so regenerating to a different one
      // remounts the picker instead of showing stale selection state.
      return <ServersideTarget key={artifact?.bc?.name ?? artifact?.intent ?? ""}
                               a={artifact} onPick={onServersidePick} />;
    case "serverside_code":   return <ServersideCode a={artifact} />;
    case "serverside_build":  return <ServersideBuild a={artifact} />;
    case "serverside_deploy": return <ServersideDeploy a={artifact} />;
    default:
      // Never drop it. An unrenderable artifact is still a decision the user
      // is being asked to make.
      return (
        <>
          <Empty>No renderer for “{kind ?? "unknown"}”. Showing it raw.</Empty>
          <pre className="code">{JSON.stringify(artifact, null, 2)}</pre>
        </>
      );
  }
}

/* ── Case 3: server-side Java extensions ─────────────────────────────────────
 *
 * The three-step shape AUX used for its server-side rules (pick a component,
 * see its fields, describe the rule) with one thing it never had: the
 * component list, the field names AND their real Java types all come from
 * QAD's compiled dependency jar, so nothing shown here is inferred.
 */

/** Step 1 — which component, and what rule.
 *
 * Rewritten 2026-08-14 after the owner could not tell what was selected. Three
 * problems, all of them correctness rather than polish:
 *
 *   1. Field chips LOOKED interactive and were not. The whole point of this
 *      step, ported from AUX, is choosing fields; they are now real toggles
 *      with an unmistakable selected state.
 *   2. The component choice is consequential and was easy to miss.
 *      `PurchaseOrder` and `PurchaseOrderHeader` BOTH have a `remarks` field,
 *      but only the latter exposes the *WithConfirmation save paths the QAD UI
 *      actually uses. Picking the wrong one deploys cleanly and never fires,
 *      so near-identical siblings are now surfaced explicitly.
 *   3. Rendering ~290 components and ~200 chips at once was slow. Lists are
 *      capped and report what they are hiding rather than silently truncating.
 */
function ServersideTarget({ a, onPick }: {
  a: Bag;
  onPick?: (v: { bc_name?: string; target_class?: string; instruction?: string }) => void;
}) {
  const [query, setQuery] = useState("");
  const [fieldQuery, setFieldQuery] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const [changing, setChanging] = useState(false);

  if (a.intent === "delete") {
    const deployed: string[] = a.deployed ?? [];
    return (
      <>
        <Section title="Remove a validation">
          <p className="muted">
            Removing rebuilds the jar without that class. Because a deploy replaces
            the whole jar, it then disappears from QAD entirely.
          </p>
        </Section>
        <Section title={`${deployed.length} recorded as deployed`}>
          {deployed.length === 0 ? (
            <p className="warn">
              Nothing is recorded as deployed for this app, so there is nothing to
              remove here. If a validation was deployed by other means this app has
              no record of it: QAD cannot be asked what is currently live.
            </p>
          ) : (
            <div className="pick-list" role="listbox">
              {deployed.map((c) => {
                const on = c === a.target_class;
                return (
                  <div key={c} role="option" aria-selected={on}
                       className={"pick-item" + (on ? " active" : "")}
                       onClick={() => onPick?.({ target_class: c })}>
                    <span className="pick-mark">{on ? "✓" : ""}</span>
                    <span className="pick-body">
                      <span className="pick-name">{c.split(".").pop()}</span>
                      <span className="pick-meta">{c}</span>
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </Section>
      </>
    );
  }

  const bc: Bag = a.bc ?? {};
  const fields: Bag[] = bc.fields ?? [];
  const savePaths: Bag[] = (bc.save_paths ?? []).filter((p: Bag) => p.mutating);
  const options: Bag[] = a.component_options ?? [];

  // Near-identical siblings are the trap: PurchaseOrder vs PurchaseOrderHeader.
  // Surfaced up front rather than left to be discovered after a silent no-op.
  const siblings = options.filter(
    (o) => o.name !== bc.name &&
      (o.name.startsWith(bc.name) || bc.name.startsWith(o.name)));

  const matches = query.trim()
    ? options.filter((o) => o.name.toLowerCase().includes(query.trim().toLowerCase()))
    : options;
  const shownOptions = matches.slice(0, 25);

  const fieldMatches = fieldQuery.trim()
    ? fields.filter((f) => f.name.toLowerCase().includes(fieldQuery.trim().toLowerCase()))
    : fields;
  const shownFields = fieldMatches.slice(0, 30);

  const toggle = (name: string) =>
    setPicked((p) => p.includes(name) ? p.filter((x) => x !== name) : [...p, name]);

  return (
    <>
      {/* What is actually selected, stated plainly, before anything else. */}
      <Section title="Selected">
        <dl className="pairs">
          <dt>Component</dt>
          <dd>
            <strong>{bc.name}</strong>{" "}
            <span className="muted">
              {bc.app_owned ? "created by this app" : "standard QAD"} · <code>{bc.package}</code>
            </span>
          </dd>
          <dt>Rule</dt><dd>{a.rule}</dd>
          <dt>Blocked save shows</dt><dd><strong>{a.message}</strong></dd>
          <dt>Java class</dt><dd><code>{a.class_name}</code></dd>
        </dl>
      </Section>

      <Section title={`Save paths guarded (${savePaths.length})`}>
        <div className="fills">
          {savePaths.map((p: Bag) => (
            <span key={p.name} className="dry-pill on">✓ {p.name}</span>
          ))}
        </div>
        <p className={bc.has_confirmation_variants ? "muted" : "warn"}>
          {bc.has_confirmation_variants
            ? "This component also saves through confirmation methods, and all of them are covered."
            : "This component exposes no confirmation variants. If the QAD screen for it saves through one, the rule would never fire — check the sibling components below."}
        </p>
      </Section>

      {siblings.length > 0 && (
        <Section title="Similarly named components">
          <p className="warn">
            {siblings.length === 1 ? "There is another component" : "There are other components"}{" "}
            with a near-identical name. They are different business components with
            different save paths, and only one drives the screen you mean.
          </p>
          <div className="pick-list" role="listbox">
            {siblings.map((o) => (
              <div key={`${o.package}.${o.name}`} role="option" aria-selected={false}
                   className="pick-item"
                   onClick={() => onPick?.({ bc_name: o.name })}>
                <span className="pick-mark" />
                <span className="pick-body">
                  <span className="pick-name">{o.name}</span>
                  <span className="pick-meta">use this instead · {o.package}</span>
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      <Section title="Fields">
        <p className="muted">
          Read from the compiled component with their real Java types. Select the
          ones the rule is about, or just leave it: the rule above already names them.
        </p>
        <label className="field">
          <span>Filter {fields.length} fields</span>
          <input value={fieldQuery} placeholder="remarks, date, status…"
                 onChange={(e) => setFieldQuery(e.target.value)} />
        </label>
        <div className="fills">
          {shownFields.map((f: Bag) => {
            const on = picked.includes(f.name);
            return (
              <button type="button" key={f.name}
                      className={"dry-pill selectable" + (on ? " on" : "")}
                      aria-pressed={on}
                      title={`${f.getter}() returns ${f.type}`}
                      onClick={() => toggle(f.name)}>
                <span className="pill-mark">{on ? "✓" : "+"}</span>
                {f.name}<em className="chip-type">{f.type}</em>
              </button>
            );
          })}
        </div>
        {fieldMatches.length > shownFields.length && (
          <p className="muted">
            Showing {shownFields.length} of {fieldMatches.length}. Filter to narrow.
          </p>
        )}
        {fieldMatches.length === 0 && <p className="muted">No field matches.</p>}

        {picked.length > 0 && (
          <div className="picked-bar">
            <span>
              <strong>{picked.length} selected:</strong> {picked.join(", ")}
            </span>
            <span className="picked-actions">
              <button className="ghost" onClick={() => setPicked([])}>Clear</button>
              {onPick && (
                <button className="primary" onClick={() => onPick({
                  instruction: `The rule concerns these fields specifically: ${picked.join(", ")}.`,
                })}>
                  Rewrite the rule around these
                </button>
              )}
            </span>
          </div>
        )}
      </Section>

      <Section title="Target a different component">
        {!changing ? (
          <button className="ghost" onClick={() => setChanging(true)}>
            Change component ({options.length} available)
          </button>
        ) : (
          <>
            <label className="field">
              <span>Search {options.length} components</span>
              <input autoFocus value={query} placeholder="purchase, sales, item…"
                     onChange={(e) => setQuery(e.target.value)} />
            </label>
            <div className="pick-list" role="listbox">
              {shownOptions.map((o) => {
                const on = o.name === bc.name;
                return (
                  <div key={`${o.package}.${o.name}`} role="option" aria-selected={on}
                       className={"pick-item" + (on ? " active" : "")}
                       onClick={() => { setChanging(false); onPick?.({ bc_name: o.name }); }}>
                    <span className="pick-mark">{on ? "✓" : ""}</span>
                    <span className="pick-body">
                      <span className="pick-name">{o.name}</span>
                      <span className="pick-meta">{o.app_owned ? "app" : "QAD"} · {o.package}</span>
                    </span>
                  </div>
                );
              })}
            </div>
            {matches.length > shownOptions.length && (
              <p className="muted">
                Showing {shownOptions.length} of {matches.length}. Type to narrow.
              </p>
            )}
            {matches.length === 0 && <p className="muted">Nothing matches “{query}”.</p>}
          </>
        )}
      </Section>
    </>
  );
}

/** Step 2 — the Java itself. */
function ServersideCode({ a }: { a: Bag }) {
  if (a.intent === "delete") {
    const remaining: string[] = a.remaining_after ?? [];
    return (
      <>
        <Section title="Will be removed">
          <p><code>{a.class_name}</code></p>
          <p className="muted">Source file: <code>{a.relative_path}</code></p>
        </Section>
        <Section title={`${remaining.length} will remain`}>
          {remaining.length
            ? <ul className="plain">{remaining.map((c) => <li key={c}><code>{c}</code></li>)}</ul>
            : <p className="muted">None. The app will have no server-side validations.</p>}
        </Section>
      </>
    );
  }
  const s: Bag = a.summary ?? {};
  return (
    <>
      <Section title={a.class_name}>
        <ul className="plain">
          <li>Guards: {(s.guarded_paths ?? []).join(", ")}</li>
          <li>A blocked save will show: <strong>{a.message}</strong></li>
        </ul>
      </Section>
      <Section title="Java source">
        <pre className="code">{a.source}</pre>
      </Section>
    </>
  );
}

/** Step 3 — the compiler's verdict. Local only; nothing has been sent. */
function ServersideBuild({ a }: { a: Bag }) {
  const b: Bag = a.build ?? {};
  const classes: string[] = b.classes ?? [];
  const errors: string[] = b.compile_errors ?? [];
  return (
    <>
      <Section title={b.ok ? "Compiled" : "Compile failed"}>
        <p className="muted">
          Maven ran over the whole workspace. Nothing was sent to QAD: this proves
          the code compiles against QAD's real types before anything is uploaded.
        </p>
        {errors.length > 0 && (
          <ul className="plain">
            {errors.map((e, i) => <li key={i} className="warn">{e}</li>)}
          </ul>
        )}
      </Section>
      <Section title={`${classes.length} class${classes.length === 1 ? "" : "es"} in the jar`}>
        <ul className="plain">{classes.map((c) => <li key={c}><code>{c}</code></li>)}</ul>
        <p className="muted">{b.jar_bytes} bytes</p>
      </Section>
    </>
  );
}

/** Step 4 — the only stage that writes. */
function ServersideDeploy({ a }: { a: Bag }) {
  const p: Bag = a.plan ?? {};
  const after: string[] = p.classes_after_deploy ?? [];
  const removed: string[] = p.removed ?? [];
  const added: string[] = p.added ?? [];
  return (
    <>
      {removed.length > 0 && (
        <Section title="This deploy DELETES">
          <ul className="plain">
            {removed.map((c) => <li key={c} className="warn"><code>{c}</code></li>)}
          </ul>
          <p className="warn">
            Uploading replaces the entire jar, so these stop working the moment it
            succeeds. QAD reports success either way and gives no warning.
          </p>
        </Section>
      )}

      <Section title={`Afterwards, ${after.length} extension${after.length === 1 ? "" : "s"} will be live`}>
        {/* The FULL list, not a diff: under whole-jar replacement this IS the
            deployment. */}
        <ul className="plain">
          {after.map((c) => (
            <li key={c}>
              <code>{c}</code>{added.includes(c) && <em className="tag"> new</em>}
            </li>
          ))}
        </ul>
        {!p.previously_deployed_known && (
          <p className="warn">
            This app has no recorded successful deploy, so what is live right now is
            unknown: QAD cannot be asked. Anything deployed by other means will be
            replaced by this upload.
          </p>
        )}
      </Section>

      <Section title="Exact request">
        <ul className="plain">
          <li>POST <code>{p.url}</code></li>
          <li>multipart field <code>{p.part_field_name}</code>, filename <code>{p.part_filename}</code></li>
          <li>{p.part_content_type} · {p.jar_bytes} bytes</li>
        </ul>
      </Section>
    </>
  );
}
