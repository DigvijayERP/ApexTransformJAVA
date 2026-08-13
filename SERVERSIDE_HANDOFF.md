# SERVER-SIDE / JAVA EXTENSION — HANDOFF

**For:** a Claude session with zero prior context, implementing the server-side milestone of
`adaptive_java_version`.
**Written:** 2026-08-13.
**Author's position:** I audited both repos and the QAD training guides. I have **never run a JEF build
or a JEF deploy**, and neither has this project.

---

## READ THIS BEFORE ANYTHING ELSE

Three facts that determine how you should treat the rest of this document.

**1. No Java/JEF code exists anywhere.** Not in `adaptive_java_version`, not in `aux_web_version`.
`find . -iname "*.java" -o -iname "pom.xml"` returns nothing in either repo. Phase 6 (the SSS→JEF port)
is `⬜ Not started` in `PROGRESS.md:82`. You are starting from zero code. [CONFIRMED]

**2. There are no server-side wire captures.** The project has exactly one capture file,
`captures/2026-08-12_embedded_EmbeddedExmpl2.md`, and it is about the **embedded BC relation**, not the
server side. Nothing in this document's section C for JEF comes from a capture I have seen. [CONFIRMED]

**3. The JEF REST contract in this document is second-hand.** It comes from the project owner's build
brief, which states it was established by decompiling the `qad-java-sse-vscode` 1.0.10 plugin and then
exercised end-to-end against a live sandbox where a hand-written Java validation deployed and worked.
**The owner labels it confirmed. I did not see the decompile or the traffic.** I reproduce it verbatim
and attribute it as owner-confirmed, which is a weaker warrant than a capture you can re-read. Treat it
as the best available and still verify the first live call. [CONFIRMED that the brief says this;
the underlying facts are owner-confirmed, not verified by me]

A corollary that matters: the *older* environment AUX targeted is not the environment you are building
for. Every AUX value in section F is **stale** for `eeadaptive`.

---

# A. WHAT "SERVER SIDE" ACTUALLY MEANS HERE

Four distinct things wear the words "server side" in this project. Conflating them is the single
easiest way to waste a week.

| # | Name | What it is | Language | Status in this project |
|---|---|---|---|---|
| 1 | **JEF — Java Extension Framework** | Maven-based Java project injecting custom logic into the **lifecycle of Business Components** on the server | Java | **The target.** Not started |
| 2 | **SSS — Server-Side Scripting / "Server-Side Rules"** | The older TypeScript mechanism doing the same job: subclass a standard BC, override create/update, register with a ServiceLocator | TypeScript | **Working in AUX.** Explicitly **not ported** — decision 6 of the brief |
| 3 | **Client-side event handlers** | TypeScript running in the **browser**, reacting to UI events (field change, grid events, button click) | TypeScript | Working in both. **Not server side** despite living near it |
| 4 | **Business Services** | NOT KNOWN — see below | — | — |

### Definitions in QAD's own vocabulary

**JEF** — *"The Java Extension Framework is the mechanism that allows a developer to inject custom logic
into the lifecycle of Business Components"* (`Docs/qad_enterprise_platform_class_6_java_extensions_training_guide.pdf.md:39`).
And: *"Java Extension is a Maven-based Java project that contains custom code"* (`DOC:55`). Extensions
*"are separated from the core QAD application and, as a result, are upgrade-safe"* (`DOC:45`), and are
*"supported by platform and coded BCs"* (`DOC:44`). [CONFIRMED]

**The runtime dispatch model**, which is the thing to hold in your head (`DOC:59-69`) [CONFIRMED]:

```
Web UI save  →  Progress BL  →  "Java Extension for this BC exists?"
                                   │ yes
                                   ▼
                    Progress BL triggers the overridden create() in JEF
                                   │
                    your code runs, then calls super.create()
                                   │
                    control returns to Progress BL  →  DB  →  Web UI
```

**Progress BL remains the only component that touches the database.** A Java Extension is an
interception layer Progress BL calls *out to* before doing its own work. `super.<method>()` hands
control back. [CONFIRMED — owner brief, corroborated by `DOC:59-69`]

**This makes SSS and JEF structural siblings** — both are extension layers in front of the same Progress
engine, which is exactly why the AUX SSS pipeline is a usable porting template even though the language
changes completely. [INFERRED, but stated as such in the owner brief]

**SSS** — AUX's own docstring: *"Server-Side Rules (SSS file upload API)"*
(`aux_web_version/backend/core/qad_session.py:7`). Mechanically: a TypeScript class extending the
standard BC's generated class, registered via `ServiceLocator.STATIC_INSTANCE.addService(...)` and
`ScriptsRegistry.registerBCScript(...)`. See section F for the exact shape. [CONFIRMED]

**Business Services** — **NOT KNOWN.** You asked which QAD UI tabs correspond to each capability, naming
"Business Services, Java Extensions, Deployment" as example Business Component tabs. **I have no
evidence about a Business Services tab, and none of the seven training guides I read describes one.** I
am not going to guess what it does. [NOT KNOWN]

### Which QAD UI screens correspond to what

| Capability | UI location | Evidence |
|---|---|---|
| JEF | **No QAD web-UI screen is documented for authoring.** The entire JEF workflow is VS Code palette commands. The only web-UI touchpoints named are the **My Developer Settings** page (for the "VS Code Plugin Connection URL", `DOC:553-557`) and the **Client IDs management page** (`DOC:568-574`) | `DOC:541-826` [CONFIRMED] |
| JEF errors at runtime | Web UI **"Errors"** grid, columns **Field / Error / Error ID** | `DOC:871-875` [CONFIRMED] |
| Client-side event handlers | Business Components → select BC → **Form → Event Handlers** grid → **New** | audit B1 [CONFIRMED] |
| Deployment tab | **NOT KNOWN** as a JEF surface. A BC **Deployment panel** with a `Deploy` button and a Data Store URI exists (audit B4, class 5), but nothing ties it to Java extensions | [NOT KNOWN] |
| SSS | NOT KNOWN — AUX drives it entirely by API; no screen was identified | [NOT KNOWN] |

**Which one this work targets: JEF, exclusively.** The brief's decision 6: *"AUX keeps SSS; Adaptive
uses JEF. Both are retained, in separate applications. Not a toggle."* [CONFIRMED]

---

# B. THE END-TO-END PROCEDURE, IN ORDER

## B.1 JEF — the documented human workflow

From the class-6 guide, which is a **screen-by-screen IDE tutorial, not an API reference**. Every server
interaction is hidden behind a palette command name. [CONFIRMED]

### Once per machine

| # | Step | Local/HTTP | Reversible | Proof of success | Cite |
|---|---|---|---|---|---|
| 1 | Install JDK — OpenLogic, **Version 17, Windows, x64, Package JDK**, MSI | local | yes | — | `DOC:139-158` |
| 2 | Install Maven — download latest binary zip | local | yes | — | `DOC:197-199` |
| 3 | Extract Maven; *"Maven does not require installation. Just extract the archive"*; e.g. `C:\Program Files\Maven\apache-maven-x.x.x` | local | yes | — | `DOC:237-242` |
| 4 | Env vars: verify `JAVA_HOME`; create/edit `MAVEN_HOME`; put `%MAVEN_HOME%\bin` on `Path` | local | yes | — | `DOC:285-334` |
| 5 | Verify: `java -version`, `mvn -version` | local | n/a | version banners print | `DOC:394-398` |
| 6 | Install VS Code | local | yes | — | `DOC:419-424` |
| 7 | Install **"Extension pack for Java"** by Microsoft | local | yes | — | `DOC:438-444` |
| 8 | Get the QAD plugin: download **"Visual Studio Code plugin for Java Extensions"** (a ZIP); extract; **inside the extracted contents extract `data.zip`**; find `qad-java-sse-vscode-x.x.x.vsix` | local | yes | the `.vsix` exists | `DOC:456-462` |
| 9 | Install it: Gear → Extensions → `(...)` → **"Install from VSIX…"**. *"It is recommended to restart Visual Studio Code after the plugin installation."* | local | yes | command appears in palette | `DOC:464-494` |

⚠️ **Restart VS Code fully after any PATH change — not "Reload Window".** The plugin builds its Maven
task as `ShellExecution("mvn", …)` relying on the terminal's cached PATH, and does **not** read
`maven.executable.path` (that setting governs a different extension). [CONFIRMED — owner brief, trap 3]

### Once per app

| # | Step | Local/HTTP | Reversible | Proof of success | Cite |
|---|---|---|---|---|---|
| 10 | Palette (**F1**) → **"QAD Extension: Init app"** | both | the folder is deletable | project structure appears | `DOC:541-543` |
| 11 | Prompt: environment URL, e.g. `https://aldpqjavaext01.environments.qad.com/clouderp`. Found on **My Developer Settings**, field **"VS Code Plugin Connection URL"** | — | — | — | `DOC:553-557` |
| 12 | Prompt: **Client ID** — *"ask about it your environment Administrator"* | — | — | — | `DOC:568-574` |
| 13 | Prompts: user email, then password. *"user should have **Developer role**"* | **HTTP** — the OAuth call | n/a | — | `DOC:582-592` |
| 14 | Prompt: **select the app** from a server-returned list. *"If login was successful, you should see a list of apps"* | **HTTP** — app list | n/a | the list renders | `DOC:602-604` |
| 15 | Result: *"an empty project structure"* — see section D | local | yes | folders + `pom.xml` exist | `DOC:616-618` |
| 16 | Palette → **"QAD Extension: Update app dependency"**. *"Progress will be displayed below in the Terminal."* | **HTTP** — jar download | re-runnable | *"Result … you can find in the list of app dependencies. It will include **services for each BC from the current app**"* | `DOC:628-652` |

⚠️ **Step 16 is where this project is currently blocked on the target environment**: the dependency jar
will not download (*"Downloading of core libs failed"*). See section I. [CONFIRMED — `config/environment.json` health block]

⚠️ **Step 16 is also trap 2**: the plugin reports Maven success without checking the exit code. Verify
against the filesystem. See section I. [CONFIRMED — owner brief]

### Per artifact

