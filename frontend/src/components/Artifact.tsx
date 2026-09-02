// Renders what a stage produced — the real content, not a status line.
//
// Dispatches on `artifact_kind`. An UNKNOWN kind falls through to raw JSON
// rather than rendering nothing: AUX silently drops four SSE frame types its
// frontend does not declare, and in a gated UI a frame you cannot render is a
// decision made blind.

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { api, type ArtifactKind, type BrowseField, type CatalogBrowse } from "../api";

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

// The three keys a suggestion row needs to render. Deliberately narrow: the
// rows arrive either from the stage artifact (untyped) or from the catalog
// search (CatalogBrowse), and both satisfy this.
type PickRow = { code: string; description: string; uri: string };

// Ranked guesses from QAD's own browse list, sent by the backend for one field.
// Clicking one fills the Browse URI input. They are only guesses ranked by
// name, so the copy says to check one before using it.
function BrowsePicks({ list, onPick }: { list: PickRow[]; onPick: (uri: string) => void }) {
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

function FieldSpec({ a, onBcName }: { a: Bag; onBcName?: (bc_name: string) => void }) {
  const fields: Bag[] = a.spec?.fields ?? [];
  const renamed: Bag[] = a.renamed_fields ?? [];
  const renamedOf = (code: string) =>
    renamed.find((r) => r.asked_for === code)?.actual_column;
  const suggested: string | undefined = a.suggested_name ?? undefined;

  // The label QAD will receive is not re-derived here: the payload the backend
  // already built carries it, so the gate cannot show one thing and send
  // another. Position matches because the builder emits one entityField per
  // spec field, in order; the code match is the fallback for a preview that
  // does not line up.
  const built: Bag[] = a.payload_preview?.entityMetadatas?.[0]?.entityFields ?? [];
  const labelFor = (f: Bag, i: number): string => {
    const byPos = built.length === fields.length ? built[i] : undefined;
    const byCode = built.find(
      (b) => b.entityFieldCode === (renamedOf(f.code) ?? f.code));
    return String((byPos ?? byCode)?.fieldLabel ?? "");
  };
  // Having a label proves nothing: an embedded spec gives every field one,
  // built from the parent's field code, with no source pasted at all. The
  // backend sets labelFromSource only where the pasted source really did
  // label that field, so the marker reads that flag and nothing else.
  const fromSource = (f: Bag) => f.labelFromSource === true;

  return (
    <>
      {/* The backend asked QAD whether the name is free before anything is
          written. It only sets name_taken when it got a real answer, so an
          absent key means "free or could not tell", never a false all-clear. */}
      {a.name_taken && (
        <Section title="That name is already taken">
          <p className="warn">
            QAD already has a business component called <code>{a.bc_pascal}</code>.
            Nothing will be created if you approve this stage.
          </p>
          {suggested ? (
            <>
              <p className="muted">
                <code>{suggested}</code> is free. Using it renames the component
                only: the fields below stay exactly as they are, and no model is
                asked to redo anything.
              </p>
              {onBcName && (
                <button className="ghost" onClick={() => onBcName(suggested)}>
                  Use {suggested}
                </button>
              )}
            </>
          ) : (
            <p className="muted">
              No free name could be suggested. Regenerate this stage and say
              what to call it instead.
            </p>
          )}
        </Section>
      )}

      <Section title={`${a.bc_pascal}: ${fields.length} field${fields.length === 1 ? "" : "s"}`}>
        <table className="grid">
          <thead>
            <tr><th>Field</th><th>Label</th><th>Type</th><th>Key</th><th>Required</th><th>Lookup</th><th>Values</th></tr>
          </thead>
          <tbody>
            {fields.map((f, i) => {
              const safe = renamedOf(f.code);
              return (
                <tr key={f.code}>
                  <td>
                    <code>{f.code}</code>
                    {/* A SQL reserved word becomes a differently-named QAD
                        column. Silent renaming is what a gate exists to catch. */}
                    {safe && <span className="rename" title="renamed, SQL reserved word">→ {safe}</span>}
                  </td>
                  {/* What the user will read on the QAD screen. A label the
                      pasted source supplied is marked, because the alternative
                      is a label made up from the field code. */}
                  <td>
                    {labelFor(f, i)}
                    {fromSource(f) && (
                      <span className="from-source" title="taken from the source you pasted">
                        from source
                      </span>
                    )}
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

const BROWSE_URI_PREFIX = "urn:browse:";

/** Well formed enough to ask QAD about. Not a validity check: only QAD knows
 *  whether a browse exists, and it answers 200 with no rows when it does not. */
function isBrowseUri(uri: string): boolean {
  return uri.trim().startsWith(BROWSE_URI_PREFIX)
    && uri.trim().length > BROWSE_URI_PREFIX.length;
}

// What we know about one browse's field list. "error" covers both a failed read
// and a browse QAD listed nothing for, because the user's next move is the same
// in both cases: type the field by hand.
type FieldList = {
  status: "idle" | "loading" | "ok" | "error";
  fields: BrowseField[];
  message: string;
};

const NO_LIST: FieldList = { status: "idle", fields: [], message: "" };

/** The field lists for every browse URI this gate is pointing at, one fetch per
 *  URI, kept for as long as the gate is open.
 *
 *  This is a READ. It reaches QAD but changes nothing, so it runs on a rehearsal
 *  run too - unlike `stage_lookups`, which still does not resolve on a dry run.
 *  A field the user cannot see is a decision made blind, and the copy below says
 *  where the list came from.
 */
function useBrowseFields() {
  const [byUri, setByUri] = useState<Record<string, FieldList>>({});
  // Which URIs have already been asked about. A ref, not state: the guard has to
  // be true the moment load() is called, not on the next render.
  const asked = useRef<Record<string, true>>({});

  const load = useCallback((raw: string) => {
    const uri = raw.trim();
    if (!isBrowseUri(uri) || asked.current[uri]) return;
    asked.current[uri] = true;
    setByUri((m) => ({ ...m, [uri]: { status: "loading", fields: [], message: "" } }));

    api.browseFields(uri).then((r) => {
      setByUri((m) => ({
        ...m,
        [uri]: r.fields.length
          ? { status: "ok", fields: r.fields, message: "" }
          : { status: "error", fields: [], message: r.note ?? "QAD listed no fields for this browse." },
      }));
    }).catch((e: unknown) => {
      // Let a later edit try again: a read can fail for a reason that passes.
      delete asked.current[uri];
      setByUri((m) => ({
        ...m,
        [uri]: {
          status: "error", fields: [],
          message: e instanceof Error ? e.message
            : "Could not read the fields on this browse.",
        },
      }));
    });
  }, []);

  return { byUri, load };
}

/** A field name: picked from QAD's list when we have one, typed when we do not.
 *
 *  The text input never goes away. It is the fallback when the read fails, and
 *  it stays reachable through "type it instead" even when the list loaded, so a
 *  list that is somehow short of the field the user needs cannot block the run.
 *  The value is held by the caller, so swapping control keeps it.
 */
function FieldChoice({ list, value, placeholder, className, inPill = false, onChange }: {
  list: FieldList;
  value: string;
  placeholder: string;
  className?: string;
  /** Rendered inside a fill pill: no status lines (the field above already shows
   *  them for the same browse) and the click must not reach the pill's label. */
  inPill?: boolean;
  onChange: (v: string) => void;
}) {
  const [typing, setTyping] = useState(false);
  const canPick = list.status === "ok" && list.fields.length > 0;
  const asText = !canPick || typing;
  // A value typed by hand, or left from an earlier browse, is not in the list.
  // Carry it as its own option so swapping to the select cannot blank it.
  const stray = canPick && !!value && !list.fields.some((x) => x.field === value);

  return (
    <>
      {asText ? (
        <input
          className={className}
          value={value}
          placeholder={placeholder}
          onClick={inPill ? (e) => e.preventDefault() : undefined}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <select className={className} value={value}
                onChange={(e) => onChange(e.target.value)}>
          <option value="">Choose a field</option>
          {stray && <option value={value}>{value} (typed by hand)</option>}
          {list.fields.map((x) => (
            <option key={x.field} value={x.field}>
              {x.label ? `${x.field} (${x.label})` : x.field}
            </option>
          ))}
        </select>
      )}

      {!inPill && list.status === "loading" && (
        <p className="muted">Reading the fields on this browse...</p>
      )}
      {!inPill && list.status === "error" && <p className="warn">{list.message}</p>}

      {canPick && (
        <button type="button" className="swap-input"
                onClick={() => setTyping(!typing)}>
          {typing ? "pick from the list" : "type it instead"}
        </button>
      )}
    </>
  );
}

/** A search over the local browse catalog, for when the per-field suggestions
 *  missed. Reads config/browses.json on the server and never touches QAD. */
function BrowseSearch({ onPick }: { onPick: (uri: string) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<CatalogBrowse[]>([]);

  useEffect(() => {
    const text = q.trim();
    if (text.length < 2) { setHits([]); return; }
    const t = setTimeout(() => {
      api.browseSearch(text).then((r) => setHits(r.browses)).catch(() => setHits([]));
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <>
      <label className="field">
        <span>Or search the browse list by name</span>
        <input value={q} placeholder="customer"
               onChange={(e) => setQ(e.target.value)} />
      </label>
      <BrowsePicks list={hits} onPick={onPick} />
    </>
  );
}

/** One field's lookup configuration: which browse, which field on it, and which
 *  other form fields it fills in. */
function LookupFieldConfig({ f, c, list, set, load }: {
  f: Bag;
  c: LookupCfg;
  list: FieldList;
  set: (patch: Partial<LookupCfg>) => void;
  load: (uri: string) => void;
}) {
  const uri = c.uri.trim();
  const opts: Bag[] = f.auto_populate_options ?? [];

  // Typing a URI fires one request when the typing stops, not one per keystroke.
  // A clicked suggestion does not wait: it calls load() itself, and the per-URI
  // cache makes this timer a no-op when it lands.
  useEffect(() => {
    if (!isBrowseUri(uri)) return;
    const t = setTimeout(() => load(uri), 400);
    return () => clearTimeout(t);
  }, [uri, load]);

  const pick = (picked: string) => { set({ uri: picked }); load(picked); };

  return (
    <Section title={f.label ?? f.code}>
      <label className="field">
        <span>Browse URI (which records to choose from)</span>
        <input
          value={c.uri}
          placeholder="urn:browse:bebrowse:com.yash.digwish.digsmoketest"
          onChange={(e) => set({ uri: e.target.value })}
        />
      </label>

      <BrowsePicks list={f.browse_candidates ?? []} onPick={pick} />
      <BrowseSearch onPick={pick} />

      {/* A div, not a label: the control below is followed by the "type it
          instead" button, so the label would end up wrapping two controls and
          clicking the button would count as clicking the field. */}
      <div className="field">
        <span>Field on that browse (the value returned)</span>
      </div>
      <FieldChoice
        list={list}
        value={c.field}
        placeholder="testCode"
        onChange={(v) => set({ field: v })}
      />

      {list.status === "ok" && (
        <p className="muted">
          These are the fields QAD lists for this browse, read just now. Reading
          the list changes nothing in QAD, so it works on a rehearsal run too.
        </p>
      )}

      {c.field.trim() && (
        <p className="muted">
          Result and search field: <code>{c.field.trim()}</code>. On a live
          run this is matched against the fields QAD lists for this browse,
          and QAD's own spelling is what gets sent.
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
                      set({ fills });
                    }}
                  />
                  {o.label}
                  {checked && (
                    <FieldChoice
                      list={list}
                      inPill
                      className="fill-source"
                      value={c.fills[o.target]}
                      placeholder="from which browse column?"
                      onChange={(v) => set({ fills: { ...c.fills, [o.target]: v } })}
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
}

function LookupForm({ a, onConfigure }: { a: Bag; onConfigure?: (c: Bag[]) => void }) {
  const fields: Bag[] = a.fields ?? [];
  const [cfg, setCfg] = useState<Record<string, LookupCfg>>(
    () => Object.fromEntries(fields.map((f) => [f.code, { uri: "", field: "", fills: {} }])),
  );

  const set = (code: string, patch: Partial<LookupCfg>) =>
    setCfg((c) => ({ ...c, [code]: { ...c[code], ...patch } }));

  // One field list per browse URI, shared by every field on this gate: two
  // form fields pointing at the same browse ask QAD once.
  const { byUri, load } = useBrowseFields();

  const ready = fields.every((f) => {
    const c = cfg[f.code];
    return c?.uri.trim() && c?.field.trim()
      && Object.values(c.fills).every((src) => src.trim());
  });

  // Send the column EXACTLY as typed. Do not build "<entity>.<column>" here.
  // QAD returns complete field names already, and their shape differs per
  // browse: digSmokeTest.testCode on one of ours, debtor.DebtorCode on cm001,
  // but a bare pt_part on pp125 and changeStatus on cm007. Prefixing turned
  // debtor.DebtorCode into cm001.debtor.DebtorCode and QAD rejected it. The
  // backend resolves whatever is typed against QAD's own list for this browse
  // and sends back QAD's exact spelling, so composing here can only be wrong.
  const build = () => onConfigure?.(fields.map((f) => {
    const c = cfg[f.code];
    const entity = entityOf(c.uri);
    const column = c.field.trim();
    return {
      field_code: f.code,
      browse_uri: c.uri.trim(),
      browse_label: entity.charAt(0).toUpperCase() + entity.slice(1),
      browse_entity: entity,
      result_field: column,
      search_field: column,
      additional_results: Object.entries(c.fills).map(([target, source]) => ({
        field: source.trim(),
        target,
      })),
    };
  }));

  return (
    <>
      <Section title="Configure each lookup">
        <p className="muted">{a.hint}</p>
      </Section>

      {fields.map((f) => (
        <LookupFieldConfig
          key={f.code}
          f={f}
          c={cfg[f.code]}
          list={byUri[cfg[f.code].uri.trim()] ?? NO_LIST}
          set={(patch) => set(f.code, patch)}
          load={load}
        />
      ))}

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
                          onBcName, onServersidePick }: {
  kind: ArtifactKind | undefined;
  artifact: Bag;
  onBrowseUris?: (v: Record<string, string>) => void;
  onConfigure?: (c: Bag[]) => void;
  onParentKey?: (key: string) => void;
  /** Field gate: re-run the stage under a different component name. */
  onBcName?: (bc_name: string) => void;
  onServersidePick?: (v: { bc_name?: string; target_class?: string; instruction?: string }) => void;
}) {
  switch (kind) {
    case "text":            return <Text a={artifact} />;
    case "field_spec":
    case "field_spec_diff": return <FieldSpec a={artifact} onBcName={onBcName} />;
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
