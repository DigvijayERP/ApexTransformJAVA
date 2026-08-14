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

## 5. The local build pipeline, PROVEN END TO END (same day)

The owner's existing workspace at
`C:\Users\digvijay.parmar\Desktop\Python_Snake\JAVA_SSS\urn_app_com.yash.digwish` was scaffolded
2026-08-04 but never built: `lib/` empty, no `.java`, `target/` empty. The missing piece was the
dependency jar, which we already had from section 3. Installed it and built, all local, no QAD writes.

### The real `pom.xml` — confirms the brief, corrects one inference

```xml
<groupId>com.yash.digwish</groupId>
<artifactId>digwish-server-side-extension</artifactId>
<version>1.0-SNAPSHOT</version>
<properties><java.version>1.8</java.version></properties>
<dependencies>
  <dependency><groupId>com.yash.digwish</groupId><artifactId>ext-dependencies</artifactId><version>1.0</version></dependency>
  <dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><version>2.12.3</version></dependency>
</dependencies>
<build>
  <finalName>com.yash.digwish-ext-cust</finalName>
  maven-compiler-plugin 3.5.1, source/target 1.8
  maven-jar-plugin 3.3.0, manifestEntries: App-Name=com.yash.digwish, Low-Code-Artifact-Type=extension
</build>
```

**CORRECTION to handoff E.1:** the Maven artifactId is **`<app_name>-server-side-extension`**, not
`<bc>-server-side-extension`. The deck's `training-server-side-extension` was app
`com.extensions.training` whose app name IS `training`, so the n=1 sample was ambiguous and was read
the wrong way. Ours is `digwish-server-side-extension`, and there is no BC named DigWish.

Everything else in the brief is confirmed verbatim: plugin versions, `1.8` target, jackson 2.12.3,
`finalName`, and both manifest entries.

### Commands run

```bash
cp qad-ext-dependencies.jar <workspace>/lib/
mvn install:install-file -Dfile=lib/qad-ext-dependencies.jar \
    -DgroupId=com.yash.digwish -DartifactId=ext-dependencies -Dversion=1.0 -Dpackaging=jar
mvn clean package
```

`.m2/repository/com/yash/digwish/ext-dependencies/1.0/` now holds a real `ext-dependencies-1.0.jar`
(3,201,580 bytes) and `.pom`. ⚠️ Before this, it held ONLY `.lastUpdated` markers from 2026-08-11
pointing at Maven Central: the exact poisoned-cache state of handoff trap I.2, which had to be
cleared first or Maven would serve the cached failure.

### The probe class compiled against the real generated types

`src/main/java/com/yash/digwish/DigSmokeTestValidation.java` extends `DigSmokeTestBaseService`,
overrides `create`/`update`, iterates `getTtDigSmokeTest()`, calls `addValidationError` +
`throwAddedValidationErrors()`. Compiled clean on the first attempt: the javap-derived API surface in
section 4 is accurate.

⚠️ Note `package com.yash.digwish;` — the app package with NO BC segment, while generated types live
in `com.yash.digwish.digsmoketest`. This matches the brief's reference example and is now confirmed
to compile. Handoff E.1 listed this as NOT KNOWN (cropped from the deck).

### Output

```
[INFO] Building jar: …\target\com.yash.digwish-ext-cust.jar
[INFO] BUILD SUCCESS       (13.6 s, mvn exit 0)
```

`jar tf` → `com/yash/digwish/DigSmokeTestValidation.class` plus Maven descriptors. **MANIFEST.MF,
verbatim:**

```
Manifest-Version: 1.0
Created-By: Maven JAR Plugin 3.3.0
Build-Jdk-Spec: 17
App-Name: com.yash.digwish
Low-Code-Artifact-Type: extension
```

Both `App-Name` and `Low-Code-Artifact-Type=extension` confirmed on a real artifact. They were
owner-brief-only and **absent from the class-6 deck entirely**.

