# Captured: embedded BC created by hand in the new environment (2026-08-12)

Owner created `EmbeddedExmpl2` (embedded under Items) through eeadaptive's own UI and captured
four requests off the Network tab. All four returned HTTP 200. Verbatim below, analysis after.
This is the Case 2 equivalent of the lookup Save capture: QAD's own client is the authority.

## 1. Entity Builder save

```
POST https://eeadaptive.yash.com:33005/clouderp/api/qracore/entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD
```

```json
{"entityMetadatas":[{"customData":null,"uri":"urn:be:com.qad.qra.app.IApp:","entityTables":[],"entityRelationships":[],"dataLists":[],"fieldGroups":[],"appURI":"urn:app:com.yash.digwish","disallowedActions":"","disallowedActionsMessage":"","moduleURI":"urn:app:com.yash.digwish","entityCode":"EmbeddedExmpl2","entityDescription":"embedded testing","dataOperation":"","entityURI":"urn:be:com.yash.digwish.EmbeddedExmpl2.IEmbeddedExmpl2","businessComponentStatus":"INITIAL","sharedSetType":"","apiUrl":"","bdocumentCode":"","bdocumentURI":"","bdocumentDescription":"","bdocumentBrowseURI":"","bdocumentLabel":"","secureResourceURI":"urn:be:com.yash.digwish.EmbeddedExmpl2.IEmbeddedExmpl2","registrationCode":null,"isAllowApproval":false,"isBusinessDocument":false,"isFollowable":true,"isDataExtensionOnly":true,"isControlFile":false,"cachedBdocumentURI":"urn:bd:com.yash.digwish.EmbeddedExmpl2.IEmbeddedExmpl2","isQadStandard":false,"isBusinessDocumentCompatible":false,"isUseOptimisticLocking":false,"doNotExtend":false,"doNotExtendReason":"","entityName":"EmbeddedExmpl","scope":"SYSTEM","appName":"DigWish","entityFields":[{"primaryKey":null,"entityFieldCode":"ItemCoat","fieldLabel":"ItemCoat","physicalFieldName":"ItemCoat","isFormula":false,"hasLookup":false,"dataType":"character","maxLength":null,"displayFormat":"","currencyField":"","dataListCode":"","defaultValue":"","fieldGroup":"","minValue":"","maxValue":"","isDescription":false,"associatedField":"","isRequired":false,"isReadOnly":false,"isHidden":false,"isHiddenForUI":false,"isUserDefinedField":false,"isDeployed":false,"isDiscriminator":false,"isFormattedBy":false,"formattedBy":"","hasOverrides":false,"__gridLockedDummyColumn":"","uniqueID":"595544f1-e6de-4fb7-a5ad-e8239eabcfc6","fieldURI":"urn:field:com.yash.digwish.EmbeddedExmpl.IEmbeddedExmpl:xxembedded.ItemCoat"},{"primaryKey":3,"entityFieldCode":"ItemCost","fieldLabel":"Item Cost","physicalFieldName":"ItemCost","isFormula":false,"hasLookup":false,"dataType":"decimal","maxLength":null,"displayFormat":"->>,>>9.99<<<<","currencyField":"","dataListCode":"","defaultValue":null,"fieldGroup":"","minValue":null,"maxValue":null,"isDescription":false,"associatedField":"","isRequired":true,"isReadOnly":false,"isHidden":false,"isHiddenForUI":false,"isUserDefinedField":false,"isDeployed":false,"isDiscriminator":false,"isFormattedBy":false,"formattedBy":"","hasOverrides":false,"__gridLockedDummyColumn":"","uniqueID":"a77eef2b-3ecc-4783-83a6-30f009540bb2","fieldURI":"urn:field:com.yash.digwish.EmbeddedExmpl.IEmbeddedExmpl:xxembedded.ItemCost"},{"primaryKey":2,"entityFieldCode":"ItemCode","fieldLabel":"ItemCode","physicalFieldName":"ItemCode","isFormula":false,"hasLookup":false,"dataType":"character","maxLength":null,"displayFormat":"","currencyField":"","dataListCode":"","defaultValue":"","fieldGroup":"","minValue":"","maxValue":"","isDescription":false,"associatedField":"","isRequired":true,"isReadOnly":false,"isHidden":false,"isHiddenForUI":false,"isUserDefinedField":false,"isDeployed":false,"isDiscriminator":false,"isFormattedBy":false,"formattedBy":"","hasOverrides":false,"__gridLockedDummyColumn":"","uniqueID":"0b5bfa8d-1fc0-4f3d-9d60-990345f6b164","fieldURI":"urn:field:com.yash.digwish.EmbeddedExmpl.IEmbeddedExmpl:xxembedded.ItemCode"},{"primaryKey":1,"entityFieldCode":"DomainCodee","fieldLabel":"DomainCodee","physicalFieldName":"DomainCodee","isFormula":false,"hasLookup":false,"dataType":"character","maxLength":null,"displayFormat":"","currencyField":"","dataListCode":"","defaultValue":"","fieldGroup":"","minValue":"","maxValue":"","isDescription":false,"associatedField":"","isRequired":true,"isReadOnly":false,"isHidden":false,"isHiddenForUI":false,"isUserDefinedField":false,"isDeployed":false,"isDiscriminator":false,"isFormattedBy":false,"formattedBy":"","hasOverrides":false,"__gridLockedDummyColumn":"","uniqueID":"5d0587bb-44ca-4094-bc21-915d1e509bad","fieldURI":"urn:field:com.yash.digwish.EmbeddedExmpl.IEmbeddedExmpl:xxembedded.DomainCodee"}],"isDataExtensionEnable":true,"isFirstDeployed":false,"bcType":"STANDARD","browseSearchOperators":{"date":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS"],"character":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS","CONTAINS","STARTS_WITH","ENDS_WITH"],"datetime":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS"],"int64":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS"],"datetime-tz":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS"],"integer":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS"],"decimal":["EQUALS","GREATER_THAN","GREATER_THAN_EQUALS","IS_NOT_NULL","IS_NULL","LESS_THAN","LESS_THAN_EQUALS","NOT_EQUALS"],"logical":["EQUALS","IS_NOT_NULL","IS_NULL","NOT_EQUALS"]},"allowBeRelations":true}],"lookupBERelations":[],"relatedLookups":[],"javaExtensionsInfo":[],"activityTrackingInfos":[{"activityTracking":false}],"entityDeployments":[{"entityURI":"","dataStoreURI":"","isDeployed":false,"initialDataStoreURI":"","initialTableName":"xxembedded","isInitialDataLoaded":false,"initialFileName":"","isEntityBuilderBased":true,"isImportedFromDB":false,"allowActivityTracking":false,"concurrencyHash":"","dataOperation":"","recordsGenerationPending":false,"generationStarted":false}]}
```

