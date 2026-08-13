# JEF live probe + dependency jar inspection (2026-08-13)

Read-only verification of `SERVERSIDE_HANDOFF.md`, run against `eeadaptive` from this project's own
`qad_client`. **No writes.** Every JEF endpoint below is a GET the handoff classifies as a safe read
(section J.1). This file is the evidence the handoff itself asked for: "The first live call proves or
disproves it."

## 1. The environment is NO LONGER BROKEN

The handoff's section I.1 lists four open blockers (HTTP 500s, "Downloading of core libs failed",
BC stuck in `Initial`) and item K.6 makes "is the environment fixed?" a blocker on **all live JEF
work**. It is fixed. All four JEF reads returned HTTP 200:

| Endpoint id | Result |
|---|---|
| `jef.apps.list` | **200**, 15,605 bytes JSON, app list renders |
| `jef.developer_settings` | **200**, `submitResult.success: true`, `activeApp: "YASHApp"`, `envNamespace: "com.yash"` |
| `jef.dependency_jar` | **200**, `content-type: application/java-archive`, **3,201,580 bytes**, PK zip magic, `content-disposition: attachment; filename="qad-ext-dependencies.jar"` |
| `jef.build_api_sources` | **200**, `submitResult.success: true` (previously 500) |

## 2. The URL shape is CONFIRMED (was the handoff's #1 "shaky" item)

`{base_url}/api/qracore/…` with **no `/qad-central/` segment**, exactly as inferred at
`config/environment.json` and `PHASE1_REGISTRY.md:57-68`. Resolved live:

```
GET https://eeadaptive.yash.com:33005/clouderp/api/qracore/browses?browseId=urn%3Abrowse%3Abe%3Acom.qad.qra.app.IApp&pageSize=1000
GET https://eeadaptive.yash.com:33005/clouderp/api/qracore/developersettings/systemDefaultApp
GET https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse?appURI=urn%3Aapp%3Acom.yash.digwish
GET https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse/build-api-sources?appURI=urn%3Aapp%3Acom.yash.digwish
```

Bearer auth from the existing OAuth password grant works unchanged on all four. The registry ids in
`config/endpoints.json` resolve correctly with no edits. Status upgraded from
`BRIEF/jef-contract, confirmed` to **live-verified** for these four.

## 3. The dependency jar, inspected (first time ever on this project)

Saved to scratch (NOT committed, 3.2 MB binary). JDK 17.0.12 and `jar`/`javap` are available locally.

- **2,159 entries**; top-level packages `com/qad/`, `com/yash/`, `META-INF/maven/`.
- **289 `*BaseService` classes** — the whole surface an extension can target.
- **Our app's 8 BCs are all present**: `DigLookupTest`, `DigLookupTest2`, `DigOrderTest`,
  `DigOrderTesting`, `DigSmokeTest`, `DigSoPacking`, `DigTest`, `FirstTest`. Every BC this project
  created through Case 1 and Case 2 has generated Java types waiting for it.
- Standard QAD BCs are present too (`com/qad/base/address/CarrierBaseService`, etc.), so extensions
  can target platform components, not only ours.
- `META-INF/MANIFEST.MF` is absent or empty (`unzip -p` returned nothing).

### Class layout, confirmed

`com/yash/digwish/<bc_lower>/` containing `<BC>BaseService`, `<BC>DataSet`, `<BC>Record`,
`<BC>Service`, `<BC>Adapter`, and a `<BC>MethodRunnerStrategyFactoryProvider` with one nested class
per lifecycle method (`$CreateMethodRunner`, `$UpdateMethodRunner`, `$DeleteMethodRunner`,
`$InitializeMethodRunner`, `$FetchMethodRunner`, `$ExistsMethodRunner`).

⚠️ Embedded children created BEFORE the naming was settled carry a physical-table-named record
(`com/yash/digwish/embeddedexmpl2/XxembeddedRecord.class`), while `DigSoPacking` carries the clean
`DigSoPackingRecord`. Read the actual class name from the jar; do not derive it.

## 4. The API surface, by `javap` — CORRECTS the brief in two places