| # | Step | Local/HTTP | Reversible | Proof of success | Cite |
|---|---|---|---|---|---|
| 17 | Under `src/main/java`, in the **`training` folder**, add **`Training.java`** (class simple name == BC name) | local | yes | file exists | `DOC:664-666` |
| 18 | *"Copy code from the file, which provided in materials for current class."* — **the canonical source is an external handout not present in the repo** | local | yes | — | `DOC:706-708` |
| 19 | Palette (**F1**) → **"QAD Extension: Build and Deploy"** | local build **then HTTP** | ⚠️ **NO** | see below | `DOC:752-775` |
| 20 | Build internals visible in the terminal: `Executing task in folder urn_app_com.extensions.training: mvn clean package`, artifactId `training-server-side-extension`, `jar:3.3.0:jar`, `Building jar: …target\com.extensions.training-ext-cust.jar`, `BUILD SUCCESS` | local | — | `BUILD SUCCESS` | `DOC:804-816` |
| 21 | Deploy confirmation: *"no errors in the Terminal and the notification about successful deploy of extension"* / *"Extension building and deploying is successfully completed"* | — | — | ⚠️ notification only | `DOC:824-826` |
| 22 | Test: open the screen, **New** → StartDate prefilled; set Capacity 0, save → error *"Capacity is mandatory"*; restore → saves | manual | — | **the only real proof** | `DOC:836-838`, `DOC:878-881` |

**Step 22 is the only trustworthy success signal in the whole sequence.** Step 21 is a notification, and
the plugin is known to emit success notifications without checking exit codes. [INFERRED from trap 2 +
`DOC:824-826`; the reasoning is mine]

### The step ordering that is NOT cosmetic

**Dependencies (16) must precede writing the class (17).** The dependency jar is what *contains*
`<BC>BaseService`, `<BC>DataSet` and `<BC>Record`. Without it there is nothing to extend and nothing to
import. [INFERRED from `DOC:652` — "It will include services for each BC from the current app" — and
from the fact that the example imports `com.extensions.training.training.TrainingDataSet`]

**App dependencies are a server-side choice, not a `pom.xml` choice.** Which module BCs appear in the
jar is set in the **app definition in QAD** (e.g. `urn:app:com.qad.sales`, `urn:app:com.qad.purchasing`,
`urn:app:com.qad.qracore`). Needing another module means amending the app definition and regenerating —
not editing `pom.xml`. [CONFIRMED — owner brief]

## B.2 SSS — AUX's working sequence, as the porting template

Six stages behind `/api/sss/*`, driven one request at a time. This is the shape to port.

| # | Stage | Local/HTTP | Reversible | Proof | Source |
|---|---|---|---|---|---|
| 0 | **scaffold** — create workspace from bundled template at startup, idempotent, never overwrites | local | yes | `scaffold_sss_workspace` returns True | `core/sss_scaffold.py:20-115` |
| 1 | **readiness** — gate every route on `lib/salesgen.d.ts` existing; structured 503 if not | local | n/a | `{ready: true, missing: []}` | `sss/readiness.py:27-56` |
| 2 | **discover** — parse `.d.ts` typedefs to list targetable BCs | local | n/a | non-empty BC list | `sss/discover.py:211-232` |
| 3 | **generate** — LLM writes the validation body only; structure is assembled deterministically | local + LLM | yes | TS returned | `sss/generate.py`, `sss/templates.py` |
| 4 | **HUMAN APPROVAL** — review, edit, Approve / Regenerate / Discard | frontend | yes | user clicks | `routers/sss.py` + frontend |
| 5 | **deploy** — write `.ts`, `npm run compile` (tsc 3.5), then multipart upload | local **then HTTP** | ⚠️ **NO** | `resp.ok` | `routers/sss.py:99-119` |

Note the rollback that **does** exist in SSS and has no JEF equivalent: on compile failure,
`sss_compile.reset_bc(req.bc_name)` deletes the generated `.ts` (`routers/sss.py:110`). That is a *local*
rollback of an uncompiled file — not a deployment rollback. [CONFIRMED]

---

# C. EVERY HTTP ENDPOINT

## C.1 JEF endpoints — owner-confirmed, reproduced verbatim from the build brief

⚠️ **Provenance for all seven: the owner's build brief, established by decompiling
`qad-java-sse-vscode` 1.0.10 and exercised live against a sandbox. NOT captured or verified by me.
`{envUrl}` in the brief's notation ends with a slash.**

| Operation | Call |
|---|---|
| Login | `POST {envUrl}oauth/token?client_id=…&grant_type=password&username=…&password=…` |
| Refresh | `POST {envUrl}oauth/token?client_id=…&grant_type=refresh_token&refresh_token=…` |
| App list | `GET {envUrl}api/qracore/browses?browseId=urn:browse:be:com.qad.qra.app.IApp&pageSize=1000` |
| Dependency jar | `GET {envUrl}api/qracore/sse?appURI={appURI}` — returns `application/java-archive` |
| Deploy | `POST {envUrl}api/qracore/sse/upload-packages?appURI={appURI}` — multipart, form field name `files` |
| Developer settings | `GET {envUrl}api/qracore/developersettings/systemDefaultApp` |
| Regenerate proxies (UI-only, not in the plugin) | `GET {envUrl}api/qracore/sse/build-api-sources?appURI={appURI}` |

Rules that go with them, verbatim from the brief [owner-CONFIRMED]:

- Credentials are passed as **query-string parameters**, not a JSON body.
- Non-auth calls use `Authorization: Bearer {access_token}`.
- On `401` the plugin refreshes and retries once; on `403` it reports a permissions failure.
- Deploy success is judged **only** on HTTP response `.ok` — there is **no** `submitResult.success:false`
  business-error envelope as there is in BC creation.
- There is **no undeploy command** in plugin 1.0.10, and **no endpoint was found for listing or reading
  back what is currently deployed.**

### Resolved against the target environment

`base_url` = `https://eeadaptive.yash.com:33005/clouderp` and `context_root` = `""`
(`config/environment.json`), giving:

```
POST  https://eeadaptive.yash.com:33005/clouderp/oauth/token?client_id=…&grant_type=password&username=…&password=…
GET   https://eeadaptive.yash.com:33005/clouderp/api/qracore/browses?browseId=urn:browse:be:com.qad.qra.app.IApp&pageSize=1000
GET   https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse?appURI=urn:app:com.yash.digwish
POST  https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse/upload-packages?appURI=urn:app:com.yash.digwish
GET   https://eeadaptive.yash.com:33005/clouderp/api/qracore/developersettings/systemDefaultApp
GET   https://eeadaptive.yash.com:33005/clouderp/api/qracore/sse/build-api-sources?appURI=urn:app:com.yash.digwish
```

⚠️ **This resolution is [INFERRED], not validated.** No call has been made to `eeadaptive` on any of
these paths. The reasoning: AUX uses `{bare-host}/qad-central/api/qracore/…`; the Adaptive base already
carries its context root `/clouderp`, which occupies the same slot; so no extra prefix. That matches the
brief's `{envUrl}api/qracore/…` form. Recorded at `config/environment.json` `_context_root_note` and
`PHASE1_REGISTRY.md:57-68`. **The first live call proves or disproves it.**

⚠️ **Request payload for the deploy is UNPROVEN in one respect.** Multipart with form field name `files`
is owner-confirmed, but I have **no capture showing how many parts, what filenames, or what content
types** the Java deploy sends. Do not assume it mirrors the SSS three-file upload. [NOT KNOWN]

⚠️ **Response shapes for all seven JEF endpoints: NOT KNOWN.** The brief gives success/failure
*criteria* (`.ok`, 401→refresh, 403→permissions) but no response body. I have never seen one.

### Registry ids already defined

`config/endpoints.json` → `phases.case3_serverside_jef` holds five of these with ids
`jef.apps.list`, `jef.dependency_jar`, `jef.deploy`, `jef.developer_settings`,
`jef.build_api_sources`, each `"source": "BRIEF/jef-contract"`, `"status": "confirmed"`. The two OAuth
entries are under `phases.auth` as `auth.token.password` and `auth.token.refresh`. Code resolves an
endpoint by id via `config.resolve_url()`; **no endpoint literal may appear in application code.**
[CONFIRMED — read the file]

## C.2 The SSS endpoint — recorded, deliberately NOT ported

`config/endpoints.json` → `not_ported.endpoints[0]`, id `sss.deploy`. Reproduced because you will see it
in AUX and should know why it is absent from Adaptive.

Built at `aux_web_version/backend/sss/deploy.py:36-46` — **verbatim**:

```python
def _upload_url() -> str:
    """{QAD_BASE_URL}/qad-central/api/qracore/sss?...  (base = host:port only)."""
    base = (config.qad_base_url() or "").rstrip("/")
    app_uri = appconfig.app_uri()
    filename = f"{appconfig.app_script_name()}dev"
    return (
        f"{base}/qad-central/api/qracore/sss"
        f"?appURI={quote(app_uri, safe='')}"
        f"&filename={quote(filename, safe='')}"
        f"&appSeq=0&fileSeq=3"
    )
```

⚠️ Note this is **four** query parameters — `appURI`, `filename`, `appSeq`, `fileSeq`. An earlier
internal summary of this project recorded only `appSeq` and `fileSeq` and **omitted `filename`**. The
code above is authoritative. [CONFIRMED]

`appSeq=0` and `fileSeq=3` are **unexplained literals** copied from the VS Code extension; nothing in
the AUX repo derives them. The module's own docstring says the upload was kept *"BYTE-FOR-BYTE as the
aux-agent version … because the live deploy path is not yet verified against QAD"*
(`sss/deploy.py:11-13`). [CONFIRMED]

The multipart body, verbatim (`sss/deploy.py:55-72`):

```python
    # multipart: three parts all named "files", matching the extension exactly.
    fields = []
    for p in files:
        ctype = "application/javascript" if p.suffix == ".js" else "application/octet-stream"
        fields.append(("files", (p.name, p.read_bytes(), ctype)))
    enc = MultipartEncoder(fields=fields)

    return requests.post(
        _upload_url(),
        data=enc,
        headers={
            "Content-Type": enc.content_type,
            "Cookie": f"JSESSIONID={session_id}",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip,deflate",
        },
        timeout=600,
    )
```

Three parts, all named `files`: `<script>dev.js` (`application/javascript`), `<script>dev.js.map`
(`application/octet-stream`), `<script>dev.d.ts` (`application/octet-stream`). [CONFIRMED]

## C.3 ⚠️ SSS AND JEF USE DIFFERENT AUTHENTICATION — do not conflate

This is the most easily-missed thing in the whole document.

| Surface | Mechanism | Endpoint | Credential travels as | Response field |
|---|---|---|---|---|
| qracore metadata APIs, **and JEF** | OAuth2 password grant → **Bearer** | `POST {base}/qad-central/oauth/token` | **query params** | `access_token` |
| **SSS file upload only** | Form login → **JSESSIONID cookie** | `POST {base}/qad-central/api/login` | **JSON body** | `sessionId` |

Verbatim from `aux_web_version/backend/core/qad_session.py:27-29`:

```python
# All QAD APIs live under the /qad-central/ context on the base host:port.
OAUTH_PATH = "/qad-central/oauth/token"
LOGIN_PATH = "/qad-central/api/login"
```