**⚠️ This jar was NOT deployed.** Building is local and free; deploying replaces the whole server-side
jar with no validated undeploy, and needs an explicit human gate.

## 6. 🎉 THE DEPLOY CONTRACT, SETTLED LIVE (2026-08-14)

The last unknown on the JEF critical path. Not captured from the plugin: **constructed and sent
directly**, which is a stronger result because it means the app never needs the plugin to deploy.

### Background: the plugin cannot deploy on this machine

The owner ran `QAD Extension: Build and Deploy` twice. `mvn clean package` succeeded both times
(BUILD SUCCESS, jar written), then the plugin failed at the network step:

```
request to https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse/upload-packages
  ?appURI=urn:app:com.yash.digwish failed, reason: socket hang up
```

Non-mutating probes proved the route itself is healthy:

| Method | Result |
|---|---|
| `OPTIONS` | **200**, `allow: POST,OPTIONS` |
| `GET` / `HEAD` | 500 (wrong method) |

So the endpoint exists and accepts POST. `socket hang up` is the plugin's own HTTP layer
(a Node client failing an upload, classically an unanswered `Expect: 100-continue`), **not QAD**.
⚠️ Consequence: on this environment the plugin is unreliable for deploys. Our own client is not.

### The request that worked, verbatim

```
POST https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse/upload-packages
     ?appURI=urn%3Aapp%3Acom.yash.digwish
Authorization: Bearer <token>
Content-Type: multipart/form-data; boundary=<generated>

--<boundary>
Content-Disposition: form-data; name="files"; filename="com.yash.digwish-ext-cust.jar"
Content-Type: application/java-archive

<3,321 bytes of jar>
--<boundary>--
```

### The response

```
HTTP 200
server: nginx
content-length: 0
(empty body)
```

### What this settles

- **The multipart shape is CONFIRMED**: exactly ONE part, form field name `files`, `filename` set
  to the jar's own name, part content type `application/java-archive`. The brief said field name
  `files`; part count, filename and content type were NOT KNOWN and are now known.
- **Success is judged on the HTTP status alone.** The response body is **empty**, `content-length: 0`.
  There is no `submitResult` envelope, confirming the brief's ".ok only" rule and confirming that
  the BC-style `submitResult.success:false` business-error check does NOT apply here.
- **No `Expect: 100-continue` is needed**, and no cookie: Bearer auth is sufficient.
- **The app can deploy without the VS Code plugin at all.** Given the plugin fails on this machine,
  that is not merely a convenience: it is the only working path.

⚠️ Still NOT established: what a REJECTED deploy looks like (a malformed jar, a wrong appURI, a
missing manifest key). Every failure mode remains unobserved, so error handling in the deploy stage
must treat any non-2xx as a failure and surface the raw status and body rather than pattern-match.

## 6a. 🎉 THE EXTENSION FIRES — full chain proven (2026-08-14, 11:50 IST)

The behavioural test, run by the owner in QAD's own UI minutes after the deploy. New DigSmokeTest
record, Test Code `1251jsd`, **Description left blank**, Save:

```
Unable to save
Errors
  Field | Error                   | Error ID
        | Description is required.| JEF20260814…
```

- **`Description is required.`** is the exact literal from `DigSmokeTestValidation.validate()`.
  Nothing else on the platform produces that string; it was written for this test.
