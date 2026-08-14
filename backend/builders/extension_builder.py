"""
Generates the Java source for a server-side extension.

THE DIVISION OF LABOUR, PORTED FROM AUX

`aux_web_version/backend/sss/templates.py:6-8` states the rule this module
follows: "The LLM only produces the validation body ... Everything structural -
references, namespace, the class extending the STANDARD BC, factory, service
registration - is generated here so the output always compiles."

Here that means the model contributes ONE thing: the statements inside a loop
over records, given a `record` variable. Everything else - package, imports,
annotation, superclass, one override per save path, the null-safe array walk,
the super call, `throwAddedValidationErrors()` - is emitted from facts read out
of the dependency jar by `core.jar_inspector`.

WHY THE SIGNATURES CANNOT BE TEMPLATED

Two BC families, two shapes (both observed live 2026-08-14):

    standard    void create(PurchaseOrderHeaderDataSet)
                void createWithConfirmation(PurchaseOrderHeaderDataSet,
                                            InputOutput<PurchaseOrderHeaderConfDataSet>)
    generated   void create(InputOutput<DigSmokeTestDataSet>)

so the DataSet is sometimes the bare first parameter, sometimes wrapped, and
sometimes accompanied by a confirmation parameter that must be passed through
untouched. Each override is therefore emitted from that path's ACTUAL parameter
list, and the expression handed to the validator is derived, never assumed.

Missing a save path is the silent failure this whole case is designed against:
a class overriding only create/update on a coded BC compiles, deploys, returns
HTTP 200 and never runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Optional

from builders.identity import AppIdentity, resolve
from core.jar_inspector import BusinessComponent, SavePath

# QAD types every extension needs.
_EXTENSION_ANNOTATION = "com.qad.ipc.service.Extension"
_EXEC_ERROR = "com.qad.ipc.dto.BCExecutionError"


class ExtensionBuildError(ValueError):
    """The requested extension cannot be expressed against this BC."""


@dataclass
class ValidationSpec:
    """What to generate. `body` is the only model-authored part."""
    class_name: str
    description: str
    # Statements run once per record, with a `record` variable in scope. May
    # call addValidationError("..."). No trailing throwAddedValidationErrors():
    # the template owns that so it can never be forgotten.
    body: str
    # Save-path METHOD NAMES to override. Empty means every mutating path,
    # which is the safe default and what the UI should preselect.
    guarded_paths: List[str] = dc_field(default_factory=list)

    def sanity(self) -> None:
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", self.class_name or ""):
            raise ExtensionBuildError(
                f"'{self.class_name}' is not a valid Java class name. Use PascalCase, "
                f"letters and digits only.")
        if not (self.body or "").strip():
            raise ExtensionBuildError("The validation body is empty - there is nothing to enforce.")


def _generic_inner(java_type: str) -> Optional[str]:
    m = re.fullmatch(r"[\w.]+<(.+)>", java_type)
    return m.group(1) if m else None


def _param_names(path: SavePath) -> List[str]:
    """Readable parameter names, derived from their types.

    'PurchaseOrderHeaderDataSet' -> dataSet
    'InputOutput<...ConfDataSet>' -> confirmation
    """
    names: List[str] = []
    for i, t in enumerate(path.param_types):
        inner = _generic_inner(t) or t
        simple = inner.rsplit(".", 1)[-1]
        if simple.endswith("ConfDataSet"):
            base = "confirmation"
        elif simple.endswith("DataSet"):
            base = "dataSet"
        else:
            base = simple[0].lower() + simple[1:] if simple else f"arg{i}"
        name = base
        n = 2
        while name in names:
            name = f"{base}{n}"
            n += 1
        names.append(name)
    return names


def _dataset_expression(path: SavePath, names: List[str], data_set: str) -> str:
    """How to get the DataSet out of this method's parameters.

    Bare parameter -> the parameter itself.
    InputOutput<DataSet> -> .getValue() on it.
    """
    for t, n in zip(path.param_types, names):
        if t == data_set:
            return n
        if _generic_inner(t) == data_set:
            return f"{n}.getValue()"
    raise ExtensionBuildError(
        f"'{path.name}' does not take {data_set.rsplit('.', 1)[-1]}, so a validation "
        f"cannot read the records it is about to save. Parameters: "
        + ", ".join(path.param_types))


def _select_paths(bc: BusinessComponent, wanted: List[str]) -> List[SavePath]:
    if not wanted:
        chosen = bc.mutating_paths
        if not chosen:
            raise ExtensionBuildError(
                f"{bc.name} exposes no create/update/delete methods to guard.")
        return chosen

    by_name = {p.name: p for p in bc.save_paths}
    missing = [w for w in wanted if w not in by_name]
    if missing:
        raise ExtensionBuildError(
            f"{bc.name} has no save path(s) named {', '.join(missing)}. It offers: "
            + ", ".join(p.name for p in bc.save_paths))
    return [by_name[w] for w in wanted]


def _imports(bc: BusinessComponent, paths: List[SavePath], pkg: str) -> List[str]:
    """Every type the emitted source names, minus same-package and java.lang."""
    needed = {bc.base_service, bc.data_set, bc.record, _EXEC_ERROR, _EXTENSION_ANNOTATION}
    for p in paths:
        for t in p.param_types:
            needed.add(t)
            inner = _generic_inner(t)
            if inner:
                # The raw generic type itself must be imported too.
                needed.add(t.split("<", 1)[0])
                needed.add(inner)
    out = set()
    for t in needed:
        if not t or "<" in t or "." not in t:
            continue
        if t.startswith("java.lang.") or t.rsplit(".", 1)[0] == pkg:
            continue
        out.add(t)
    return sorted(out)


def build_extension_source(bc: BusinessComponent, spec: ValidationSpec,
                           identity: Optional[AppIdentity] = None) -> Dict[str, object]:
    """Emit a complete, compilable extension class.

    Returns the source plus a summary the gate renders, so the human approving
    it sees which save paths are covered without reading Java.
    """
    spec.sanity()
    ident = resolve(identity)
    if not bc.data_set or not bc.record or not bc.accessor:
        raise ExtensionBuildError(
            f"{bc.name} has no DataSet/Record/accessor in the jar, so no validation "
            f"can be generated against it.")

    # The app package with NO business-component segment. Confirmed to compile
    # and deploy 2026-08-14; generated types live in a deeper package and are
    # imported rather than shared.
    pkg = ident.module
    paths = _select_paths(bc, spec.guarded_paths)

    record_simple = bc.record.rsplit(".", 1)[-1]
    data_simple = bc.data_set.rsplit(".", 1)[-1]

    overrides: List[str] = []
    for path in paths:
        names = _param_names(path)
        expr = _dataset_expression(path, names, bc.data_set)
        params = ", ".join(f"{_short(t)} {n}" for t, n in zip(path.param_types, names))
        overrides.append(
            f"    @Override\n"
            f"    public {path.returns} {path.name}({params}) throws {_short(_EXEC_ERROR)} {{\n"
            f"        {_VALIDATE}({expr});\n"
            f"        super.{path.name}({', '.join(names)});\n"
            f"    }}"
        )

    # Re-indent the model's statements to sit inside the record loop. Its own
    # relative indentation is preserved so nested blocks still read correctly.
    raw = spec.body.strip().splitlines()
    common = min((len(l) - len(l.lstrip()) for l in raw if l.strip()), default=0)
    body = "\n".join(f"                {l[common:]}" if l.strip() else "" for l in raw)

    covered = ", ".join(p.name for p in paths)
    note = ""
    if bc.has_confirmation_variants:
        note = (f"\n * {bc.name} is a coded QAD component: it saves through the\n"
                f" * *WithConfirmation methods as well as the plain ones, so BOTH are\n"
                f" * overridden. Guarding only create/update here would compile, deploy\n"
                f" * and never fire.")

    source = f"""package {pkg};