## 2. BERelation save (the endpoint Case 2 adds)

```
POST https://eeadaptive.yash.com:33005/clouderp/api/qracore/berelation?viewUri=urn:be:com.qad.qra.berelation.IBERelation
```

```json
{"supplementaryMessages":[],"BERelations":[{"uri":"urn:be:com.qad.qra.berelation.IBERelation:dd77147f-40a5-ad85-f514-2469f8257959","BERelationFields":[{"sourceFieldCode":"DomainCodee","relatedFieldCode":"DomainCode","isSourceFieldLiteral":false,"sourceFieldLiteral":null},{"sourceFieldCode":"ItemCode","relatedFieldCode":"ItemCode","isSourceFieldLiteral":false,"sourceFieldLiteral":null}],"BERelationFilterConditions":[],"sourceEntityURI":"urn:be:com.yash.digwish.EmbeddedExmpl2.IEmbeddedExmpl2","relationID":"dd77147f-40a5-ad85-f514-2469f8257959","isExtension":true,"moduleURI":"urn:app:com.yash.digwish","sourceEntityCode":"EmbeddedExmpl2","isLookup":false,"relationType":"child","isCascadeDelete":false,"isDrill":false,"isEmbedded":false,"isIncludeOnParent":false,"isParent":false,"isVisualizedAsDropDown":false,"sourceAppName":"DigWish","isCascadeDeleteForBD":true,"relationCode":"EmbeddedExmpl2","relationLabel":"EmbeddedExmpl2","cardinality":"MANYTOONE","relatedEntityCode":"Items","relatedEntityURI":"urn:be:com.qad.base.item.IItem","isUseInBusinessDocument":true}]}
```

## 3. Deploy, two calls to the SAME endpoint

```
POST https://eeadaptive.yash.com:33005/clouderp/api/qracore/deployBusinessEntity
{"entityURI":"urn:be:com.yash.digwish.EmbeddedExmpl2.IEmbeddedExmpl2","isInitialDataLoaded":false}

POST https://eeadaptive.yash.com:33005/clouderp/api/qracore/deployBusinessEntity
{"entityURI":"urn:be:com.yash.digwish.EmbeddedExmpl2.IEmbeddedExmpl2","appURI":"urn:app:com.yash.digwish","dataStoreURI":"urn:datastore:com.yash.extension","isInitialDataLoaded":false,"allowActivityTracking":false}
```

