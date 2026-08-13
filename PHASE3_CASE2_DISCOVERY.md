# PHASE 3 — Case 2 (Embedded BC) Discovery

**Written 2026-08-12.** Product of a 9-agent parallel audit of `aux_web_version` (read-only
reference), the QAD training guides (classes 3, 6, 7), and `PHASE0_AUDIT.md`, cross-checked into
portable / stale / unknown. Raw structured findings (343 cited facts) are in
`CASE2_DISCOVERY_DATA.json` next to this file. Citations are `file:line` in AUX unless prefixed
`C3:`/`C6:`/`C7:` (training-guide classes) or named otherwise. Facts are [CONFIRMED] unless a
bullet says otherwise; anything uncertain is in the Unknowns section by design.

## What Case 2 is

An **embedded child Business Component under an existing parent BC** — QAD's "extension" feature
(class 3). The artifact set is: child BC with data-extension flags + fields + ONE child-to-parent
BERelation with two field mappings + deploy. **No form, no view, no event handler, no lookups for
the child** — the parent's form grows an embedded grid automatically after child-only deploy
(page refresh may be needed; the parent is never redeployed). AUX implements this as
`pipeline_embedded.py` (7 steps, 8 with an optional standalone view), invoked via
`POST /api/run` with `mode="embedded"`, 2-3 LLM calls, zero human gates.

The flow in AUX: (1) LLM picks a parent from a registry menu and names the BC; (2) LLM emits a
field spec whose first three fields are the mandatory PK trio `domaincodeEx` + parent-FK + child
PK; (3) POST the Entity Builder metadata payload; (4) on failure, one LLM auto-fix and a single
retry; (3.5) GET-patch-POST round trip wiring dropdowns to data lists; (5) POST the BERelation
(MANYTOONE, `relationType "child"`, two BERelationFields); (6) POST deployCheckForWarnings
(response discarded); (7) POST deployBusinessEntity; (8, optional) POST a standalone view.

## Portable — approaches worth carrying over (20)

**1. Case 2 artifact set: embedded child BC (data-extension flags) + fields + one child->parent BERelation with field mapping + deploy; NO form, NO browse, NO view, NO event handler, NO lookups for the child**
   - AUX's embedded pipeline structure matches QAD's official procedure exactly (Embedded checkbox BC, Child relationship, auto-built grid, skip Form/View); this is platform semantics, not old-env accident
   - Cites: `backend/pipeline_embedded.py:29-41`; `PHASE0_AUDIT.md:831-836`; `C3:57-342`; `C3:319-321`

**2. Mandatory PK trio discipline: field 1 domaincodeEx (character), field 2 = parent FK field, field 3 = child-specific PK that is NOT part of the FK; custom fields non-PK after**
   - Grounded in the QAD rule quoted verbatim in the prompt ('Full primary key of Extension-entity cannot be contained in the foreign key of N-1 relation') and corroborated by docs (child PK = parent keys + own distinguishing keys); without field 3 QAD rejects the BERelation
   - Cites: `backend/agents/prompts.py:467-479`; `backend/agents/prompts.py:417`; `C3:109-113`

**3. Deterministic post-LLM safety guard that injects a fallback child PK when the LLM omits one**
   - Cheap defense-in-depth for the load-bearing PK constraint; independent of environment
   - Cites: `backend/pipeline_embedded.py:132-149`

**4. Parent-entity registry mechanism: durable table (entity_code, uri, pk_fields ordered, fk_field, fk_type, description, source builtin|custom) as source of truth, hydrate-at-startup overlay, write-through registration, infer_fk_field heuristic (first PK that is not domaincode/domaincodeex)**
   - The mechanism (not the data) is sound and directly reusable; Adaptive needs the same registry to drive parent selection. The 5 builtin ROWS are stale (see stale list)
   - Cites: `backend/qad_entity_registry.py:1-28`; `backend/qad_entity_registry.py:125-195`; `backend/database.py:33-41`

**5. Embedded children are never registered as eligible parents (no register_and_persist_custom_bc call; backfill filters mode='standard')**
   - What looked like an omission is actually the platform constraint: 'Embedded Business Components cannot be extended' (Related-BC picker defaults to Embedded=No). Keep the omission deliberately in the port
   - Cites: `backend/pipeline.py:778-800`; `backend/main.py:132-134`; `C3:493`

**6. BERelation payload semantics: authored FROM the child (sourceEntity=child, relatedEntity=parent), relationType 'child', exactly two BERelationFields (domaincodeEx -> parent domain field; fk_field -> fk_field identical name), known-working flags isEmbedded=False, isUseInBusinessDocument=True, isIncludeOnParent=False**
   - Direction and mapping structure match the docs' Relationship + Field Mapping procedure; the flag combination is a recorded live-tested working set (2026-07-15). Values re-verify on new env, structure ports
   - Cites: `backend/builders/embedded_builder.py:265-321`; `backend/builders/embedded_builder.py:15-24`; `C3:190-302`