{chr(10).join(f'import {i};' for i in _imports(bc, paths, pkg))}

/**
 * {spec.description}
 *
 * Generated by Adaptive. The structure below is derived from
 * {bc.base_service.rsplit('.', 1)[-1]} as compiled in the app's dependency jar;
 * only the checks inside {_VALIDATE} describe the rule itself.
 *
 * Save paths covered: {covered}{note}
 */
@{_short(_EXTENSION_ANNOTATION)}
public class {spec.class_name} extends {_short(bc.base_service)} {{

{(chr(10) + chr(10)).join(overrides)}

    private void {_VALIDATE}({data_simple} dataSet) throws {_short(_EXEC_ERROR)} {{
        if (dataSet == null) {{
            return;
        }}
        {record_simple}[] records = dataSet.{bc.accessor}();
        if (records != null) {{
            for ({record_simple} record : records) {{
                if (record == null) {{
                    continue;
                }}
{body}
            }}
        }}
        throwAddedValidationErrors();
    }}
}}
"""

    return {
        "source": source,
        "class_name": spec.class_name,
        "package": pkg,
        "relative_path": f"{pkg.replace('.', '/')}/{spec.class_name}.java",
        "summary": {
            "bc": bc.name,
            "bc_package": bc.package,
            "app_owned": bc.is_app_owned,
            "class_name": spec.class_name,
            "guarded_paths": [p.name for p in paths],
            "covers_confirmation_variants": any(p.with_confirmation for p in paths),
            "confirmation_variants_exist": bc.has_confirmation_variants,
            "record": bc.record,
            "accessor": bc.accessor,
        },
        "warnings": _warnings(bc, paths),
    }


_VALIDATE = "validate"


def _warnings(bc: BusinessComponent, paths: List[SavePath]) -> List[str]:
    out: List[str] = []
    chosen = {p.name for p in paths}
    # THE check this module exists for.
    unguarded = [p.name for p in bc.mutating_paths if p.name not in chosen]
    if unguarded:
        out.append(
            f"{bc.name} also saves through {', '.join(unguarded)}, which this class does "
            f"NOT override. A save on those paths will bypass the rule entirely - it will "
            f"deploy cleanly and appear to work.")
    if bc.has_confirmation_variants and not any(p.with_confirmation for p in paths):
        out.append(
            f"{bc.name} is a coded QAD component whose UI normally saves through the "
            f"*WithConfirmation methods. None are covered, so this rule will almost "
            f"certainly never fire.")
    return out


def _short(java_type: str) -> str:
    """Fully-qualified to simple, generics preserved: InputOutput<FooConfDataSet>."""
    return re.sub(r"[A-Za-z_][\w.]*\.([A-Z]\w*)", r"\1", java_type)