The cookie login (`qad_session.py:70-93`) posts `{"username": …, "password": …}` as **JSON** with
`Content-Type: application/json;charset=UTF-8` and reads `.sessionId`. The Bearer call
(`qad_session.py:43-67`) passes `client_id`, `username`, `password`, `grant_type=password` as **params**
and reads `.access_token`. [CONFIRMED — read both]

**For JEF, use the Bearer path.** The brief's JEF contract is unambiguous: `Authorization: Bearer`.
Whether `api/login` even exists on `eeadaptive` is **NOT KNOWN** and irrelevant unless you port SSS,
which you should not.

## C.4 Endpoints relevant to server-side but belonging to other cases

Included because a server-side flow may need them and they are already proven.

| id | Method | Path | Status |
|---|---|---|---|
| `eventhandler.read` | GET | `eventhandler?appURI=&viewURI=&eventHandlerType=&appliesTo=WEB` | **confirmed-in-code-never-executed** |
| `eventhandler.update` | POST | `eventhandler` | **confirmed-in-code-never-executed** — see G/Q-L |

⚠️ **Casing trap, confirmed:** `viewURI` on the `eventhandler` endpoint, but `viewUri` on the entity
endpoints. Recorded in `config/endpoints.json`. [CONFIRMED]

---

# D. THE LOCAL JAVA TOOLCHAIN

## D.1 Versions

| Item | Value | Provenance |
|---|---|---|
| **JDK for the toolchain** | **17** — guide instructs "Version 17, Windows, x64, Package JDK"; verify transcript prints `openjdk version "17.0.18" 2026-01-20` | `DOC:143-158`, `DOC:377-388` [CONFIRMED] |
| **`pom.xml` bytecode target** | **`<java.version>1.8</java.version>`** | owner brief [CONFIRMED] |
| Maven (reference) | `Apache Maven 3.9.12`, home `C:\Program Files\Maven\apache-maven-3.9.12` | `DOC:383-384` [CONFIRMED] |
| Maven minimum version | **NOT KNOWN** — the deck states none | [CONFIRMED absent] |
| `maven-compiler-plugin` | **3.5.1** | owner brief [CONFIRMED] |
| `maven-jar-plugin` | **3.3.0** — corroborated by `jar:3.3.0:jar` in the build log | owner brief + `DOC:807` [CONFIRMED] |
| `jackson-databind` | **`com.fasterxml.jackson.core:jackson-databind:2.12.3`** | owner brief [CONFIRMED] |

🚩 **The guide contradicts itself on Java version.** Prose and the verify transcript say **17**
(`DOC:135,143,158,378-385`); the installer screenshot says **"OpenLogic-OpenJDK JDK with Hotspot
8u432-b06 (x64)"** (`DOC:179-181`) and **both** env-var tables show
`JAVA_HOME = C:\Program Files\OpenLogic\jdk-8.0.432.06-hotspot\` (`DOC:290`, `DOC:312`). The confirmed
POM target of `1.8` aligns with the screenshots. **Resolution: install JDK 17, build a project that
targets 1.8.** That works (17 can target 8), and the deck never shows `pom.xml`, so a reader cannot know
the target level from the deck alone. [CONFIRMED contradiction; the resolution is INFERRED]

The same staleness affects Maven: env-var tables show `apache-maven-3.6.3` (`DOC:291`, `DOC:313`) while
the transcript prints `3.9.12` and a folder listing shows `3.9.9` (`DOC:320`). Same cause — a Java-8-era
deck with newer slides swapped in and screenshots left stale. [CONFIRMED — VERIFICATION_ROUND2 B2 missed-item 2]

## D.2 Build commands — verbatim from the owner brief

```
mvn install:install-file -Dfile=<lib>/qad-ext-dependencies.jar \
  -DgroupId=<fullAppName> -DartifactId=ext-dependencies \
  -Dversion=1.0 -Dpackaging=jar
mvn clean package     # produces target/<fullAppName>-ext-cust.jar
```

[owner-CONFIRMED]. Note `mvn clean package` is independently corroborated verbatim in the deck's
terminal output (`DOC:804`); `mvn install:install-file` and the filename `qad-ext-dependencies.jar`
are **absent from the deck entirely** — they come only from the brief. [CONFIRMED absent from DOC]

⚠️ **You must check exit codes yourself.** See section I, trap 2.

## D.3 Workspace layout — verbatim from the owner brief

```
<appFolder>/
  pom.xml
  src/main/java/<namespace>/
  src/main/resources/
  data/
  lib/
  config/qad-sse.config.json        # envUrl, id, appURI — safe to commit
  config/qad-sse.concurrency.json   # cached tokens — never commit
```

The deck's independent description of the same scaffold (`DOC:616-618`): folders `config`, `data`,
`lib`, `src`, `target`; files `.gitignore`, `pom.xml`; workspace folder named
`urn_app_com.extensions.training`, i.e. **`urn_app_` + full app name**. [CONFIRMED — both sources agree]

**For this project that folder name would be `urn_app_com.yash.digwish`.** [INFERRED from the pattern,
n=1 example]

⚠️ **`config/` and `data/` purposes: the deck never explains them** (`DOC:618` lists them and stops).
The brief says `config/` holds the two JSON files above. What `data/` is for is **NOT KNOWN**.

**What `JEF_WORKSPACE_DIR` should point at:** `<appFolder>` — the directory *containing* `pom.xml`,
`lib/`, `src/`, `config/`. That is the directory `mvn` runs in and the one the plugin calls
`urn_app_<fullAppName>`. [INFERRED from the layout; there is no `JEF_WORKSPACE_DIR` in any code yet —
the name is yours to define]

**Precedent for the analogous SSS setting:** `QAD_APP_DIR=./sss_workspace`, resolved relative to
`backend/` (`aux_web_version/backend/.env.example`), pointing at the folder containing `package.json`,
`tsconfig.json`, `lib/`, `src/`, `dist/`, `node_modules/`. [CONFIRMED]

## D.4 Where dependency jars come from

- **Fetched by:** palette command **"QAD Extension: Update app dependency"** (`DOC:628`), which calls
  `GET {envUrl}api/qracore/sse?appURI={appURI}` returning `application/java-archive` [owner-CONFIRMED].
- **Lands in:** `lib/` — [INFERRED]. The deck shows a `lib` folder (`DOC:618`) but **never says a jar
  lands there**; the brief's `mvn install:install-file -Dfile=<lib>/qad-ext-dependencies.jar` implies it.
- **Installed into the local repo as:** groupId `<fullAppName>`, artifactId `ext-dependencies`,
  version `1.0` [owner-CONFIRMED].
- **Refreshed by:** re-running the same palette command. [INFERRED — the deck implies re-runnability but
  never states it]
- **Contains:** *"services for each BC from the current app"* (`DOC:652`) — i.e. `<BC>BaseService`,
  `<BC>DataSet`, `<BC>Record` per BC, scoped to the app's declared dependencies [CONFIRMED].

⚠️ **Verify installation against the filesystem, not the tool's output.** Real success shows a `.jar`
and a `.pom` under `%USERPROFILE%\.m2\repository\…\ext-dependencies\1.0`. Failure leaves only
`.lastUpdated` markers, **and that folder must be cleared before retrying** — Maven caches the failed
resolution and the next build fails with *"was not found … this failure was cached in the local
repository"*. [CONFIRMED — owner brief, trap 2]

## D.5 What is produced

- **Artifact:** `target/<fullAppName>-ext-cust.jar` — for the example,
  `com.extensions.training-ext-cust.jar` (`DOC:814`); `<finalName><fullAppName>-ext-cust</finalName>`
  in the POM [owner-CONFIRMED].
- **Maven artifactId:** `training-server-side-extension` — i.e. **`<bc>-server-side-extension`**
  (`DOC:807,810,813`) [CONFIRMED for n=1; the pattern is INFERRED].
- **Manifest entries:** `App-Name` and `Low-Code-Artifact-Type=extension` [owner-CONFIRMED; **absent
  from the deck entirely**].
- **Internal structure:** compiled classes from everything under `src/main/java`. **NOT KNOWN** in any
  further detail — I have never seen a `jar tf` listing.

⚠️ **One project, many BCs, one jar.** `mvn clean package` compiles *everything* under `src/main/java`
into one jar and uploads that **entire jar**. Whole-package replacement, not an incremental patch.
[CONFIRMED — owner brief]

## D.6 Generated-sources step

**There is no `generate-sources` Maven phase involved.** The generated types (`<BC>BaseService`,
`<BC>DataSet`, `<BC>Record`) arrive **pre-compiled inside the dependency jar**, produced server-side.
[INFERRED — from `DOC:652` plus the fact that the brief's build has no codegen step]

The server-side generator is reachable at `GET {envUrl}api/qracore/sse/build-api-sources?appURI=…`
("Regenerate proxies"), which the brief marks **UI-only, not in the plugin** [owner-CONFIRMED].
⚠️ **This endpoint currently returns HTTP 500 on the target environment.** See section I.

---

# E. CODE SHAPE OF A SERVER-SIDE ARTIFACT

## E.1 Naming, derived from app identity

For app `urn:app:com.yash.digwish` (`fullAppName` = `com.yash.digwish`, `app_name` = `digwish`):

| Thing | Pattern | This project | Warrant |
|---|---|---|---|
| Workspace folder | `urn_app_<fullAppName>` | `urn_app_com.yash.digwish` | [INFERRED, n=1] |
| Generated types package | `<fullAppName>.<bc_lower>` | `com.yash.digwish.<bc_lower>` | `DOC:711-712` [CONFIRMED for n=1] |
| Extension class package | **NOT KNOWN** — the `package` line is cropped out of both listings | — | [CONFIRMED absent] |
| Class file / simple name | `<BC>.java`, in folder `<bc_lower>` | `Training.java` in `training/` | `DOC:664-666` [CONFIRMED] |
| Base class | `<BC>BaseService` | `TrainingBaseService` | `DOC:719` [CONFIRMED, n=1] |
| DataSet | `<BC>DataSet` | `TrainingDataSet` | `DOC:711` [CONFIRMED] |
| Record | `<BC>Record` | `TrainingRecord` | `DOC:712` [CONFIRMED] |
| Temp-table accessor | `getTt<BC>()` → `<BC>Record[]` | `getTtTraining()` | `DOC:722` [CONFIRMED] |
| Maven artifactId | `<bc>-server-side-extension` | | `DOC:807` [INFERRED pattern] |
| Output jar | `<fullAppName>-ext-cust.jar` | `com.yash.digwish-ext-cust.jar` | `DOC:814` [CONFIRMED] |

⚠️ **The extension class's own package is genuinely unknown.** Both code listings in the deck begin at
**source line 6**, so the `package` statement and imports 1–5 are cropped (`DOC:711` gutter shows "6").
The reference implementation in the brief declares `package com.extensions.digtest;` — i.e. the app
package **without** a BC segment, while generated types sit in `…digtest.training`. That is the best
evidence available. [CONFIRMED that the brief's example does this; that it is *required* is INFERRED]

## E.2 The API surface — verbatim from the owner brief, verified with `javap` against the real jar

```java
// com.qad.ipc.service.Extension — marker annotation, no members
// com.qad.ipc.service.BaseBC — parent of every <BC>BaseService
protected void addValidationError(String);
protected void addValidationError(String, String, String, KeyFieldDTO);
protected void clearValidationErrors();
protected void throwAddedValidationErrors() throws BCValidationError;
protected Logger getLogger();
// com.qad.ipc.dto.BCValidationError extends BCExecutionError
//   ^ this is why an override declared `throws BCExecutionError` compiles
// com.qad.ipc.dto.InputOutput<T> extends Output<T> extends ParameterHolder<T>
public T getValue();
public void setValue(T);
```

Per-BC lifecycle methods available to override, verbatim from the brief:

```java
void create(InputOutput<XxxDataSet>)  throws BCExecutionError;
void update(InputOutput<XxxDataSet>)  throws BCExecutionError;
void delete(InputOutput<XxxDataSet>)  throws BCExecutionError;
void initialize(Output<XxxDataSet>)   throws BCExecutionError;
void fetch(String, String, Output<XxxDataSet>) throws BCExecutionError;
Boolean exists(String, String)        throws BCExecutionError;
```

[owner-CONFIRMED via `javap`]

⚠️ **The deck documents only three of the six.** `delete`, `fetch` and `exists` never appear as
lifecycle hooks anywhere in it — so an LLM grounded only on the deck will not know they exist.
[CONFIRMED — audit B2 §2, corrected by VERIFICATION_ROUND2 B2 flag 2 to "never as a lifecycle hook";
the bare words do occur in unrelated prose]

⚠️ **`DataSet` exposes records as an ARRAY**, using the ABL temp-table naming convention carried into
Java — `TrainingDataSet.getTtTraining()` returns `TrainingRecord[]`. Not a `List`. [owner-CONFIRMED,
corroborated at `DOC:722`]

⚠️ **The deck's example indexes `[0]` only** (`DOC:722`, `DOC:742`). Copying that yields
single-row-only code. Iterate the array and null-guard. [INFERRED — but the reference implementation
below does exactly this, so it is the owner's practice too]

## E.3 The complete minimal working example

**Verbatim from the owner brief. This was deployed and confirmed working on both reject and accept
paths against a live sandbox.** This is the single most valuable artifact in section E — it is the only
Java that is known to have compiled, deployed and executed.

```java
package com.extensions.digtest;

