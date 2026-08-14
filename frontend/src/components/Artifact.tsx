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
            <label key={p.field} className="field">
              <span><code>{p.field}</code> <small>{p.context}</small></span>
              <input
                value={uris[p.field] ?? ""}
                placeholder="urn:browse:bebrowse:com.qad.erp.base.customers"
                onChange={(e) => setUris({ ...uris, [p.field]: e.target.value })}
              />
            </label>
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

// ── Dispatch ─────────────────────────────────────────────────────────────────
export function Artifact({ kind, artifact, onBrowseUris, onConfigure, onParentKey,
                          onServersidePick }: {
  kind: ArtifactKind | undefined;
  artifact: Bag;
  onBrowseUris?: (v: Record<string, string>) => void;
  onConfigure?: (c: Bag[]) => void;
  onParentKey?: (key: string) => void;
  onServersidePick?: (v: { bc_name?: string; target_class?: string }) => void;
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

/** Step 1 — which component, and what rule. */
function ServersideTarget({ a, onPick }: {
  a: Bag; onPick?: (v: { bc_name?: string; target_class?: string }) => void;
}) {
  const [query, setQuery] = useState("");
  const [fieldQuery, setFieldQuery] = useState("");

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
        <Section title={`${deployed.length} validation${deployed.length === 1 ? "" : "s"} recorded as deployed`}>
          {deployed.length === 0 ? (
            <p className="warn">
              Nothing is recorded as deployed for this app, so there is nothing to
              remove here. If a validation was deployed by other means this app has
              no record of it: QAD cannot be asked what is currently live.
            </p>
          ) : (
            <div className="pick-list" role="listbox">
              {deployed.map((c) => (
                <div key={c} role="option" aria-selected={c === a.target_class}
                     className={"pick-item" + (c === a.target_class ? " active" : "")}
                     onClick={() => onPick?.({ target_class: c })}>
                  <span className="pick-name">{c.split(".").pop()}</span>
                  <span className="pick-meta">{c}</span>
                </div>
              ))}
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
  const shown = options
    .filter((o) => o.name.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 60);
  const visibleFields = fields.filter(
    (f) => f.name.toLowerCase().includes(fieldQuery.toLowerCase()));

  return (
    <>
      <Section title="The rule">
        <p>{a.rule}</p>
        <ul className="plain">
          <li>A blocked save will show: <strong>{a.message}</strong></li>
          <li>Java class: <code>{a.class_name}</code></li>
        </ul>
      </Section>

      <Section title={`Component: ${bc.name}`}>
        <p className="muted">
          {bc.app_owned ? "Created by this app." : "A standard QAD component."}{" "}
          <code>{bc.package}</code>
        </p>
        {/* The distinction that decides whether a rule fires at all. */}
        <p className={bc.has_confirmation_variants ? "warn" : "muted"}>
          {bc.has_confirmation_variants
            ? `This component also saves through confirmation methods, so all
               ${savePaths.length} paths are guarded. Guarding only create and
               update would deploy cleanly and never fire.`
            : `${savePaths.length} save paths, all guarded.`}
        </p>
        <div className="fills">
          {savePaths.map((p: Bag) => (
            <span key={p.name} className="dry-pill">{p.name}</span>
          ))}
        </div>
      </Section>

      {options.length > 0 && (
        <Section title="Target a different component">
          <label className="field">
            <span>Search {options.length} components</span>
            <input value={query} placeholder="purchase, sales, item…"
                   onChange={(e) => setQuery(e.target.value)} />
          </label>
          <div className="pick-list" role="listbox">
            {shown.map((o) => (
              <div key={`${o.package}.${o.name}`} role="option"
                   aria-selected={o.name === bc.name}
                   className={"pick-item" + (o.name === bc.name ? " active" : "")}
                   onClick={() => onPick?.({ bc_name: o.name })}>
                <span className="pick-name">{o.name}</span>
                <span className="pick-meta">{o.app_owned ? "app" : "QAD"} · {o.package}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      <Section title={`Fields you can check (${fields.length})`}>
        <p className="muted">
          Read from the compiled component, with their real Java types. Naming a
          field in the rule is enough; the types are what keep the generated code
          correct.
        </p>
        <label className="field">
          <span>Filter</span>
          <input value={fieldQuery} placeholder="remarks, date, status…"
                 onChange={(e) => setFieldQuery(e.target.value)} />
        </label>
        <div className="fills">
          {visibleFields.slice(0, 120).map((f: Bag) => (
            <span key={f.name} className="dry-pill" title={`${f.getter}() returns ${f.type}`}>
              {f.name}<em className="chip-type">{f.type}</em>
            </span>
          ))}
          {visibleFields.length === 0 && <span className="muted">No field matches.</span>}
        </div>
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