**7. Grid-vs-panel platform finding: MANYTOONE always renders as an embedded grid on the parent form; a panel requires a ONETOONE redesign (child PK = domaincodeEx + parent FK only, no separate child identifier)**
   - AUX's live-test finding is independently corroborated by the training docs (Many-to-One = grid, One-to-One = panel, cardinality auto-identified from key structure); this is the design lever if Case 2 ever wants panels
   - Cites: `backend/builders/embedded_builder.py:15-24`; `C3:39-41`; `C3:749-758`; `PHASE0_AUDIT.md:838-853`

**8. Two-pass dropdown wiring: create with empty dataListCode -> GET the QAD-enriched entity ({data:{...}} unwrap) -> patch_dropdown_fields sets dataListCode+defaultValue -> POST the enriched body back**
   - QAD assigns list codes server-side at create; the round-trip is the discovered contract, shared with the working Case 1 flow. Port the pattern (fixing the sql_safe key mismatch, see stale)
   - Cites: `backend/pipeline_embedded.py:229-262`; `backend/builders/bc_builder.py:98-111`; `backend/builders/bc_builder.py:114-144`

**9. is_qad_success success gate: HTTP 200 counts as success only when submitResult.success==true AND errorSeverity==0 AND errors empty; {error,raw} envelope for transport/non-JSON failures**
   - QAD returns 200 with embedded errors; this triple-check is wire-contract knowledge that transfers to any QRA-style endpoint
   - Cites: `backend/qad_client.py:72-82`