import com.extensions.digtest.training.TrainingBaseService;
import com.extensions.digtest.training.TrainingDataSet;
import com.extensions.digtest.training.TrainingRecord;
import com.qad.ipc.dto.InputOutput;
import com.qad.ipc.dto.BCExecutionError;
import com.qad.ipc.service.Extension;

@Extension
public class TrainingCapacityValidation extends TrainingBaseService {

    @Override
    public void create(InputOutput<TrainingDataSet> io) throws BCExecutionError {
        validateCapacity(io.getValue());
        super.create(io);
    }

    @Override
    public void update(InputOutput<TrainingDataSet> io) throws BCExecutionError {
        validateCapacity(io.getValue());
        super.update(io);
    }

    private void validateCapacity(TrainingDataSet dataSet) throws BCExecutionError {
        TrainingRecord[] records = dataSet.getTtTraining();
        if (records != null) {
            for (TrainingRecord record : records) {
                Integer capacity = record.getCapacity();
                if (capacity == null || capacity <= 0) {
                    addValidationError("Capacity must be greater than 0.");
                }
            }
        }
        throwAddedValidationErrors();
    }
}
```

Note what this example establishes that the deck does not: the `package` line, the `Extension` import
(`com.qad.ipc.service.Extension`), the class name **differing from the BC name**
(`TrainingCapacityValidation` extends `TrainingBaseService`), array iteration rather than `[0]`, and
`addValidationError` called **unqualified** rather than `this.`-qualified.

The deck's own (truncated, differently-shaped) example for comparison — `initialize` sets a default,
`create`/`update` validate. Ordering observed there: `initialize` calls `super` **first** then mutates;
`create`/`update` validate → `throwAddedValidationErrors()` → **then** `super`. (`DOC:721-738`)
[CONFIRMED from the listing; that the ordering is *mandatory* is INFERRED]

## E.4 How the class binds to a BC

**By inheritance alone, plus the `@Extension` marker.** There is no registration file, no XML, no
declarative config, no rules engine. Subclass the BC's `<BC>BaseService`, annotate `@Extension`,
override lifecycle methods, always call `super.<method>()`. Progress BL resolves the extension at
runtime by asking *"Java Extension for this BC exists?"* (`DOC:63`). [CONFIRMED — owner brief +
`DOC:59-69`]

**Contrast with SSS**, which *does* require explicit registration (see F.5): two calls to
`ServiceLocator.STATIC_INSTANCE.addService(...)` and `ScriptsRegistry.registerBCScript(...)`. **JEF
drops this entirely.** Do not port the registration concept. [CONFIRMED]

## E.5 Timing options

**JEF has none.** There is no Pre/Post/Primary concept for Java extensions anywhere in the deck or the
brief. Timing belongs to **client-side event handlers**, which are a different mechanism. [CONFIRMED
by absence — whole-file read of the deck]

For completeness, since the words recur in this project — the **client-side event handler** timings and
their exact wire values:

| UI label | DB / wire value | Meaning |
|---|---|---|
| `Primary` | `PRIMARY` | primary handler for the BC; platform BCs only |
| `Pre` | **`BEFORE`** | runs before the existing application code |
| `Post` | **`AFTER`** | runs after the existing application code |

[CONFIRMED — audit B1, from `Form Builder - Event Handlers.txt:100-103` and corroborated by the runtime
artefact naming `com_extensions_oneforce_TIMING.ts` where *"Timing can be BEFORE, AFTER, or PRIMARY"*]

AUX hardcodes `"eventHandlerType": "BEFORE"` at
`aux_web_version/backend/builders/event_handler_builder.py:30`. [CONFIRMED]

## E.6 Multiple extensions per BC

The deck lists *"creating multiple extensions for the same Business Component"* as a supported
capability (`DOC:97`), and states **no ordering, precedence or chaining rules** (`DOC:97`, nothing
further). [CONFIRMED]

⚠️ **The owner's standing rule contradicts the deck and wins: one extension class per BC**, with
multiple checks inside one method, until two-subclasses-per-BC resolution is actually tested. Java
permits two subclasses of the same `BaseService`; what QAD's runtime does when resolving "the
extension" is **untested**. [CONFIRMED — owner brief, "Also unvalidated"]

---

# F. AUX'S EXISTING IMPLEMENTATION

**Everything in this section is TypeScript SSS, not Java.** It is the porting template for *pipeline
shape*, and a source of stale values to avoid.

## F.1 `core/sss_scaffold.py` — 115 lines

Auto-creates the workspace at startup. `scaffold_sss_workspace(app_dir) -> bool`, **idempotent**,
**never overwrites existing files** (`:21-25`). Creates `lib/`, `src/`, `dist/`; copies `package.json`,
`tsconfig.json`, `qad-sss.config.json` from `sss_template/` only if absent (`:34-39`); copies `*.d.ts`
into `lib/` (`:41-47`); installs TypeScript from a bundled copy into `node_modules/typescript` and
writes a `.bin/tsc.cmd` shim on Windows (`:49-72`), falling back to `npm install` (`:74-93`).

Ends with a **drift check worth porting**: it compares `tsconfig.json`'s `outFile` against
`f"dist/{appconfig.app_script_name()}dev.js"` and warns *"SSS deploy may fail if QAD_APP_URI changed"*
(`:95-112`). That is a real class of bug — identity changes, build output name doesn't follow.
[CONFIRMED — read in full]

**Works.** **Stale:** the whole thing is TypeScript-specific.

## F.2 `core/ts_compiler.py` — 119 lines

A **real `tsc` syntax gate** used by the *client-extension* pipeline, not by SSS. Returns
`(ok, diagnostics)`. Fails only on **TS1xxx** (syntax) and deliberately tolerates **TS2xxx** (type)
errors, because the generated code references QAD-side types that only exist at deploy time (`:38-42`).
Prefers the SSS-installed `tsc` for version match, falls back to `shutil.which("tsc")` (`:46-56`).
**Fail-soft**: if no `tsc` is reachable it returns `ok=True` with a warning (`:69-71`).

Exact invocation (`:84-99`):

```
tsc <file> --noEmit --target ES5 --module none --strict false --skipLibCheck --pretty false
```

**The JEF analogue is `mvn compile` / `mvn clean package`.** The design lesson to carry across: a
*syntax* gate that tolerates unresolvable platform types. ⚠️ **That distinction may not survive the port
— `javac` has no equivalent of "syntax errors only"**, and unresolved imports are hard errors. If the
dependency jar is installed, everything resolves and the distinction is moot; if it is not, nothing
compiles at all. [INFERRED — worth deciding early]

## F.3 `routers/sss.py` — 136 lines

`APIRouter(prefix="/api/sss")`. Five routes: `GET /bcs`, `GET /bcs/{name}`, `POST /generate`,
`POST /deploy`, `GET /connection`. All but `/connection` carry `dependencies=GATED` where
`GATED = [Depends(ensure_ready)]` — a **readiness** gate, **not auth** (`:38`). `/generate` is
rate-limited `10/minute` (`:84`). Body caps: `_MAX_PROMPT_CHARS = 20_000`, `_MAX_TS_CHARS = 200_000`
(`:20-21`).

**The deploy route is the shape to port** (`:99-119`): write `.ts` → compile → **on CompileError, roll
back the `.ts`** via `reset_bc` and return 422 → then deploy → on DeployError return 502.

⚠️ **No authentication on any route.** [CONFIRMED]

## F.4 `sss/discover.py` — 239 lines

Parses `.d.ts` typedefs from `lib/` by regex + brace matching. **Scope is hardcoded to two standard
modules** (`:31-34`):

```python
STANDARD_SOURCES: list[tuple[str, str]] = [
    ("salesgen", "Sales"),
    ("purchasinggen", "Purchasing"),
]
```

Custom-app BCs (`lib/{app}gen.d.ts`) are **deliberately not parsed** (`:11-13`). Resolves the chain
`<Data> → ds<Y> → <Y>DataSet → tt<Z> → <Z>Record → fields` (`:118-148`) and caches on
`(path, mtime)` (`:45-46`).

**This is the closest existing analogue to JEF's `discover` stage** — but the mechanism is completely
different. SSS reads **text** `.d.ts` files. JEF must read **compiled classes from a jar**. Per the
brief's mapping table: *"discover — reads generated `BaseService` / `DataSet` / `Record` classes from
the dependency jar"*. Expect to use `jar tf` / `javap` or a bytecode reader; **none of that exists
anywhere in either repo.** [CONFIRMED]

## F.5 `sss/templates.py` — 116 lines — the code-shape generator

**The single most instructive file for the port.** Read it in full before designing the Java generator.
Its core insight: **the LLM produces only the validation body; every structural element is generated
deterministically so the output always compiles.**

Verbatim docstring (`:6-8`): *"The LLM only produces the validation body (and which logical operations
to guard: create / update). Everything structural — references, namespace, the class extending the
STANDARD BC, factory, service registration — is generated here so the output always compiles and
matches QAD's canonical SSS shape."*

Two hard-won facts encoded in it (`:9-17`):

1. The parent class lives in the **BC's own QAD namespace**
   (e.g. `com.qad.sales.salesorder.gen.bc.SalesOrderHeaders`), while the subclass lives in the
   **extension app's dev namespace** (`com.extensions.customapp.dev`) — *"extend standard, deploy into
   customapp"*.
2. ⚠️ *"the QAD Web UI usually saves through **createWithConfirmation / updateWithConfirmation**, NOT
   plain create/update — so for each guarded operation we override BOTH variants (when the BC has them)
   and register them all. **Otherwise a deployed rule may silently never fire.**"*

**Fact 2 is a silent-half-works trap and the most important thing in this file.** Whether JEF has an
equivalent `…WithConfirmation` split is **NOT KNOWN** — the brief's six lifecycle methods show no such
variants, and the deck shows none. **Check `javap` output on a real `<BC>BaseService` before assuming
JEF is free of it.** [CONFIRMED for SSS; NOT KNOWN for JEF]

The emitted template (`:84-116`), verbatim:

```
/// <reference path="{_REF}lib/p2js.d.ts" />
/// <reference path="{_REF}lib/api.d.ts" />
/// <reference path="{_REF}lib/{source}.d.ts" />