```
public class com.yash.digwish.digsmoketest.DigSmokeTestBaseService
        extends com.qad.ipc.service.BaseBC
        implements com.yash.digwish.digsmoketest.DigSmokeTestService {
  public void    create(InputOutput<DigSmokeTestDataSet>) throws BCExecutionError;
  public void    update(InputOutput<DigSmokeTestDataSet>) throws BCExecutionError;
  public void    delete(InputOutput<DigSmokeTestDataSet>) throws BCExecutionError;
  public void    initialize(Output<DigSmokeTestDataSet>)  throws BCExecutionError;
  public void    fetch(String, Output<DigSmokeTestDataSet>) throws BCExecutionError;
  public Boolean exists(String) throws BCExecutionError;
  public String  getEntityURI();
}
```

**Correction 1:** `fetch` takes **two** args `(String, Output<DataSet>)`, not the brief's three
`(String, String, Output<...>)`.
**Correction 2:** `exists` takes **one** arg `(String)`, not the brief's two `(String, String)`.
Also present and undocumented in the brief: **`getEntityURI()`**.

**🎉 Correction 3, the important one: there is NO `…WithConfirmation` split.** The handoff's I.3
flags SSS's `createWithConfirmation`/`updateWithConfirmation` trap ("a deployed rule may silently
never fire") as NOT KNOWN for JEF, and tells you to check `javap` before assuming JEF is free of it.
**Checked. JEF is free of it.** Overriding `create` and `update` is sufficient. The single scariest
silent-failure mode in the whole handoff does not apply.

Identical shape on an **embedded** child (`DigSoPackingBaseService`), so embedded and standalone BCs
extend the same way. No embedded-specific concerns.

### `BaseBC` — the real validation API

```
public abstract class com.qad.ipc.service.BaseBC implements com.qad.ipc.service.I_BaseBC {
  protected void addValidationError(String);
  protected void addValidationError(String, String, String, KeyFieldDTO);
  protected void clearValidationErrors();
  protected void throwAddedValidationErrors() throws BCValidationError;
  protected void handleError(Exception, List<BCError>);
  protected void registerMethodRunner(String, MethodRunnerStrategy);
  protected void setMethodRunnerStrategyFactory(MethodRunnerStrategyFactory);
  public    BCRunnerReturn runMethod(CommandArgs);
  public    boolean implementsMethod(String);
  protected org.slf4j.Logger getLogger();
  protected static <T> T castParameter(Object, Class<T>);
}
```

The brief's four validation methods are confirmed exactly. The logger is **slf4j**. Extra methods
the brief omitted: `handleError`, `registerMethodRunner`, `setMethodRunnerStrategyFactory`,
`runMethod`, `implementsMethod`, `castParameter`.

`@Extension` is confirmed as a **marker annotation with no members**
(`public interface com.qad.ipc.service.Extension extends java.lang.annotation.Annotation {}`).

### DataSet and Record

```
public class DigSoPackingDataSet extends com.qad.ipc.dto.UnmappedPropertiesDTO {
  public DigSoPackingRecord[] getTtDigSoPacking();
  public void setTtDigSoPacking(DigSoPackingRecord[]);
}

public class DigSmokeTestRecord extends com.qad.ipc.dto.UnmappedPropertiesDTO {
  public String    getDescription();  public void setDescription(String);
  public String    getStatusCode();   public void setStatusCode(String);
  public String    getTestCode();     public void setTestCode(String);
  public LocalDate getTestDate();     public void setTestDate(LocalDate);
}
```

- Records really are an **array**, not a `List` — confirmed, as the brief said.
- Accessor is `getTt<BC>()` using the BC's PascalCase name (`getTtDigSoPacking`), not the lowercase
  package segment.
- Both extend `com.qad.ipc.dto.UnmappedPropertiesDTO`.
- **Field types map to real Java types**: `character` → `String`, `date` → `java.time.LocalDate`.
- The field list reflects our own SQL-safe renames (`statusCode`, not `status`).

**This settles the `discover` stage design.** A JEF generator can read the exact field list, Java
types, and accessor names for any BC straight out of this jar with `javap`, the same way the SSS
pipeline parsed `.d.ts`. No guessing, no LLM inference for structure.

## 5. What is still unknown after this probe

Unchanged from the handoff, because none of it is readable:

- **The deploy multipart shape** (part count, filenames, content types). Still the single biggest
  unknown on the critical path. Only a capture of the plugin's "Build and Deploy" settles it.
- **Every JEF response body** for the deploy POST.
- **Whether undeploy exists** (handoff finding F1).
- **Whether rollback works.**
- **The extension class's own `package` line** — the brief's example is still the only witness,
  though the jar confirms generated types live in `com.yash.digwish.<bc_lower>`.
