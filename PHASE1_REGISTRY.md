# PHASE 1 — endpoint & settings registry

**Status:** config layer built. **The static-vs-dynamic classification below needs your
confirmation before I build the settings panel around it** — the brief asks me to propose it and
have you verify rather than assume it (Phase 1, bullet 3).

## Answering your question: no, not just BC creation

You asked whether I needed the BC-creation endpoints. I need **all** of them — but it turned out I
didn't need you to supply any. **Every endpoint path was already recoverable**, so the registry ships
pre-populated and you review rather than type:

| Where they came from | Count |
|---|---|
| Read out of AUX's code, each cited to `file:line` | 15 |
| The confirmed JEF decompile in your brief | 5 |

**20 endpoints total.** What I actually needed was the environment identity — which you've now given.

## Files

| File | Committed? | Holds |
|---|---|---|
| [config/endpoints.json](config/endpoints.json) | ✅ yes | All 20 endpoints, segregated by phase/case, each with `source` provenance and `status` |
| [config/environment.json](config/environment.json) | ✅ yes | base URL, app URI, context root, known environment health issues |
| [backend/.env.example](backend/.env.example) | ✅ yes | Template — key names, no values |
| `backend/.env` | ❌ **gitignored** | Real client ID; username/password/OpenAI key still blank |

Verified: `git check-ignore` confirms `backend/.env` is excluded, and `git add --dry-run` stages only
the three safe files.

## The classification — please confirm

### Dynamic — changes per environment

| Value | Where | Status |
|---|---|---|
| `base_url` | `environment.json` | ✅ `https://eeadaptive.yash.com:33005/clouderp` |
| `app_uri` | `environment.json` | ✅ `urn:app:com.yash.digwish` |
| `context_root` | `environment.json` | ✅ empty — see below |
| `QAD_CLIENT_ID` | `backend/.env` | ✅ supplied |
| `QAD_USERNAME` / `QAD_PASSWORD` | `backend/.env` | ⚠️ **still needed** |
| `OPENAI_API_KEY` | `backend/.env` | ⚠️ **still needed** |

### Static — identical across every environment

Everything else: all 20 endpoint paths, `api/qracore`, `oauth/token`, and every
`viewUri=urn:be:com.qad.qra.*` query parameter.

**Reasoning, and the line I'm drawing.** The `urn:be:com.qad.qra.*` URIs name **QAD's own platform CRUD
adapters** — `IEntityBuilderCRUD`, `IViewResourceMetadata`, `IBERelation`, `ILookup`. They ship with the
platform and are the same on every QAD install. Your `urn:app:com.yash.digwish` is the opposite: it names
**your** app, so it's dynamic. That's the whole rule — *does this identifier belong to QAD or to you?*

**If you disagree with any single row, say which** — each is a one-line move between files.

## The one thing I changed from AUX, and why

AUX builds every URL as `{base}/qad-central/api/qracore/{endpoint}`
(`aux_web_version/backend/qad_client.py:57,:65`) against a bare host:port base
(`http://qadee.yash.com:81`). Your Adaptive base already carries its context root: `.../clouderp`.

So **`qad-central` and `clouderp` occupy the same slot.** Adaptive resolves to
`{base_url}/api/qracore/{endpoint}` with no extra prefix — which is exactly the
`{envUrl}api/qracore/…` shape your brief lists as confirmed and exercised live.

**Confidence:** derived from a confirmed fact, but **not yet validated against `eeadaptive`** — no call
has been made. It's the first thing that will prove or disprove itself the moment we test.

AUX hardcodes that prefix in three places. The registry makes it a setting, so it never has to be
guessed again.

## Three things worth your eye

**1. `QAD_CLIENT_ID` placement — I made a judgement call, tell me if it's wrong.**
I put it in `backend/.env` (gitignored). Your brief says the plugin's `config/qad-sse.config.json` holds
`envUrl, id, appURI` and is *"safe to commit"* — so the JEF convention would commit it. But AUX, the
reference implementation, keeps `QAD_CLIENT_ID` in `.env` (`core/config.py:94`). Working rule 7 says
match the reference, so I did. An OAuth `client_id` genuinely isn't a secret in the OAuth sense; both
positions are defensible. **One line to move it if you'd rather it were committed.**

**2. Endpoints that are recorded but deliberately not carried across.**
`sss?appURI=…&appSeq=0&fileSeq=3` is in the registry under `not_ported`, not deleted — a named deferral
per working rule 6. Its `appSeq=0&fileSeq=3` are **unexplained literals** copied from the VS Code
extension; nothing in AUX derives them. Moot for Adaptive, since JEF replaces that path entirely.

**3. Two endpoints are marked `confirmed-in-code-never-executed`.**
`eventhandler.read` and `eventhandler.update` come from `probe_parent_eh.py`. The read is the most
valuable artifact Phase 0 recovered — an existing read-back of a handler on a **QAD-standard parent
view**. The update is a **write against a standard parent** and stays unexecuted pending Q-L.

## What Phase 1 still needs

| # | Item | Blocked on |
|---|---|---|
| 1 | Your confirmation of the classification above | You |
| 2 | `QAD_USERNAME`, `QAD_PASSWORD`, `OPENAI_API_KEY` | You |
| 3 | The settings **panel** (UI reading/writing this config) | Item 1 |
| 4 | Live validation that `{base_url}/api/qracore/…` resolves | A test run |

Exit criterion *"no endpoint literals remain anywhere in code"* is currently met trivially — there is no
application code yet. It becomes a standing constraint from Phase 2 onward.