namespace {app_ns}.dev {
    import {name}DTO = {parent_ns}.gen.dto.{dto};
    import ServiceLocator = com.qad.tsfoundation.service.ServiceLocator;

    export class {name} extends {parent_ns}.gen.bc.{name} {

{overrides_src}

        private validateRecords(dsEntity: {name}DTO): void {
            const rows = dsEntity.{ds_prop}.{tt_prop} || [];
            for (const rec of rows) {
{indented}
            }
            this.throwAddedValidationErrors();
        }
    }

    export class {name}Factory extends {parent_ns}.gen.bc.{name}Factory {
        public getInstance(): {name} {
            return new {name}();
        }
    }

    ServiceLocator.STATIC_INSTANCE.addService({name}.ENTITY_URI, new {name}Factory());
    com.qad.p2js.bcscriptrunner.ScriptsRegistry.registerBCScript({name}.ENTITY_URI, [{registered_src}]);
}
```

`_REF = "../../../../../../"` (`:24`) — six levels up from
`src/com/extensions/{app}/dev/bc/{BC}.ts` to the app root.

Note `this.throwAddedValidationErrors()` — the **same method name as JEF's**. The validation API is
conceptually identical across both. [CONFIRMED]

## F.6 `sss/compile.py` — 130 lines

`write_ts(bc_name, ts)` writes to `_bc_dir()`, which is **hardcoded** (`:29-38`):

```python
    return (
        Path(appconfig.app_dir())
        / "src" / "com" / "extensions" / appconfig.app_script_name() / "dev" / "bc"
    )
```

⚠️ **`"com" / "extensions"` is a hardcoded path segment** — stale for `com.yash.digwish`.

`dist_files()` (`:49-53`) returns exactly three paths: `dist/{script}dev.js`, `.js.map`, `.d.ts`.
`compile_app()` runs **`npm run compile`** (`:97`) and fails if `returncode != 0` **or fewer than three
dist files were produced** (`:101`) — a filesystem check rather than trusting the exit code, which is
the correct instinct and directly applicable to Maven. `_clean_stale_ts` deletes every `.ts` under
`src/` except the one being compiled (`:77-85`).

⚠️ **`_clean_stale_ts` is a one-artifact-at-a-time design.** JEF is the opposite — the jar contains
*everything* under `src/main/java`, and deleting other sources would **silently erase** their deployed
behaviour. **Do not port this function.** [INFERRED from the whole-jar semantics — but the reasoning is
solid and the consequence is severe]

## F.7 `sss/deploy.py` — 115 lines

Covered in C.2. Additional details: retries once on **401** by re-fetching the session cookie
(`:84-87`); `timeout=600`; judges success on `resp.ok` (`:95`) — the same criterion the JEF contract
uses. `check_connection()` (`:108-114`) is a cheap sign-in probe.

## F.8 `sss/appconfig.py` and `sss/readiness.py`

`appconfig.py` derives SSS-shaped values from `core.config`. `app_script_name()` takes the **last
dotted segment** of the app URI (`:25-28`): `urn:app:com.extensions.customapp` → `customapp`. For
`urn:app:com.yash.digwish` that yields `digwish` — which happens to match the owner-supplied
`app_name`. [CONFIRMED; the coincidence is worth noting but should not be relied on]

`readiness.py` gates on **`salesgen.d.ts` only** (`PRIMARY_TYPEDEF`, `:21`) and returns a structured
503 with `error`, `message`, `missing`, `action`, `docs_url` (`:40-49`). Good pattern; port the shape.

## F.9 `sss_template/` and `sss_workspace/`

`sss_template/` is the tracked seed. Contents and **exact stale values**:

`qad-sss.config.json` — **verbatim, entirely stale**:

```json
{
  "envUrl": "http://qadee.yash.com:22010/qad-central/",
  "id": "126758264977",
  "appURI": "urn:app:com.extensions.customapp"
}
```

⚠️ Note `:22010` here versus `QAD_BASE_URL=http://qadee.yash.com:81` in AUX's `.env` — **the committed
config disagrees with the live setting**. Nothing in the Python reads this file; `sss_scaffold.py:34-38`
only copies it. It is inert and misleading. [CONFIRMED]

`package.json` — `"name": "urn_app_com.extensions.customapp"`, `"typescript": "3.5"` devDependency,
`"compile": "tsc -v && tsc"`. `tsconfig.json` — `"target": "es6"`, `"noEmitOnError": true`,
`"declaration": true`, `"rootDir": "src/"`, **`"outFile": "dist/customappdev.js"`** ← stale.
Bundled TypeScript version: **3.5.3**. [CONFIRMED — read all]

`sss_template/lib/` holds seven `.d.ts` totalling ~2.3 MB: `api.d.ts` (12 KB), `basegen.d.ts` (726 KB),
`customappgen.d.ts` (183 KB), `p2js.d.ts` (12 KB), `purchasinggen.d.ts` (335 KB), `qracoregen.d.ts`
(336 KB), `salesgen.d.ts` (713 KB). `sss_workspace/` is the live copy, identical `lib/`. [CONFIRMED]

⚠️ `qracoregen.d.ts` is where the **event-handler record shape** was recovered from — see G/Q-L.

## F.10 `probe_parent_eh.py` — 135 lines, untracked

Not SSS. A standalone probe for the **client-side event handler** update contract. Covered fully in
section G. Relevant here only because it is the one file in AUX that reads anything back from QAD, and
because it is **untracked, uncommitted, and reaches QAD via `qad_client` rather than `httpx`** — which
made it invisible to two separate audit passes. [CONFIRMED]

## F.11 Server-side parts of `pipeline.py` and the builders

**There are none.** `pipeline.py` never imports anything from `sss`; its only overlap is
`from core.ts_compiler import check_typescript_syntax` (`pipeline.py:14`), a shared utility. SSS is a
fully separate flow. [CONFIRMED — audit A3.3]

## F.12 Complete stale-value inventory

Every value below is wrong for `eeadaptive` / `digwish`.

| Stale value | Where | Correct value |
|---|---|---|
| `com.extensions.customapp` | `event_handler_builder.py:3`, `bc_builder.py:4-6`, `form_builder.py:3-4`, `view_builder.py:4-6`, `deploy_builder.py:3-4`, `prompts.py:259,265,266,326`, `sss_template/package.json`, `qad-sss.config.json` | `com.yash.digwish` |
| `urn:datastore:com.extensions.extension` | `deploy_builder.py:3`, re-hardcoded inline at `embedded_builder.py:337` | `urn:datastore:com.yash.extension` |
| `/qad-central/` path segment | `qad_client.py:44,57,65`; `qad_session.py:28,29`; `sss/deploy.py:42` | **empty** — base already ends `/clouderp` |
| `http://qadee.yash.com:81` | AUX `.env` | `https://eeadaptive.yash.com:33005/clouderp` |
| `http://qadee.yash.com:22010/qad-central/` | `sss_template/qad-sss.config.json:2` | n/a — file not ported |
| `"id": "126758264977"` | same file | n/a |
| `"outFile": "dist/customappdev.js"` | `sss_template/tsconfig.json` | n/a — JEF has no tsconfig |
| `"com" / "extensions"` path segments | `sss/compile.py:33-34` | n/a — Java layout differs |
| `salesgen` / `purchasinggen` | `sss/discover.py:31-34` | n/a — JEF reads a jar |
| `eventHandlerType: "BEFORE"` hardcoded | `event_handler_builder.py:30` | parameterise |

⚠️ **The prompt-template case is the dangerous one.** `prompts.py` hardcodes
`com.extensions.customapp` in **four places inside the TypeScript module the model is told to emit**.
Copying those prompts verbatim generates handlers **in AUX's namespace on your app** — silently, and
visible only inside QAD. The Adaptive project already solved this: prompts are templates, `render()`
substitutes identity (including `ComYashDigwish` and `com_yash_digwish` forms), and a test asserts
AUX's namespace never appears in a rendered prompt. **Apply the same discipline to any Java prompt.**
[CONFIRMED — `SESSION_HANDOFF.md:112-116`]

---

# G. THE THREE OPEN QUESTIONS

## G.1 Q-L — was `probe_parent_eh.py` ever run? **UNANSWERED**

**Status: still open.** Listed as blocker #5 in `SESSION_HANDOFF.md:142`. The owner has not answered.

### What the file does

