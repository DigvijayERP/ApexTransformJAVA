# PHASE 3 — Case 2 (Embedded BC) Build Plan

**Written 2026-08-12**, after the owner's scope decisions and the EmbeddedExmpl2 wire captures.
Discovery and evidence live in `PHASE3_CASE2_DISCOVERY.md` and
`captures/2026-08-12_embedded_EmbeddedExmpl2.md`; this file is the shorter build contract.

## Owner decisions (2026-08-12)

1. The embedded grid IS visible on the Items screen after child-only deploy — U4/U9/U10 settled.
   Zero parent-side writes is the complete core flow.
2. The standalone view for the embedded child is IN SCOPE, against the audit's recommendation.
   It ships as a conditional, gated, clearly-flagged stage: the docs say embedded BCs are not
   menu-accessible and AUX never provably exercised its step 8, so the first live approval of
   this stage is itself the experiment that settles U11.
3. `.p`/`.cls` input is IN SCOPE. The Progress parser ports from AUX with one rework: parse ALL
   temp-tables, not only the first (AUX: progress_parser.py:379-380), because a parent+child
   file naturally holds two. Parsed schema grounds the requirements prompt; the LLM still shapes
   the spec and the gate still decides.

## The embedded stage set (mode "embedded")

Stage identity stays in `core/stages.py` as the single source, now keyed by run mode. The
standard manifest is unchanged; embedded runs get:

| # | id | gate | writes | notes |
|---|----|------|--------|-------|
| 1 | requirements | yes | none | LLM + optional parsed ABL; proposes a parent from the registry; the GATE shows a parent picker so the human confirms or overrides the choice (AUX let the LLM guess unchecked) |
| 2 | fields | yes | bc.create (+ metadata read/write only when dropdowns exist) | PK trio first: domain field + every parent non-domain PK + child PK; PascalCase codes per the capture; one-shot entity save per the capture |
| 3 | relate | yes | relation.create | The stage that makes it embedded. Gate shows parent, cardinality, and EVERY PK mapping. Payload verbatim from the capture |
| 4 | deploy | yes | deploy.check_warnings, deploy.business_entity | Same proven Case 1 contract; capture confirms dataStoreURI urn:datastore:com.yash.extension |
| 5 | view | yes, conditional | view.register | Only when the user asked for a separate view at stage 1. Flagged experimental (docs contradiction). AFTER deploy, matching AUX's ordering |

No form, no handler, no lookups: platform semantics for embedded children (discovery, Portable #1).

## Payload sources — capture is authority, AUX is not

- Entity save: the capture's single entitymetadatas POST. Client-generated `uniqueID` GUIDs per
  field, NO percent-encoded URI scheme, NO modelId sequence, `browseSearchOperators` echoed as
  captured. `initialTableName` = `xx` + bc lowercase (prefix is convention, suffix free).
  Field codes PascalCase with `physicalFieldName` equal to the code; `fieldURI` from entityName.
- Relation: `relationID` = plain uuid4, echoed in `uri`; `BERelationFields` maps EVERY parent PK
  (child field name mirrors the parent's, the pattern the capture half-proves with
  ItemCode→ItemCode); flags exactly as captured (`isExtension` true, `isEmbedded` false,
  `isIncludeOnParent` false, `isUseInBusinessDocument` true, `isCascadeDeleteForBD` true).
- Deploy: Case 1's existing deploy_builder (check_warnings + full deployBusinessEntity). The
  capture shows the UI calling deployBusinessEntity twice instead; recorded, not copied — our
  contract is already proven live on this environment.

## Parent registry

`config/parents.json`: candidate parents seeded from the 2026-08-12 live probe, each with uri,
entity_code, ordered pk_fields with data types, domain field name, and an `offerable` flag.
InventoryMaster ships `offerable: false` with reason `doNotExtend on eeadaptive`. AUX's
single-`fk_field` model is replaced by the full PK list because the relation must map every
parent PK (WorkOrderMasters has three). `core/parent_registry.py` reads the file and can
re-verify a parent live (bc.metadata.read) at gate time; the live read is the authority when
they disagree, and a mismatch is surfaced, not silently patched.

## Prompts

`EMBEDDED_REQUIREMENTS_GATHERING` and `EMBEDDED_FIELD_CREATOR` port from AUX (they carry zero
old-env identity) with these changes: the entity menu injects only `offerable` parents; the
domain PK field defaults to the parent's own domain field name (capture proves the name is
user-chosen and identical names work, ItemCode→ItemCode); field codes PascalCase; the field
prompt is told every parent PK it must mirror, not one FK; parsed ABL tables, when present, are
injected as authoritative schema context.

## Known deferrals created by this plan

- The `view` stage for embedded children is experimentally flagged until its first live success
  (U11's experiment).
- `lookup_detector.py` is NOT ported: embedded children cannot carry lookups, and Case 1's
  lookup flow has its own settled machinery. Revisit only if `.p` input for Case 1 standalone
  runs should auto-mark `needsLookup`.
- appName casing: the capture sent `DigWish`, Case 1's accepted lookups sent `digwish`. The
  builders use the configured identity verbatim; if an embedded save rejects on appName, this is
  the recorded knob.