- **The Error ID carries the `JEF` prefix** — the Java Extension Framework's own error namespace
  (`DOC:65-66` names JEF as the framework's acronym), date-stamped `20260814`.
- It surfaced in the Web UI **Errors grid with Field / Error / Error ID columns**, exactly the
  presentation the class-6 guide documents at `DOC:871-875`.
- The save was **blocked**: no record was written, which is the validation doing its job rather than
  merely logging.

**This closes the JEF chain end to end: discover → generate → build → deploy → EXECUTE.** Every
stage is now evidenced on this environment, not inferred.

It also retires the last inherited risk. The SSS precedent (handoff I.3) was a rule that deploys
cleanly, reports success, and silently never runs. JEF has no `…WithConfirmation` split (section 4)
and the override demonstrably fires on the UI's ordinary save path. **Overriding `create`/`update`
is sufficient, confirmed behaviourally as well as structurally.**

⚠️ Consequence to remember: `DigSmokeTestValidation` is LIVE on `DigSmokeTest` and will keep
rejecting blank descriptions until a jar without it is deployed. Removing the class and redeploying
*should* erase it (whole-jar replacement) but that rollback is still untested.

## 6b. Standard BC validated, and ROLLBACK PROVEN (2026-08-14, 12:00 IST)

Second deploy: a jar containing **only** `PurchaseOrderRemarksValidation`, targeting
`com.qad.purchasing.purchaseorders.PurchaseOrderHeaderBaseService` — a QAD-shipped coded BC, not one
we generated. `DigSmokeTestValidation` was deliberately left out so the same deploy tested rollback.

### 🔴 CORRECTION: the `…WithConfirmation` split IS real on standard BCs

Section 4 concluded "JEF has no WithConfirmation split". **That is true only of entity-builder BCs.**
`javap` across the jar:

| Base service | `WithConfirmation` methods |
|---|---|
| `PurchaseOrderHeaderBaseService` | **3** (create/update/delete) |
| `SalesOrderHeaderBaseService` | **3** |
| `ItemBaseService` | 0 |
| `DigSmokeTestBaseService` (ours) | 0 |

So the SSS trap (handoff I.3 — "deploys cleanly, silently never fires") **does apply to JEF**, on
coded BCs. Signatures differ too: standard BCs take a bare `DataSet` on create/update, while
generated ones take `InputOutput<DataSet>`; and `fetch`/`exists` carry the extra key argument the
brief described, which generated BCs do not.

`PurchaseOrderRemarksValidation` therefore overrides **all four** save paths. Result, in QAD's UI,
saving a PO with Remarks empty:

```
Unable to save
Errors:  Remarks is required on a Purchase Order.    Error ID: JEF20260814…
```

**Design rule for Case 3, now evidence-backed: read the target `BaseService` with `javap` and
override EVERY save path it exposes. Never assume two.** Had this class been written like the first
one it would have compiled, deployed, returned 200, and never fired.

### 🎉 ROLLBACK WORKS — the last unknown in the handoff

Same deploy, same moment: a DigSmokeTest record (`456tyu`) with a **blank Description** now
**SAVES**. The previously-live `DigSmokeTestValidation` is gone because it was absent from the new
jar.

**Whole-jar replacement is confirmed in both directions**: uploading a jar installs what it contains
and REMOVES what it does not. Handoff I.4 listed rollback as "untested, nothing may depend on it";
it is now tested and dependable.

⚠️ The flip side is the sharpest hazard in Case 3: **deploying a jar built from an incomplete
workspace silently erases every extension not in it** — no warning, no error, 200 either way. The
deploy gate must therefore list every class that WILL exist after the deploy, and loudly flag any
class present in the last deploy but missing from this one.

### Incidental confirmation for Case 2

The Purchase Orders screen shows a **`DigPoInspection` tab** beside Main / Order Lines / Receiving /
Billing / Totals / Notes — the embedded child from Case 2, rendering on a standard QAD parent.

## 7. What is still unknown after this probe

Unchanged from the handoff, because none of it is readable:

- **The deploy multipart shape** (part count, filenames, content types). Still the single biggest
  unknown on the critical path. Only a capture of the plugin's "Build and Deploy" settles it.
- **Every JEF response body** for the deploy POST.
- **Whether undeploy exists** (handoff finding F1).
- **Whether rollback works.**
- **The extension class's own `package` line** — the brief's example is still the only witness,
  though the jar confirms generated types live in `com.yash.digwish.<bc_lower>`.