`aux_web_version/backend/probe_parent_eh.py`, 135 lines, **untracked**, created 2026-08-06 14:28:18,
the newest file in `backend/`. Docstring (`:1-8`) verbatim:

```
Update flow probe — confirms whether we can:
  1. GET an existing event handler
  2. POST it back (with concurrencyHash) as an update

Uses the SalesOrders handler we already know exists.
The update is a NO-OP (same TS code returned) — no functional change.
```

Constants (`:24-27`) verbatim:

```python
CUSTOM_APP_URI = "urn:app:com.extensions.customapp"
SO_VIEW_URI    = "urn:view:viewmeta:com.qad.erp.sales.SalesOrders"
EH_TYPE        = "BEFORE"
APPLIES_TO     = "WEB"
```

⚠️ **It targets a QAD-STANDARD parent view** (`com.qad.erp.sales.SalesOrders`) from the custom app —
i.e. it reads back *our own* `BEFORE` handler on a standard parent, not QAD's Primary.

The GET (`:44-51`) verbatim:

```python
    ep = (
        f"eventhandler"
        f"?appURI={_q(CUSTOM_APP_URI)}"
        f"&viewURI={_q(SO_VIEW_URI)}"
        f"&eventHandlerType={EH_TYPE}"
        f"&appliesTo={APPLIES_TO}"
    )
    get_result = await get_qad(ep, token)
```

where `_q = urllib.parse.quote(s, safe="")` (`:30-31`). It unwraps
`get_result["data"]["eventHandlerV2s"][0]` and reads `uri`, `concurrencyHash`, `isActive`,
`typeScriptCode` (`:58-63`).

### The UPDATE contract, and the two payload shapes

**Shape A** (`:74-89`) — verbatim, **11 keys**:

```python
    payload_a = {
        "supplementaryMessages": [],
        "eventHandlerV2s": [{
            "uri":              handler["uri"],             # ← from GET
            "appURI":           CUSTOM_APP_URI,
            "viewURI":          SO_VIEW_URI,
            "eventHandlerType": EH_TYPE,
            "appliesTo":        APPLIES_TO,
            "isActive":         handler["isActive"],
            "concurrencyHash":  handler["concurrencyHash"], # ← from GET
            "typeScriptCode":   handler["typeScriptCode"],  # unchanged
            "javaScriptCode":   handler["javaScriptCode"],  # unchanged
            "mappingCode":      handler.get("mappingCode", ""),
            "disallowedActions": handler.get("disallowedActions", ""),
        }]
    }
```

**Shape B** (`:111-125`) — **9 keys**. It drops **`uri`** *and* **`disallowedActions`**.

⚠️ **The file's own comment is wrong about this.** `:68` says *"Shape B: without 'uri', only
concurrencyHash"*, implying one difference. There are **two**. [CONFIRMED — diffed the two literals]

⚠️ **The shapes are mutually exclusive, not both attempted.** Shape B sits in the `else` at `:109` —
reached **only if Shape A failed**. Step 3, the re-GET hash check, runs **only if Shape A succeeded**
(`:96`). So one execution exercises either A + re-GET, or A + B. Never all three.

### Does the hash rotate? **NOT KNOWN**

The probe was *written to find out* (`:95-107` re-GETs and prints `old hash` / `new hash` /
`changed: {old != new}`). Whether it ever produced that output is unknown.

### Which shape does QAD accept? **NOT KNOWN**

That the file A/B tests two shapes is itself evidence the contract was **unsettled when it was
written**. [INFERRED, but strongly]

### What I established about whether it ran — and the limits of it

Investigated without executing it (it POSTs; no greenlight was given):

| Check | Result |
|---|---|
| `git log --all -- backend/probe_parent_eh.py` | **No trace.** 3 commits exist, all predating it |
| `git ls-files` / `git stash list` | Untracked, never staged, never stashed |
| Writes any file or DB row? | **No.** Imports only `asyncio, json, urllib.parse, sys, os` + `qad_client`. Every output is `print()` to stdout. No `logging`, no `database` import |
| `backend/history.db` | 19 `runs` / 22 `parent_entities` rows; last written **2026-08-06 12:36:48**. The probe writes neither table |
| `backend/logs/app.log` | Last line **2026-08-06 12:36:50** — a startup health check |
| Probe file created | **14:28:18** — 1h51m *after* the last log write. Nothing in `backend/` written since |

**Verdict: no evidence either way, and by construction none would exist.**

⚠️ **One nuance that matters.** `app.log` *does* capture httpx lines — there is a
`POST http://qadee.yash.com:81/qad-central/api/qracore/eventhandler "HTTP/1.1 200 "` at
`app.log:131` (2026-07-13). So a run **through the backend server process** would be visible, and the
timeline rules that out. But the probe is standalone (`if __name__ == "__main__"`, `:133`) and never
imports the app's logging config, so its httpx calls would emit to a handler-less logger and vanish.
**Absence from the log does not mean it never ran.** [CONFIRMED reasoning]

### A finding for Phase 5 nobody has acted on

The probe's `viewURI` is `urn:view:viewmeta:com.qad.erp.sales.SalesOrders`, but AUX's registry row for
`SalesOrderHeaders` in `parent_entities` holds `urn:be:com.qad.sales.salesorder.ISalesOrderHeader` —
**different namespace** (`com.qad.erp.sales` vs `com.qad.sales.salesorder`) **and different URI kind**
(view vs be). So the parent view URI was **not derived from the registry**. There is **no known
BC → parent-view-URI derivation rule.** [CONFIRMED — read both]

### Corroborating platform evidence

`aux_web_version/backend/sss_template/lib/qracoregen.d.ts:2005-2012` declares on `IEventHandlerV2s`:

```ts
fetch(appURI: string, viewURI: string, eventHandlerType: string, appliesTo: string): EventHandlerV2sDTO;
exists(appURI: string, viewURI: string, eventHandlerType: string, appliesTo: string): boolean;
```

and the stored record at `:1971-1985`:

```ts
interface EventHandlerV2Record {
    AppURI: string;  ViewURI: string;  IsActive: boolean;
    EventHandlerType: string;  JavaScriptCode: any;  TypeScriptCode: any;
    MappingCode: any;  Properties: any;  AppliesTo: string;
    ConcurrencyHash: string;  DataOperation: string;
    DisallowedActions: string;  DisallowedActionsMessage: string;
}
```

⚠️ The DTO wraps an **array** (`ttEventHandlerV2: EventHandlerV2Record[]`, `:1969`). An earlier audit
claim that the 4-tuple yields "exactly one row" was **downgraded to [INFERRED]** by verification — it
was deduced from a method signature, not from a stated uniqueness constraint. [CONFIRMED —
VERIFICATION_ROUND2 B1 flag 7]

**`EventHandlerV2sComm.ENTITY_URI` is declared as `static ENTITY_URI: string` with no literal
(`:2019`) — the concrete `urn:be:` value is NOT in the typedef.** But you do not need it: the probe
reaches handlers through the plain `eventhandler` endpoint on the qracore prefix. [CONFIRMED]

## G.2 Q-F — grid claiming. **UNANSWERED, and the question was framed backwards**

**Status: still open.** Blocker #6 in `SESSION_HANDOFF.md:143`. Deferred to live testing.

**The original question:** can a Pre/Post handler module claim a `gridId` already listed in the parent
Primary's `ViewGridsToHandleList`, and do both then receive grid events?

🔴 **Verification found the premise inverted.** `Event handlers API reference.txt:832`:
*"get/set list of view grid handlers that need to be created. **If not set, all view grids will be
handled.**"*

**`ViewGridsToHandleList` is an opt-OUT filter, not an opt-in claim.** A Post module that simply
*omits* the array receives **all** grids by default. The audit presented the array as the only gate,
which materially misframed the risk. [CONFIRMED — VERIFICATION_ROUND2 B1 flag 5]

**Consequence for the experiment: it needs TWO ARMS** — Post-with-explicit-list and
Post-with-no-list. A one-arm test would answer the wrong question. [CONFIRMED — recorded as trap 2 in
`SESSION_HANDOFF.md:231-233`]