**10. Fresh-token-per-QAD-call policy (no token caching anywhere)**
   - Recorded rationale: QAD sessions are short-lived; safe default for the port (unify AUX's two duplicate auth implementations into one)
   - Cites: `backend/core/qad_session.py:10-16`; `backend/pipeline_embedded.py:164-170`

**11. VALIDATOR_AND_CORRECTOR single-retry auto-fix pattern (fix spec from QAD submitResult, retry create exactly once, abort on second failure)**
   - Proven recovery loop shared with Case 1 (already ported to Adaptive). CAVEAT carried from two readers: it has zero embedded-specific guardrails, so the ported variant must forbid renaming/removing domaincodeEx, the FK field, and the child PK
   - Cites: `backend/agents/prompts.py:100-155`; `backend/pipeline_embedded.py:176-227`; `PHASE0_AUDIT.md:776`

**12. EMBEDDED_REQUIREMENTS_GATHERING and EMBEDDED_FIELD_CREATOR prompt content (JSON output shapes, child-PK rules, dropdown_values rules, PascalCase-with-renames field conventions, .replace-not-.format injection of {QAD_DOCS_CONTEXT} and {ENTITY_MENU})**
   - Both prompts contain ZERO hardcoded old-env identity (confirmed by grep: all 4 com.extensions.customapp hits in prompts.py are inside standalone TS_CODE_WRITER) and neither exists in Adaptive yet - they port nearly verbatim
   - Cites: `backend/agents/prompts.py:391-451`; `backend/agents/prompts.py:453-515`; `backend/agents/prompts.py:259,265,266,326`; `D:/WEB_AUX/adaptive_java_version/backend/agents/prompts.py:38-490 (no EMBEDDED_* present)`

**13. Embedded create-payload shape knowledge: superset of Case 1's entitymetadatas payload with extra top-level keys (lookupBERelations:[], relatedLookups:[], viewResourceInfos stub), isDataExtensionEnable/isDataExtensionOnly true, isBusinessDocument false, viewResourceInfos {isVirtualBE:true, existingForm/existingGridForm 'No', parentEntity 'none', eventHandlerInfos:[]}, per-field extras (modelId seq from 4, suitableDataType via DROPDOWN_BASE_TYPE, overrideContextType 'Domain' only for domaincodeEx, primaryKey 1-based ordinal, isRequired forced for PKs)**
   - This is the only existing capture of what an embedded Entity Builder save looks like on the wire; use as the baseline diff target when re-capturing on the new env
   - Cites: `backend/builders/embedded_builder.py:48-231`; `PHASE0_AUDIT.md:767-769`

**14. Two-step deploy contract: stepA deployCheckForWarnings {entityURI, isInitialDataLoaded:false} then stepB deployBusinessEntity {entityURI, appURI, dataStoreURI, isInitialDataLoaded:false, allowActivityTracking:false}**
   - Same endpoints as the working Case 1 deploy; the only embedded difference is passing dataStoreURI explicitly in stepB. Port with new identity values
   - Cites: `backend/builders/embedded_builder.py:326-341`; `backend/pipeline_embedded.py:294-317`; `PHASE0_AUDIT.md:1396-1397`

**15. concurrencyHash optimistic-locking pattern for UPDATING an existing (parent) event handler: GET eventhandler by 4-tuple (appURI, viewURI, eventHandlerType, appliesTo; camelCase viewURI param), echo concurrencyHash in the POST, verify hash rotation on re-GET**
   - The reusable finding from probe_parent_eh.py is the pattern, not the URNs; this is the entry point for any future parent-view integration work. Note the probe's A/B question (uri in update body or not) is unsettled
   - Cites: `backend/probe_parent_eh.py:24-128`; `PHASE0_AUDIT.md:4530-4536`; `PHASE0_AUDIT.md:4661-4663`

**16. Clean gate seams for the embedded flow: everything before the first entitymetadatas POST is non-mutating; the seven QAD write sites (pipeline_embedded.py:167,205,251,277,299,309,328) are the exact points a human-gated ledger must cover; highest-value single gate is full-spec approval after field design**
   - PHASE0's gate analysis (G1..G5) maps directly onto Adaptive's Case 1 gated-stage pattern and drives the suggested pipeline below
   - Cites: `PHASE0_AUDIT.md:935-944`; `PHASE0_AUDIT.md:4792`

**17. Docs-derived platform vocabulary for Case 2 UI/naming: Relationship Type 'Child', auto-identified Cardinality, Field Mapping with Field/Literal column, extension appears as grid + top-nav tab after child-only deploy (page refresh may be needed), parent never redeployed**
   - Official semantics for stage naming, gate copy, and post-deploy verification expectations in the Adaptive UI
   - Cites: `C3:174-302`; `C3:333-358`; `C3:597-599`

**18. NgData child-collection naming pattern for any future parent-EH work: _<module with dots as underscores>_<BCName>[i].<camelCaseField> (training: _com_extensions_training_CountryExtension[0].knownFor -> new env: _com_yash_digwish_<BCName>)**
   - Documented pattern, mechanically derivable for the new identity; also matches the known camelCase-wire vs PascalCase-field-code split
   - Cites: `C7:506-507`; `C3:2226`

**19. progress_parser.py and lookup_detector.py as environment-neutral modules (no network, no identity, no URLs; source-case preserved verbatim)**
   - Port cleanly IF the owner decides Case 2 should accept .p/.cls input; AUX deliberately gates them out of embedded mode, so this is an option, not a requirement
   - Cites: `backend/core/progress_parser.py:16-22`; `backend/core/lookup_detector.py:37-42`; `backend/routers/client_extensions.py:122-129`

**20. UX behaviors worth keeping from AUX's frontend: mounted-pane state survival, abort-on-new-run, guarded view updates (no yank-back mid-run), triple-fallback summary recovery (state, ref, history refetch)**
   - Resilience patterns independent of environment; the rest of AUX's embedded UX (no gates) is superseded
   - Cites: `D:/WEB_AUX/aux_web_version/frontend/src/features/client_ext/ClientExtPanel.tsx:34-71`; `D:/WEB_AUX/aux_web_version/frontend/src/features/client_ext/ClientExtPanel.tsx:105-162`

## Stale — wrong for the new environment (16)

**1. MODULE='com.extensions.customapp' / appName 'CustomApp' hardcoded across embedded_builder (entity URIs, appURI, field URIs, relation moduleURI/sourceAppName), pipeline_embedded summary, pipeline.py lookup metadata/summary/parent-registration, main.py backfill, view/form/bc builders**
   - New identity is module com.yash.digwish / app digwish; every URN and app reference derived from these literals is wrong by definition
   - Cites: `backend/builders/embedded_builder.py:13,48,124,131,163-164,198,309,316-318`; `backend/pipeline_embedded.py:363`; `backend/pipeline.py:39-44,770,787`; `backend/main.py:146-149`; `backend/builders/view_builder.py:4-6`; `backend/builders/form_builder.py:3-4`

**2. dataStoreURI 'urn:datastore:com.extensions.extension' re-hardcoded in embedded deploy stepB (a diverging copy of deploy_builder's constant)**
   - New datastore is urn:datastore:com.yash.extension; the duplication means a single-constant fix elsewhere would miss it
   - Cites: `backend/builders/embedded_builder.py:337`; `PHASE0_AUDIT.md:797`

**3. Hardcoded '/qad-central/' context root in every URL builder: qad_client (oauth token, api/qracore base), qad_session (OAUTH_PATH, LOGIN_PATH), lookup endpoint chain, sss config**
   - New base https://eeadaptive.yash.com:33005/clouderp has NO /qad-central/ segment anywhere; every wire call the embedded flow makes crosses these literals
   - Cites: `backend/qad_client.py:44,57,65`; `backend/core/qad_session.py:28-29`; `backend/core/lookup_generator.py:70`; `PHASE0_AUDIT.md:1439-1445`

**4. Percent-encoded module literal 'com%2Eextensions%2Ecustomapp' baked directly into two f-strings (per-field uri and deployment_uri) instead of derived from MODULE**
   - Doubly stale: encodes the old identity AND survives any naive find-replace of the plain module string; the port must derive percent-encoding programmatically from the new module (if the scheme is even required - see unknown)
   - Cites: `backend/builders/embedded_builder.py:124,131`; `PHASE0_AUDIT.md:1476,1505`

**5. The 5 builtin parent-registry rows: URIs (urn:be:com.qad.sales.salesorder.ISalesOrderHeader etc.), pk_fields, fk_field codes, all-character fk_type**
   - Hand-transcribed from the OLD environment, never validated live even there; a wrong uri/fk surfaces only as a berelation rejection. Must be re-captured from the new env before seeding Adaptive's registry
   - Cites: `backend/qad_entity_registry.py:37-82`; `PHASE0_AUDIT.md:908-909,1480`

**6. probe_parent_eh.py identity constants: CUSTOM_APP_URI urn:app:com.extensions.customapp, SO_VIEW_URI urn:view:viewmeta:com.qad.erp.sales.SalesOrders, plus its get_token/qad_client dependency**
   - Old-env identities and view assumption; only the GET/POST-with-concurrencyHash pattern carries over (listed portable)
   - Cites: `backend/probe_parent_eh.py:24-25`

**7. Auto-registered custom-parent URI template urn:be:com.extensions.customapp.{bc}.I{bc} and any persisted parent_entities / runs rows in AUX's SQLite**
   - Stale identity baked into both code and DATA; a naive DB copy into the new app would poison the registry
   - Cites: `backend/pipeline.py:787`; `backend/main.py:146-149`; `backend/database.py:33-41`

**8. Embedded flow skipping sql_safe on entityFieldCode while build_data_lists keys field_list_map by sql_safe(code)**
   - Latent bug, not a contract: a reserved-word dropdown field code (e.g. 'status') silently deploys with dataListCode never wired. The port must unify code normalization, not replicate the mismatch
   - Cites: `backend/builders/embedded_builder.py:52,83`; `backend/builders/bc_builder.py:144-146`; `PHASE0_AUDIT.md:957-958`

**9. deployCheckForWarnings response discarded (assigned to nothing, never inspected)**
   - Warnings never reach the user; in a human-gated port this is exactly the material a gate should display - replicating the discard would waste the stage
   - Cites: `backend/pipeline_embedded.py:294-303`; `PHASE0_AUDIT.md:798`

**10. AUX's zero-gate one-shot embedded UX: LLM picks the parent from a menu with no user confirmation, no spec approval, no dry-run, first submit goes live; frontend hardcodes drifted step labels, cannot render step 8, drops 'warning' SSE events, and offers a .p attach button the backend ignores in embedded mode**
   - Superseded wholesale by Adaptive's Case 1 human-gated, server-driven-manifest pattern; the drifted labels and invisible step 8 are concrete evidence client-side step duplication is the wrong approach
   - Cites: `D:/WEB_AUX/aux_web_version/frontend/src/features/client_ext/components/ProgressPanel.tsx:22-32,64`; `D:/WEB_AUX/aux_web_version/frontend/src/features/client_ext/api.ts:6`; `backend/pipeline_embedded.py:29-41,319-342`; `D:/WEB_AUX/aux_web_version/frontend/src/features/client_ext/ClientExtPanel.tsx:422-439`

**11. MODEL_MATRIX (gpt-4o / gpt-4o-mini via AsyncOpenAI + OPENAI_API_KEY), including embedded step 1 using the expensive 'generation' model where standalone uses 'planning'**
   - LLM provider/model choices are AUX-environment specifics, not part of the QAD contract; the port re-decides them under its own stack
   - Cites: `backend/pipeline.py:136-140`; `backend/pipeline_embedded.py:63,79-82`

**12. Router rate-limit comment 'each run spawns 8 LLM calls'**
   - Factually stale for embedded (2-3 calls); do not copy the comment or size limits from it
   - Cites: `backend/routers/client_extensions.py:118`; `PHASE0_AUDIT.md:961`

**13. lookup_generator's case transforms against its own evidence: fieldSet suffix lowercased, fieldLabel titlecased (reference shows 'mfg-colorcode' verbatim), browseName titlecased from physical table, three-way operator/enum casing inconsistency ('eq' vs 'EQ' vs UI 'equals'; 'LITERAL' vs 'Literal'); plus its old-env reference record (com.extensions.sdapp, 2026-07-28 UI reading)**
   - Wrong-by-evidence transforms on an old-env capture; Adaptive should treat its own new-env captures as authoritative, not this record. (Lookups are out of embedded scope anyway - AUX never runs them for Case 2)
   - Cites: `backend/core/lookup_generator.py:27-53,83-96,125,134,139-156,189-190,229`

**14. viewResourceInfo entityDescription set to bc_pascal instead of the human description (inconsistent with entityMetadata.entityDescription two blocks above)**
   - Copy artifact from a captured payload; decide intentionally in the port rather than replicate
   - Cites: `backend/builders/embedded_builder.py:212 vs 182`

**15. Old-env runtime endpoints and hosts: http://qadee.yash.com:81 (app.log), sss_template envUrl http://qadee.yash.com:22010/qad-central/, training-doc identities com.extensions.training**
   - Reference-only historical values; the /clouderp base path (C6:553-557) is the one docs-confirmed piece that matches the new env
   - Cites: `backend/logs/app.log:131`; `PHASE0_AUDIT.md:1465,4706`; `C6:555`

**16. event_handler_builder's flat single-shape handler (eventHandlerType hardcoded 'BEFORE', target derived from BC name only, no uri/concurrencyHash so create-only) and TS_CODE_WRITER's 4 com.extensions.customapp literals**
   - Case 1 machinery, but recorded insufficient for any Case 2 parent-EH extension (needs selectable Pre/Post timing, parent-view targeting, update capability); if Adaptive's ported TS_CODE_WRITER kept the literals they are stale there too
   - Cites: `PHASE0_AUDIT.md:857-893,4521,4539`; `backend/agents/prompts.py:259,265,266,326`

## Unknown — cannot be settled by reading (18)

Each names the capture, live test, or owner question that settles it. Grouped by settle method
in the Next Actions section.

**U1. The berelation endpoint on the new environment: path (old {base}/qad-central/api/qracore/berelation), viewUri urn:be:com.qad.qra.berelation.IBERelation, and full payload key set - this is the ONE endpoint Case 2 adds over Case 1's already-working set**
   - Settle: Network-tab capture of a Relationship save (Child BC screen > Relationships > New > Save) on eeadaptive.yash.com:33005/clouderp; diff against embedded_builder.py:280-321

**U2. relationID format: does QAD accept any UUID, or is the '8c9676c6-0c12-13a3-f114-' prefix (embedded_builder.py:278) load-bearing? Also whether the client sends relationID at all or the server assigns it**
   - Settle: Same relationship-save capture (see what the UI sends); if absent from the capture, probe POST with a plain uuid4 against a throwaway child BC in the dev datastore

**U3. Whether cardinality is client-sent or server-computed: AUX sends cardinality 'MANYTOONE' explicitly; docs say the system auto-identifies it from key structure (C3:242-244)**
   - Settle: Same relationship-save capture; check if cardinality appears in the request body or only in the response

**U4. Is 'Include Grid on Parent Form' required/meaningful for an Embedded (Many-to-One) extension? Docs contradict themselves (C3:319 auto-grid vs C3:534 checkbox checked); AUX sends isIncludeOnParent:false and it worked on the old env**
   - Settle: Live test on new env: create one embedded extension with the flag false, confirm the grid appears on the parent form after deploy

**U5. Do the 5 builtin parent URNs (urn:be:com.qad.sales.salesorder.ISalesOrderHeader etc.) and their PascalCase pk_fields/fk_field codes exist verbatim on eeadaptive, including the domain-field name the relation maps domaincodeEx onto (registry guesses 'DomainCode')**
   - Settle: Read each parent's entity metadata from the new env (GET entitymetadatas equivalent or the Business Components UI) and re-transcribe the Adaptive registry from that capture; do NOT copy AUX's rows

**U6. Whether the new env requires the percent-encoded IEntityDeployment URI scheme (entityMetadata.uri, entityDeployment.uri, entityTable.uri, per-field uri) and the modelId-from-4 sequence, or derives them server-side (standalone bc_builder omits per-field uri and gets away with it)**
   - Settle: Capture an Entity Builder save of an extension BC (Embedded checkbox checked) on the new env and diff its body against build_embedded_schema_payload output

**U7. Is the 'xx' physical-table-name prefix (initialTableName 'xx'+bc_lower) a platform requirement for extension entities or an old-env convention? (Old lookup evidence shows xx_itemextsd-style names)**
   - Settle: Same Entity Builder capture: see what physical table name the new-env UI generates for an embedded BC

**U8. Q-L: did probe_parent_eh.py ever run, and which eventhandler UPDATE shape does QAD accept (Shape A with uri vs Shape B without), and is concurrencyHash server-rotated on update? PHASE0 flags this the single most valuable answer for parent-EH work; no recorded output exists anywhere**
   - Settle: Owner question first (commissioner's memory); if unanswered, re-run the probe pattern against a throwaway handler on the new env with new-identity URNs

**U9. Does the parent form show the extension grid automatically after BERelation + child deploy on the NEW env (docs say yes, refresh may be needed), i.e. is zero parent-side write the complete Case 2, or is parent event-handler/view work ever required for basic rendering**
   - Settle: End-to-end live test on eeadaptive: deploy one embedded extension against a standard parent, open the parent from the menu, observe grid + top-nav tab

**U10. Does the grid-not-panel MANYTOONE behavior still hold on the new Adaptive environment, and is a ONETOONE panel variant wanted for Case 2 scope**
   - Settle: Same live test for the grid half; owner/product question for whether ONETOONE panels are in scope

**U11. Is AUX's optional step 8 (standalone HYBRID_BROWSE menu view for the embedded child) even valid on the platform? Docs say embedded BCs never appear on the menu and skip View creation; AUX registers one anyway with isEntityVirtual:true**
   - Settle: Owner question (was step 8 ever exercised successfully in AUX?) plus a live attempt on the new env; until settled, keep it a conditional, clearly-flagged stage

**U12. Can an embedded BC carry its own event handlers at all (Form > Event Handlers on an embedded BC), given 'Embedded Business Components cannot be extended' (B1 6.9)**
   - Settle: Open an embedded BC's Form panel on the new env and check whether the Event Handlers grid's New button is present/enabled

**U13. Q-F grid claiming: can a Pre/Post handler module list a gridId already in the parent Primary's ViewGridsToHandleList and both receive grid events? Undocumented everywhere; blocks any parent-EH grid-logic stage**
   - Settle: Cheap live experiment per PHASE0 B1 6.1: register a Post handler claiming an already-claimed grid, console.log in onAutoGridBindData

**U14. Parent selection UX for the Adaptive port: explicit human-gated registry picker vs AUX's LLM-inferred parent_entity_key from free text**
   - Settle: Owner/design decision; Case 1's gated pattern strongly suggests an explicit picker validated against the live env at the stage-1 gate (AUX gives the user zero control and errors only after the fact)

**U15. Should Case 2 accept .p/.cls file input (AUX deliberately gates the Progress parser out of embedded mode; the parser also renders only the FIRST temp-table, while parent+child scenarios naturally have two, and the detector cannot express 'FOR EACH child OF parent' joins)**
   - Settle: Owner question on requirements; if yes, the single-table assumption (progress_parser.py:379-380) and OF-join truncation (lookup_detector.py:480-493) must be reworked, not just ported

**U16. Duplicate-BC-name handling: embedded lacks standalone's fast-fail (_is_duplicate_entity_error); replicate the omission or unify?**
   - Settle: Owner decision; recommend unifying (fast-fail before the gate that approves the spec) - settle by confirming the duplicate-error signature on the new env with one intentional duplicate create

**U17. Does the new env's OAuth token flow match (password grant, credentials as URL query params) and what replaces /qad-central/oauth/token under /clouderp**
   - Settle: Presumed already settled by Adaptive's working Case 1 - confirm from the Adaptive codebase/config rather than AUX; if not settled there, capture the webui login exchange

**U18. Whether an equivalent 'business_component' docs bundle exists for the new env to ground the two embedded prompts ({QAD_DOCS_CONTEXT})**
   - Settle: Inspect Adaptive's docs_loader content/bundles; if absent, decide whether to port AUX's bundle or re-source from the new training docs

## Contradictions between readers (6)

**C1.** SSE event ordering around steps 3/3.5/4: the pipeline_embedded reader says step 4's done event is emitted BEFORE step 3's done event when the first POST succeeds ('event order 4-then-3', pipeline_embedded.py:176-227), while the phase0_audit reader records the sequence as 3:done -> 3:running -> 3:done (step-id collision at pipeline_embedded.py:225,236,262). These may both be partially true (4:done, 3:done, 3:running, 3:done) but the exact emission order must be re-read from pipeline_embedded.py:164-262 before designing Adaptive's stage-event contract.

**C2.** Standalone view for an embedded child: the docs reader says embedded BCs are never menu-accessible and View creation is skipped entirely (C3:319-321, C3:568), while the pipeline readers confirm AUX optionally POSTs a HYBRID_BROWSE menu view for the embedded child in step 8 (pipeline_embedded.py:319-342) and phase0 notes it even sets isEligibleForMenu. Re-read whether step 8 was ever exercised successfully, and treat it as unproven against platform semantics.

**C3.** Relation flags vs docs: docs show 'Include Grid on Parent Form' CHECKED in one embedded-flow screenshot (C3:534) and cardinality as system-identified (C3:242-244), while the embedded_builder/phase0 readers record isIncludeOnParent:false + client-sent cardinality 'MANYTOONE' as the known-working live-tested combination (embedded_builder.py:15-24,280-321). Needs a wire capture before the port picks either.

**C4.** LLM call count: the router reader reports the rate-limit comment 'each run spawns 8 LLM calls' (client_extensions.py:118) as a fact, while the pipeline_embedded and phase0 readers establish embedded makes 2-3 calls (phase0 explicitly calls the comment stale, PHASE0_AUDIT.md:961). Trust 2-3; re-read only if the port copies rate limiting.

**C5.** probe_parent_eh.py framing: the pipeline_embedded reader presents it as 'likely the next piece of embedded work' (in-progress exploration), while the router_and_registry reader concludes it plausibly NEVER ran (untracked, stdout-only, zero references, zero PROGRESS.md mentions, POST-only app.log traffic, and PROGRESS.md still lists concurrencyHash as unconfirmed as of 2026-07-28). Interpretation gap, not fact conflict - but the build plan must not assume the probe's questions were answered (Q-L).

**C6.** Lookup reference-record authority: the parsers reader asserts the Adaptive port 'already has its own class-4 confirmed record' for lookups (with corrected lookupResultFields element keys) based on task history, with no file citation; no other reader corroborates. Verify inside D:/WEB_AUX/adaptive_java_version before letting it supersede AUX's lookup_generator reference docstring.

**Resolution of C6 (same day):** confirmed. Adaptive's `backend/builders/lookup_builder.py` holds
its own settled record: element keys `resultField`/`targetFieldSet` named by QAD's code-571
context paths, and run `a6a9270c9698` (DigOrderTesting) carries a live successful lookup.create.
AUX's `lookup_generator` reference record is superseded for the new environment. C1 is also
non-blocking: Adaptive does not reuse AUX's SSE step contract, so the emission-order quirk only
mattered as evidence that client-side step tables drift.

## Suggested gated pipeline for Case 2

Mirrors Case 1's pattern: server-owned stage manifest, gate before every write, dry-run default,
regeneration free until a live write lands.

### Stage 1 - Requirements & parent selection (gate: user confirms parsed intent AND the parent BC, chosen from a registry-driven picker rather than LLM guess; parent's uri/pk_fields/fk_field validated against the live env at this gate)
**Writes to QAD: no.** Port EMBEDDED_REQUIREMENTS_GATHERING (parent_entity_key, bc_pascal, description, wants_separate_view, child_pk, custom_fields) with {ENTITY_MENU} from a NEW-ENV-recaptured registry. Fixes AUX's biggest UX gap (zero parent control, error-after-the-fact). Optionally run a duplicate-BC-name precheck here so conflicts surface before any write. Cites: prompts.py:391-451, qad_entity_registry.py:114-122, pipeline_embedded.py:69-102.

### Stage 2 - Field spec design (gate: user approves the FULL field spec, with the PK trio domaincodeEx / parent-FK / child-PK visually distinguished from custom fields; dropdown value lists shown)
**Writes to QAD: no.** Port EMBEDDED_FIELD_CREATOR + the deterministic fallback-child-PK guard. This is PHASE0's G1, the highest-value single gate: everything before the first entitymetadatas POST is non-mutating. Cites: prompts.py:453-515, pipeline_embedded.py:112-157, PHASE0_AUDIT.md:935-944.

### Stage 3 - Create embedded BC metadata (gate after: show QAD submitResult; on failure run embedded-aware VALIDATOR_AND_CORRECTOR once and re-gate the corrected spec with the human before retrying)
**Writes to QAD: yes.** POST entitymetadatas (embedded superset payload, new identity/datastore, new base path). Includes the dropdown-wiring sub-step (GET enriched -> patch dataListCode/defaultValue -> POST back) with the sql_safe key mismatch fixed. Auto-fix prompt must be given guardrails forbidding changes to domaincodeEx/FK/child-PK. First irreversible write of the run. Cites: embedded_builder.py:48-231, pipeline_embedded.py:164-262, bc_builder.py:98-144.

### Stage 4 - Relate to parent (gate before: show the exact relation to be created - parent, cardinality, the two field mappings domaincodeEx->domain-field and fk->fk)
**Writes to QAD: yes.** POST berelation: MANYTOONE, relationType child, isEmbedded=false, isUseInBusinessDocument=true (known-working set), relatedEntityURI from the recaptured registry. Payload key set, relationID handling, and cardinality client-vs-server must first be settled by the new-env relationship-save capture (see unknowns). Case 2's only genuinely new endpoint over Case 1. Cites: embedded_builder.py:265-321, pipeline_embedded.py:264-292.

### Stage 5 - Pre-deploy warnings check (gate: DISPLAY the deployCheckForWarnings response and require explicit acknowledgment - do not replicate AUX's silent discard)
**Writes to QAD: no.** POST deployCheckForWarnings (stepA: entityURI, isInitialDataLoaded:false) - a validation call, not a mutation, which makes it the natural material for a human gate. AUX ignores the response entirely (pipeline_embedded.py:294-303); the port inverts that. Cites: embedded_builder.py:330-333, PHASE0_AUDIT.md:798.

### Stage 6 - Deploy (gate before: final confirm showing entityURI, appURI urn:app:com.yash.digwish, dataStoreURI urn:datastore:com.yash.extension, and that the parent will NOT be redeployed)
**Writes to QAD: yes.** POST deployBusinessEntity (stepB with new identity values). Docs confirm child-only deploy suffices and datastore must be in Development mode. Cites: embedded_builder.py:334-340, pipeline_embedded.py:305-317, C3:333-342.

### Stage 7 - Verify & summarize (gate: user confirms the extension grid/tab is visible on the parent; summary shows parent_entity - which AUX computes but never displays - plus PK trio, fields, module from config not literal)
**Writes to QAD: no.** Read back the child entitymetadatas; instruct the user to open the parent and refresh (docs: refresh may be needed, C3:356-358). Deliberately do NOT register the child as a future parent (embedded BCs cannot be extended, C3:493). Persist a run ledger covering all write sites. Cites: pipeline_embedded.py:344-368, SummaryCard.tsx:24-125, PHASE0_AUDIT.md:4792.

### Stage 8 (conditional) - Standalone view registration, only when the user explicitly requested a separate view/menu entry at Stage 1
**Writes to QAD: yes.** AUX's step 8 (viewResourceMetadatas HYBRID_BROWSE via the shared view builder) - but flagged: docs say embedded BCs are never menu-accessible, and AUX's UI never even rendered this step, so there is no evidence it was ever exercised. Gate it behind the unresolved contradiction; consider deferring out of the Case 2 milestone entirely. Cites: pipeline_embedded.py:319-342, view_builder.py:50-181, C3:319-321.

### Stage 9 (conditional, future scope) - Parent event-handler integration (grid/field logic on the parent form)
**Writes to QAD: yes.** NOT part of AUX's shipped embedded flow - only the untracked probe explores it. Blocked on Q-L (update shape A/B, concurrencyHash rotation), Q-F (grid claiming), and B1 6.9 (can embedded BCs carry handlers). Requires the GET-then-POST concurrencyHash update pattern plus Pre/Post timing support the flat Case 1 handler builder cannot express. Recommend excluding from the Case 2 milestone and treating as its own follow-on case once the live probes settle. Cites: probe_parent_eh.py:24-128, PHASE0_AUDIT.md:3400,3545,3553,4661-4663.

## Next actions, in dependency order

### UPDATE 2026-08-12, same day: the captures LANDED and the registry was probed live

The owner hand-created `EmbeddedExmpl2` (embedded under Items) in the eeadaptive UI and captured
the entity save, the berelation save, and both deploy calls — verbatim record and full analysis
in `captures/2026-08-12_embedded_EmbeddedExmpl2.md`. Combined with a read-only live probe of the
five AUX parent URNs, the unknowns table moves as follows:

- **U1, U2, U3, U6 SETTLED; U7 partial; C3 flags contradiction RESOLVED** — see the capture file.
  Highlights: relationID is a plain client UUID (AUX's magic prefix is cargo), cardinality is
  client-sent, NO percent-encoded URI scheme and NO modelId sequence exist on the new env, and
  the domain PK field's NAME is user-chosen (`DomainCodee` worked) — only its role is fixed.
- **U5 SETTLED by live probe.** All five AUX parent URNs are valid on eeadaptive, all
  isQadStandard, domain field is `DomainCode` on every one. But two corrections to AUX's rows:
  **InventoryMaster is `doNotExtend: true` on this environment — it cannot be a parent and must
  not be offered.** And **WorkOrderMaster has THREE PKs** (DomainCode, WorkOrderNumber,
  WorkOrderID): since the captured relation maps EVERY parent PK, AUX's single-fk_field model
  under-maps it. The registry schema needs pk_fields-to-map as a LIST, not one fk_field.
  Live-read PK truth: SalesOrderHeaders(DomainCode, SalesOrderNumber),
  PurchaseOrderHeaders(DomainCode, PurchaseOrderNumber), Items(DomainCode, ItemCode),
  WorkOrderMasters(DomainCode, WorkOrderNumber, WorkOrderID). Note live entityCodes also differ
  from AUX's keys: `Items`, `WorkOrderMasters`, `InventoryMasters`.
- **U4/U9/U10 SETTLED** (owner confirmation, 2026-08-12): the embedded grid IS visible on the
  Items screen after the child-only deploy with `isIncludeOnParent: false`. Zero parent-side
  writes is the complete core flow.
- **Scope decisions (owner, same day):** the standalone view is IN scope as a conditional,
  gated, experimentally-flagged stage (U11's experiment now runs at its first live approval);
  `.p`/`.cls` input is IN scope (parser ported with multi-table support; U15's rework done).

**Captures originally requested (now delivered):**
1. ~~A Relationship save~~ **DONE** — settles U1, U2, U3, C3.
2. ~~An Entity Builder save with the Embedded checkbox~~ **DONE** — settles U6, U7 partial.
3. ~~Parent entity metadata reads~~ **DONE via live probe** — settles U5.

**Owner questions (carried from Phase 0, now blocking different things):**
- Q-L: did `probe_parent_eh.py` ever run? (Blocks only Stage 9 / parent-EH work, NOT core Case 2.)
- U11/U15/U16: was AUX's step 8 ever exercised; should Case 2 accept `.p`/`.cls` input; unify
  duplicate-name fast-fail?
- U14 is recommended answered by design: an explicit human-gated parent picker, not LLM guessing.

**Live tests once the build reaches dry-run (each is one throwaway artifact on the dev datastore):**
- U4/U9/U10: deploy one embedded extension, watch the parent form grow the grid.
- U12: check whether an embedded BC's Form panel offers Event Handlers at all.
- U16: one intentional duplicate create to learn the new env's duplicate-error signature.

**Settled already, no action:** U17 (OAuth under /clouderp — Adaptive's working Case 1 is the
proof) and U18 (Adaptive's docs loader already serves the business_component bundle; verify the
bundle grounds the two EMBEDDED prompts when porting them).

## Scope recommendation

Core Case 2 milestone = Stages 1-7. Stage 8 (standalone view for an embedded child) contradicts
the docs and was never provably exercised in AUX — keep it conditional and flagged, or defer.
Stage 9 (parent event handlers) is a separate follow-on case blocked on Q-L and Q-F probes;
excluding it keeps Case 2 shippable on the strength of one wire capture (the Relationship save).