Note: AUX sent the first (minimal) payload shape to `deployCheckForWarnings`, not to
`deployBusinessEntity`. Here BOTH calls hit deployBusinessEntity. [INFERRED] the first is the
dialog's preflight phase reusing the same endpoint; no deployCheckForWarnings call was captured.
Case 1's working deploy DOES use deployCheckForWarnings, so both contracts exist on this env.

## What this settles (numbering from PHASE3_CASE2_DISCOVERY.md)

- **U1 SETTLED.** berelation endpoint confirmed: same path and viewUri as AUX, new base. Full
  payload key set now on record, including keys AUX never sent: `supplementaryMessages`,
  `BERelationFilterConditions`, `isExtension: true`, `isLookup`, `isCascadeDelete`, `isDrill`,
  `isParent`, `isVisualizedAsDropDown`, `isCascadeDeleteForBD: true`, `relationCode`,
  `relationLabel`, `sourceAppName`.
- **U2 SETTLED.** `relationID` is a client-generated standard-shaped UUID; AUX's magic
  `8c9676c6-0c12-13a3-f114-` prefix is NOT load-bearing. The `uri` echoes it:
  `urn:be:com.qad.qra.berelation.IBERelation:<relationID>`.
- **U3 SETTLED.** `cardinality: "MANYTOONE"` is client-sent.
- **C3 (flags contradiction) RESOLVED.** The new env's own UI sends `isEmbedded: false` and
  `isIncludeOnParent: false` for an embedded extension, matching AUX's live-tested set. The docs
  screenshot showing the grid checkbox checked describes a different option combination.
- **U6 SETTLED.** No percent-encoded IEntityDeployment URI scheme and NO `modelId` sequence
  anywhere. AUX's elaborate `com%2Eextensions%2Ecustomapp` uri construction and modelId-from-4
  numbering are old-env artifacts or pure cargo. Top-level `uri` is just
  `urn:be:com.qad.qra.app.IApp:` (trailing colon, generic). Fields carry a client-generated
  `uniqueID` GUID instead.
- **U7 PARTIAL.** The `xx` physical-table prefix survives (`initialTableName: "xxembedded"`),
  but the suffix is not mechanically bc_lower (entityCode EmbeddedExmpl2 → xxembedded), so the
  name is at least partly user-chosen in the UI. Treat prefix as convention, suffix as free.
- **U5 PARTIAL.** Parent `urn:be:com.qad.base.item.IItem` is VALID on the new env with
  `relatedEntityCode: "Items"`, and its domain field really is `DomainCode`. The other four AUX
  parent URNs still need validation.

## New facts no reader predicted

1. **The domain PK field's NAME is user-chosen.** This BC's is `DomainCodee`, not AUX's
   hardcoded `domaincodeEx`. What matters is the ROLE: PK position 1, character, mapped to the
   parent's `DomainCode` in the relation. The port should treat the name as a convention default,
   not a platform constant, and PascalCase it like the other fields.
2. **The child PK can be non-character** (`ItemCost`, decimal, primaryKey 3).
3. **Field codes are PascalCase** on this save (`ItemCode`, `DomainCodee`) with
   `physicalFieldName` equal to the code, and `fieldURI` built from `entityName` (not
   entityCode): `urn:field:com.yash.digwish.EmbeddedExmpl.IEmbeddedExmpl:xxembedded.ItemCode`.
4. **`entityName` and `entityCode` differ** (`EmbeddedExmpl` vs `EmbeddedExmpl2`), and the
   fieldURI/table follow entityName. [INFERRED] the UI keeps a display name separate from the
   uniquified code; the port must not assume they are equal.
5. **`appName` carries display casing** `DigWish` here, while Case 1's working lookup payload
   used `digwish`. Both were accepted by their respective endpoints; flag for consistency
   testing rather than assuming either is canonical.
6. **New top-level member `javaExtensionsInfo: []`** in the entity save, absent from AUX.
7. **One-shot save**: the whole entity (fields included) went in a single entitymetadatas POST
   with `businessComponentStatus: "INITIAL"` — matching Case 1's bc.create endpoint identity.
   No separate metadata.read/write round-trip appears; the dropdown two-pass from AUX may only
   be needed when data lists are involved (none here — no dropdown fields on this BC).