**The absence claim itself survived checking**: greps for *"same grid"*, *"multiple handlers"*,
*"two event handlers"*, *"both handlers"*, *"conflict"* across **both** `Docs/` and AUX's `qad_docs/`
confirm **no document anywhere addresses two modules claiming one grid.** [CONFIRMED by an independent
verifier's own greps]

**The experiment, unchanged:** on a BC with an existing Primary handling grid `G`, register a Post
handler that also targets `G`, override `onAutoGridBindData` with a `console.log`, open devtools, see
whether both modules log. Then repeat omitting the list. It writes one event-handler row (deletable) and
needs the owner's environment choice.

**Relevance to the server side: LOW.** Grid claiming is a **client-side** event-handler question. It
does not block JEF. It is in this document only because it was one of the three you asked about.

## G.3 Phase 1 static/dynamic classification — **PROPOSED, AWAITING CONFIRMATION**

**Status: not confirmed by the owner.** Blocker #4 in `SESSION_HANDOFF.md:141`;
`PHASE1_REGISTRY.md:3-5` explicitly says it *"needs your confirmation."*

**What was decided (by me, pending approval):**

**Dynamic — changes per environment:** `base_url`, `app_uri`, `context_root`, `QAD_CLIENT_ID`,
`QAD_USERNAME`, `QAD_PASSWORD`, `OPENAI_API_KEY`.

**Static — identical across every environment:** everything else — all 20 endpoint paths,
`api/qracore`, `oauth/token`, and every `viewUri=urn:be:com.qad.qra.*` query parameter.

**The rule, verbatim from `PHASE1_REGISTRY.md:50-53`:** *"The `urn:be:com.qad.qra.*` URIs name **QAD's
own platform CRUD adapters** — `IEntityBuilderCRUD`, `IViewResourceMetadata`, `IBERelation`, `ILookup`.
They ship with the platform and are the same on every QAD install. Your `urn:app:com.yash.digwish` is
the opposite: it names **your** app, so it's dynamic. That's the whole rule — does this identifier
belong to QAD or to you?"*

**For JEF specifically:** all five JEF endpoint paths are classified **static**; `{app_uri}` inside
their query strings is the dynamic part. The multipart form field name `files`, `grant_type=password`,
the `1.8` bytecode target and the manifest keys are also static. [CONFIRMED — read `endpoints.json`]

**One open sub-decision:** `QAD_CLIENT_ID` placement. It is in `backend/.env` (gitignored), following
AUX. The JEF convention differs — the brief lists `config/qad-sse.config.json`'s `id` as *"safe to
commit"*. Both defensible; flagged for owner override; one line to move.
[CONFIRMED — `PHASE1_REGISTRY.md:75-80`]

---

# H. WIRE CAPTURES

## H.1 ⚠️ There are NO server-side or JEF wire captures. None.

This is the honest answer to the section you called the highest-value item. I would rather say it
plainly than pad it.

- No JEF request or response body has ever been captured by this project.
- No HTTP status code from any JEF endpoint has been observed.
- No `Authorization` header exchange, no multipart body, no error envelope.
- The class-6 guide contains **zero API endpoints, zero URL paths, zero payload keys, zero header
  names** — its only URLs are four download/environment links. [CONFIRMED — whole-file grep, refined by
  VERIFICATION_ROUND2 B2 flag 1]

**Everything in section C for JEF is owner-brief text, not observed traffic.**

## H.2 The one capture that exists — and it is not server-side

`captures/2026-08-12_embedded_EmbeddedExmpl2.md` (11,898 bytes), captured from the **new** environment's
UI on 2026-08-12. It covers the **embedded BC relation** (`berelation`), i.e. Case 2. **Read it directly
— I am not reproducing 12 KB of Case-2 material in a server-side handoff**, but you should know it
exists and what it settled, because two of its findings are generalisable:

- `relationID` is a **plain client-generated UUID**; AUX's hardcoded magic prefix
  `"8c9676c6-0c12-13a3-f114-"` is **NOT load-bearing**. A worked example of an AUX constant that looked
  required and was not.
- `cardinality: MANYTOONE` is client-sent, and `BERelationFields` must map **every** parent PK
  (including the domain field to `DomainCode`).

[CONFIRMED — summarised in `config/endpoints.json` → `relation.create`]

## H.3 A second captured endpoint, recorded in the registry

`lookup.browse_fields` — captured from QAD's Lookup Definitions UI 2026-08-11, then exercised. Verbatim
from `config/endpoints.json`:

```
GET  browses
     ?browseId=urn:browse:custom:lookupBrowseFields
     &page=1
     &pageSize=200
     &pageAction=first
     &filter=browseURI,eq,{browse_uri},literal
```

⚠️ *"`page` and `pageAction=first` are REQUIRED — without them QAD returns 200 with zero rows."*
Returns `[{fieldLabel, field, fieldDataType, browseURI}]` where `field` is the exact value
`ResultField`/`SearchField` must carry — e.g. `digSmokeTest.testCode`, **camelCase entity prefix, NOT
the lowercase segment of the browse URI. Use verbatim.** [CONFIRMED]

**Why a server-side reader should care:** it demonstrates the `browses` endpoint is **generic** —
`browseId` selects which browse to read. The JEF app-list call uses the same endpoint with
`browseId=urn:browse:be:com.qad.qra.app.IApp`. That the pattern holds is now **evidenced**, where
`API_CAPTURES_NEEDED.md:49-59` had it as an inference. [INFERRED → now corroborated]

## H.4 The one log line that is a real observed request

From `aux_web_version/backend/logs/app.log:131`, against the **old** environment:

```
2026-07-13T17:03:01 | INFO    | httpx | HTTP Request: POST http://qadee.yash.com:81/qad-central/api/qracore/eventhandler "HTTP/1.1 200 "
```

URL, method and status only — httpx does not log bodies. [CONFIRMED]

## H.5 What to capture first, when the environment is fixed

In priority order for the server side. Method: open the screen in QAD, F12 → Network, do the action,
copy the request. **Strip the `Authorization` header before sharing.**

| # | Action | Settles |
|---|---|---|
| 1 | VS Code plugin → **"QAD Extension: Update app dependency"**, with a proxy or the plugin's own terminal | The real dependency-jar request/response, and what "Downloading of core libs failed" actually is |
| 2 | Plugin → **"Build and Deploy"** on a throwaway class | **The multipart body shape** — part count, filenames, content types. The single biggest JEF unknown |
| 3 | Same, capture the **response** | The success envelope, if any. The brief says `.ok` only — verify |
| 4 | Plugin → **"QAD Extension: Undeploy"** | Whether it issues an HTTP call at all — settles finding F1 (section I) |
| 5 | Any QAD screen listing deployed extensions, if one exists | Whether read-back is possible at all |

---

# I. FAILURES AND GOTCHAS

## I.1 Live environment failures — currently blocking

| Symptom | Exact text | Cause | Status |
|---|---|---|---|
| Entity-metadata generation | HTTP 500 | Backing service not responding; network team investigating | **Open** |
| `sse/build-api-sources` | HTTP 500 | same | **Open** |
| Dependency jar download | **"Downloading of core libs failed"** | same | **Open** |
| Test BC status | stuck in **`Initial`** | same | **Open** |

[CONFIRMED — `config/environment.json` health block; owner brief "Environment status"]

**Consequence, stated by the owner: the Java deploy path cannot be validated live yet. Build it, keep
dry-run default, and do not report it as done on the basis of dry-run alone.**

**One diagnostic worth trying** (from audit B4, class 4): QAD's UI **Package** action produces an Inbox
notification literally titled *"OS Script Processing: Create app package"* — a UI button demonstrably
dispatches an **OS Script**. If Source File Generation does the same, running the OS Script **directly**
from the OS Scripts screen may surface the script's own error text in the Inbox **instead of the 500
swallowing it**. Class 5 shows OS Scripts named `compile_app_source…` and `create_app_metadat…`
(truncated in the doc). [INFERRED — the single highest-value experiment the docs suggest]

## I.2 The five confirmed traps

**Trap 1 — `qad-sss-vscode` shadows the palette search.** An older TypeScript SSS extension by the same
publisher registers commands under **`QAD SSS:`**. Searching "QAD" surfaces **its** `Init app` first,
which scaffolds a completely different TypeScript project. **Always search `QAD Extension`.**
*Symptom you hit it:* **no `pom.xml`**, and a config file named **`qad-sss.config.json`** instead of
**`qad-sse.config.json`**. [CONFIRMED — owner brief]

**Trap 2 — the plugin reports Maven success without checking the exit code.** `fetchMavenCommand`
resolves as successful whenever the Maven task *finishes*, regardless of outcome. This produced a false
*"Updating the dependencies is successfully completed"* while `mvn install:install-file` had actually
failed; Maven then cached the failed resolution and the next build failed with
**"was not found … this failure was cached in the local repository"**.
**Anything you build must check exit codes itself.** Verify against
`%USERPROFILE%\.m2\repository\…\ext-dependencies\1.0` — real success shows the `.jar` and `.pom`;
failure leaves only `.lastUpdated` markers, **and that folder must be cleared before retrying**.
[CONFIRMED — owner brief; this has already bitten this project]

**Trap 3 — the VS Code integrated terminal caches PATH.** The extension builds its Maven task as
`ShellExecution("mvn", …)` relying on the terminal's PATH. It does **not** read
`maven.executable.path` — that setting governs the separate "Maven for Java" extension. **Fully restart
VS Code (not just Reload Window) after PATH changes.** [CONFIRMED — owner brief]

**Trap 4 — `dotenv_values()` reads a physical file, not `os.environ`.** This breaks Docker `env_file:`
injection. **Bind-mount the `.env` file.** Live in AUX at `core/config.py:73`. [CONFIRMED]

**Trap 5 — absence claims built from HTTP-library greps are wrong.** Two audit sections claimed AUX
never reads back from QAD. It does — `probe_parent_eh.py` reaches QAD via `qad_client`, not `httpx`
directly, so it fell out of three separate inventories and produced one outright-wrong conclusion.
**The correct sweep is `grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py`.**
This defect **recurred** in the section where it mattered most, after being flagged once.
[CONFIRMED — this project's own history]

## I.3 Things that silently half-work

**`createWithConfirmation` / `updateWithConfirmation` (SSS).** *"the QAD Web UI usually saves through
createWithConfirmation / updateWithConfirmation, NOT plain create/update … Otherwise a deployed rule may
**silently never fire**."* (`sss/templates.py:13-17`). A rule that deploys cleanly, reports success, and
does nothing. **Whether JEF has this split is NOT KNOWN — check `javap` before assuming it does not.**
[CONFIRMED for SSS]

**Deploying from an incomplete copy erases everything not in it.** *"no warning, no conflict, no
error."* [CONFIRMED — owner brief]

**`deployCheckForWarnings` response discarded.** AUX calls it and throws the result away — never
assigned, never checked (`pipeline.py:739`). The warnings are the entire point of a deploy gate.
[CONFIRMED]

**A tool reporting success is not evidence.** Verify against the filesystem. [CONFIRMED — trap 2]

## I.4 Things with no undo

| Operation | Undo | Note |
|---|---|---|
| **JEF deploy** | ⚠️ **NONE VALIDATED** | Whole-jar replacement. No undeploy in plugin 1.0.10 per the decompile |
| BC creation | none found | Why the regeneration lock says *"delete it in QAD yourself"* |
| `berelation` create | NOT KNOWN | |
| Event-handler update | NOT KNOWN | `concurrencyHash` implies update-in-place, but the previous code is gone |

🚩 **FINDING F1 — the deck contradicts the decompile on undeploy.** The class-6 guide asserts an
undeploy capability **three times**: the capability list *"undeploying an extension"* (`DOC:81`), the
Command Palette screenshot `QAD Extension: Undeploy urn_app_com.extensions.training` (`DOC:634`), and
the command table (`DOC:761`). The owner's confirmed set — decompile of 1.0.10 plus a live deploy —
says **no undeploy command**. These cannot both be true as stated.

Ranked reconciliations, **all [INFERRED]**: (a) the command is **registered in `package.json` but its
handler is a no-op or local-only cleanup**, so a decompile hunting HTTP calls correctly reports no
undeploy *endpoint* while the UI still shows the command; (b) the deck was authored against a different
plugin version; (c) the command exists and calls an endpoint that was never exercised.

**Action taken: none. Do not emit undeploy tooling. Do not design anything that depends on rollback.**
Confirm by grepping the VSIX `package.json` `contributes.commands` for an undeploy id and tracing its
handler. [CONFIRMED that the conflict exists]

**Rollback is unvalidated.** Removing a class and redeploying *should* erase it, since deploy replaces
the whole jar — **but this has never been tested.** [CONFIRMED — owner brief, "Also unvalidated"]

## I.5 Order-dependent steps

1. **Dependencies before writing the class** (B.1 step 16 before 17) — nothing to extend otherwise.
2. **`mvn install:install-file` before `mvn clean package`** — and **clear `.lastUpdated` markers before
   any retry**, or Maven serves the cached failure.
3. **Compile before deploy** — SSS enforces this explicitly (`deploy.py:51-53`: *"Compiled files
   missing - compile must run first"*).
4. **Validate → `throwAddedValidationErrors()` → then `super`** in `create`/`update`; but
   **`super` first, then mutate** in `initialize`. The order **inverts** between them (`DOC:721-738`).
5. **Restart VS Code after PATH changes**, before running any Maven command (trap 3).
6. **App definition amended server-side before regenerating**, if you need another module's BCs.

## I.6 Error-message reference

| Message | Source | Meaning |
|---|---|---|
| `Downloading of core libs failed` | plugin | Dependency-jar fetch failed. Currently the target environment |
| `was not found … this failure was cached in the local repository` | Maven | A previous `install-file` failed. Clear `.m2/.../ext-dependencies/1.0` |
| `Updating the dependencies is successfully completed` | plugin | ⚠️ **Not proof.** Exit code unchecked |
| `Extension building and deploying is successfully completed` | plugin, `DOC:826` | ⚠️ Notification only |
| `Capacity is mandatory` / Error ID `JEF202606035.` | Web UI Errors grid, `DOC:873-875` | A working validation. `JEF` is the framework's own acronym (`DOC:65-66`) |
| `Compiled files missing - compile must run first: [...]` | `sss/deploy.py:53` | SSS ordering violation |
| HTTP 403 | JEF contract | **Permissions failure** — user needs the **Developer role** (`DOC:592`) |
| HTTP 401 | JEF contract | Token expired — refresh and retry **once** |

---

# J. GATING IMPLICATIONS

The project's rule: *"Nothing writes to QAD without explicit greenlight. Dry-run is the default and must
report exactly what it would send: endpoint, method, headers, payload."* (`SESSION_HANDOFF.md:252-253`)

## J.1 Safe reads — no gate needed

| Operation | Note |
|---|---|
| `GET …/oauth/token` | Auth. Reveals nothing, changes nothing |
| `GET …/api/qracore/browses?browseId=…IApp` | App list |
| `GET …/api/qracore/developersettings/systemDefaultApp` | |
| `GET …/api/qracore/sse?appURI=…` | Downloads the jar. Writes only to local disk |
| `GET eventhandler?…` | The `probe_parent_eh.py` read half |
| Local: `mvn compile`, `javap`, `jar tf`, discovery | No network |

## J.2 Irreversible writes — hard gate, explicit approval, payload shown

| Operation | Why |
|---|---|
| **`POST …/sse/upload-packages`** | ⚠️ **The critical one.** Whole-jar replacement, no undeploy, no validated rollback |
| `POST eventhandler` (update) | Overwrites an existing handler on a **standard parent view**. Q-L |
| `POST entitymetadatas` (create) | BC exists afterwards; no delete path found |
| `POST deployBusinessEntity` | Terminal |

## J.3 What the JEF deploy gate must show

Because there is no read-back endpoint, **the tool cannot diff against the server.** It can only diff
against **its own record of what it last deployed**. Therefore:

1. **Every class that will exist in the jar after this deploy** — the full list, not the diff.
2. ⚠️ **A loud warning for any class present in the previously-deployed jar but ABSENT from this one** —
   that class is about to be silently erased.
3. The resolved URL, method, and multipart part list.
4. The `mvn` exit code and the verified presence of `target/<fullAppName>-ext-cust.jar` on disk.

**This requires Adaptive to persist a deploy manifest per app.** Build it before the first live deploy,
not after. [INFERRED — but it follows directly from "no read-back" + "whole-jar replacement"]

## J.4 What can be meaningfully dry-run

| Step | Meaningful dry run? |
|---|---|
| Auth | Partially — can verify credentials resolve without calling |
| Dependency fetch | ✅ Yes — report URL; skip the download |
| Class generation | ✅ **Fully.** Pure local |
| `mvn clean package` | ✅ **Fully, and this is the highest-value rehearsal available** — it proves the code compiles and produces the jar, with no QAD contact |
| Deploy | ⚠️ **Partially — see below** |

## J.5 ⚠️ What CANNOT be meaningfully dry-run

**The JEF deploy.** A dry run can report the URL, the multipart part list and the jar's contents. It
**cannot** tell you:

- whether QAD **accepts** the multipart shape (the part count/filenames/content-types are **NOT KNOWN**
  — no capture);
- whether the deploy **succeeds**, since success is judged only on HTTP `.ok`, which requires the call;
- **what is currently deployed**, since no read-back endpoint exists — so the "what will be erased"
  warning is only as good as the tool's own local history;
- whether the extension **actually fires**, which per the SSS precedent can silently fail (F.5).

**A green dry run of the JEF deploy proves the request was well-formed locally. It proves nothing about
QAD's acceptance.** The owner's rule already says this: *never report deploy as done on the strength of
a dry-run.* Treat the first live deploy as an experiment, on a throwaway app, with the jar contents
recorded beforehand.

**Also not dry-runnable:** whether an extension fires at all. The only proof is the manual test —
`DOC:836-838`, `DOC:878-881`: trigger the rejection path *and* the accept path.

---

# K. WHAT ONLY THE OWNER CAN SUPPLY

| # | Item | Why it cannot be read from any codebase | Blocks |
|---|---|---|---|
| 1 | **`QAD_PASSWORD`** in `backend/.env` | Secret. `QAD_CLIENT_ID` and `QAD_USERNAME` are already set | Every live call |
| 2 | **LLM API key** for the active provider (`LLM_PROVIDER=openai\|nvidia`) | Secret | Generation stages only |
| 3 | **Q-L: did `probe_parent_eh.py` ever run, and what did it print?** | Output went to stdout and was never persisted. Only the person who ran it knows | Phase 5 update contract |
| 4 | **Q-F: permission + which environment** for the grid-claiming experiment (two arms) | A live write on a standard parent view | Phase 5 design |
| 5 | **Confirmation of the static/dynamic classification** | A judgement call, explicitly deferred to the owner | Settings panel |
| 6 | **Whether the target environment is fixed** — the 500s, the jar download, the stuck BC | External; network team | **All live JEF work** |
| 7 | **A working dependency jar**, or an environment that serves one | Currently undownloadable | `javap`, discovery, compilation |
| 8 | **Permission to run `javap` / `jar tf`** against that jar, and where it is | Read-only but needs the artifact | The real API surface |
| 9 | **Which QAD app to target for JEF**, and whether its app definition declares the needed module BCs | A server-side app-definition choice, not in any repo | Which `BaseService` stubs exist |
| 10 | **Whether a throwaway app exists** for the first live deploy | Whole-jar replacement makes a shared app risky | First live deploy |
| 11 | **The class-6 "materials" handout** — the deck says *"Copy code from the file, which provided in materials for current class"* (`DOC:706`) | An external file not in the repo. It holds the uncropped `package` line and imports | The docs bundle's highest-value page |
| 12 | **The VSIX** `qad-java-sse-vscode-1.0.10` itself | Would let us settle F1 (undeploy) by grepping `contributes.commands` | Undeploy question |
| 13 | **Capture 2 from H.5** — the Build-and-Deploy multipart body | Only obtainable from a working plugin against a working environment | The one genuinely unproven JEF payload |
| 14 | **Confirmation of `QAD_CLIENT_ID` placement** — `.env` vs committed config | Convention conflict between AUX and the JEF plugin | Nothing; one-line move |

---

# CONFIDENCE MAP

## Certain — verified by reading the file or running the command myself

- **No JEF/Java code exists in either repo.** Phase 6 not started.
- **No server-side wire captures exist.**
- The complete contents and behaviour of AUX's SSS implementation: `sss_scaffold.py`, `ts_compiler.py`,
  `routers/sss.py`, `sss/{appconfig,compile,deploy,discover,readiness,templates}.py`, `sss_template/`.
  Every path, constant and command in section F was read from the file.
- **The two-auth-mechanism split** (Bearer for qracore/JEF, JSESSIONID for the SSS upload only) —
  `core/qad_session.py:27-29,43-93`.
- The SSS deploy URL has **four** query parameters including `filename`.
- **`probe_parent_eh.py`'s exact contents**, both payload shapes, the two-field difference between them,
  and their mutual exclusivity.
- The endpoint registry, the environment identity, and the classification as recorded.
- The class-6 guide's documented workflow, naming conventions, and its **absence** of any API contract.
- The five traps, and that trap 5 has already recurred in this project.

## Reasonably confident — one good source, not independently reproduced by me

- **The entire JEF REST contract** (section C.1). Owner-confirmed via decompile + live sandbox deploy.
  I never saw either. It is the best warrant available and it is not a capture.
- **The `javap` API surface and the reference `TrainingCapacityValidation` class.** Same provenance.
  The class is stated to have deployed and worked on both paths.
- **The build commands, POM specifics, manifest keys, and scaffold layout.** Same provenance; the
  scaffold and `mvn clean package` are independently corroborated by the deck.
- **JDK 17 toolchain targeting bytecode 1.8.** Two sources agree once the deck's staleness is accounted
  for.

## Shaky — inference doing real work

- **The resolved URL shape for `eeadaptive`** (`{base_url}/api/qracore/…`, no `/qad-central/`).
  Derived from a confirmed fact; **no call has been made.** First thing to prove or disprove.
- **The extension class's own package.** Cropped from the deck; the brief's example is the only witness.
- **`JEF_WORKSPACE_DIR` semantics.** No such setting exists yet; I inferred it from the SSS analogue.
- **Naming patterns generalised from n=1** — `<BC>BaseService`, `<bc>-server-side-extension`,
  `urn_app_<fullAppName>`.
- **That the dependency jar lands in `lib/`.** Implied by the brief's `install-file` path, never stated.
- **That `super` is mandatory.** The deck states no rule, and `DOC:43` says extensions may *"completely
  override"* default behaviour — which cuts against it.
- **The undeploy reconciliation (F1).** Three ranked hypotheses, none tested.

## Missing entirely — do not let confident prose elsewhere obscure these

- **Every JEF response body and status code.** Never observed.
- **The deploy multipart shape** — part count, filenames, content types. The single biggest unknown on
  the critical path.
- **Whether `probe_parent_eh.py` ever ran**, whether the hash rotates, and which payload shape QAD
  accepts. (Q-L)
- **Whether two modules can claim the same grid.** (Q-F, and the question needs re-framing first)
- **Whether JEF has a `…WithConfirmation` split** like SSS. If it does and you miss it, rules deploy
  cleanly and never fire.
- **What `data/` in the scaffold is for.**
- **The jar's internal structure** — no `jar tf` listing has ever been seen.
- **Whether rollback works.** Untested, no undeploy, nothing may depend on it.
- **What "Business Services" means** in QAD's vocabulary, and which tab corresponds to it.
- **Any BC → parent-view-URI derivation rule.**
- **Whether two extension classes may target one BC.** Deck says yes; owner's rule says one until tested.
