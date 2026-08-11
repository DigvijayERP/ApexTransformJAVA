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
      <Section title={`${a.bc_pascal} — ${fields.length} field${fields.length === 1 ? "" : "s"}`}>
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
                    {safe && <span className="rename" title="renamed — SQL reserved word">→ {safe}</span>}
                  </td>
                  <td>{f.dataType}{f.maxLength ? ` (${f.maxLength})` : ""}</td>
                  <td>{f.isPrimary ? "PK" : ""}</td>
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
        <Section key={p.panel} title={`Panel ${p.panel} — ${p.panelName}`}>
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
            Leave one blank and that line is commented out with a TODO — the same
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

function LookupConfig({ a }: { a: Bag }) {
  if (a.awaiting_configuration) {
    const fields: Bag[] = a.fields ?? [];
    return (
      <Section title="Fields marked as needing a lookup">
        <p className="muted">{a.hint}</p>
        <ul className="plain">
          {fields.map((f) => (
            <li key={f.code}>
              <code>{f.code}</code> — can auto-populate:{" "}
              {(f.auto_populate_options ?? []).map((o: Bag) => o.label).join(", ") || "nothing else"}
            </li>
          ))}
        </ul>
      </Section>
    );
  }
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
          ? <Empty>Dry run — the warnings check was rehearsed, not sent.</Empty>
          : <Payload value={warn.data ?? warn} label="Warnings response" />}
      </Section>
      <Payload value={a.payload_preview} label="Exact deploy payload" />
    </>
  );
}

// ── Dispatch ─────────────────────────────────────────────────────────────────
export function Artifact({ kind, artifact, onBrowseUris }: {
  kind: ArtifactKind | undefined;
  artifact: Bag;
  onBrowseUris?: (v: Record<string, string>) => void;
}) {
  switch (kind) {
    case "text":            return <Text a={artifact} />;
    case "field_spec":
    case "field_spec_diff": return <FieldSpec a={artifact} />;
    case "form_layout":     return <FormLayout a={artifact} />;
    case "handler_code":    return <HandlerCode a={artifact} onBrowseUris={onBrowseUris} />;
    case "view_config":     return <ViewConfig a={artifact} />;
    case "lookup_config":   return <LookupConfig a={artifact} />;
    case "deploy_preview":  return <DeployPreview a={artifact} />;
    default:
      // Never drop it. An unrenderable artifact is still a decision the user
      // is being asked to make.
      return (
        <>
          <Empty>No renderer for “{kind ?? "unknown"}” — showing it raw.</Empty>
          <pre className="code">{JSON.stringify(artifact, null, 2)}</pre>
        </>
      );
  }
}
