# API captures needed — what to grab, and when

**None of this blocks the build.** Stages 2–5 and the whole dry-run flow can be finished without a
single capture. Each item below either settles something currently guessed at, or upgrades a free-text
box into a picker.

## How to capture

All of these come from the same method the platform guide itself recommends for finding a Browse URI
(class 4, page 9): **open the screen in QAD, F12 → Network, do the action, copy the request.**

For each item, send me:

1. The full **request URL** (including query string)
2. The **request body**, if it is a POST
3. **One response body** — trimmed to a couple of records is fine

⚠️ **Strip anything that looks like a credential** before sending — bearer tokens live in the
`Authorization` header, and I don't need it. I only need the URL, the body shape, and the field names.

## The `browses` endpoint is probably generic — that's the key

The confirmed JEF contract has:

```
GET {base}/api/qracore/browses?browseId=urn:browse:be:com.qad.qra.app.IApp&pageSize=1000
```

That reads as **one generic query endpoint** where `browseId` picks *which* browse to read. If so, we
don't need new endpoints at all — we need the right `browseId` values, and each one falls out of a
single Network capture. **[INFERRED from the URL shape — not confirmed.]** Capture 1 tests it.

---

## Priority 1 — settles the last two lookup unknowns

**Why:** the Lookup Definition payload is the one request shape we'd be sending unverified. Two things
are still guesses: the `searchFieldOperator` wire value (the UI shows a phrase — "equals", "greater or
equal to" — and the wire value is unknown), and whether `uri` / `modelId` / `concurrencyHash` are
required on create. **One capture settles both.**

**When needed:** before the lookup stage is allowed to write live. Until then it stays dry-run-locked.

| # | Do this | Gives us |
|---|---|---|
| 1a | Main Menu → **Lookup Definition**. Capture the GET that loads the list | The `browseId` for lookups, and whether `browses` is generic |
| 1b | **Open an existing lookup record.** Capture the GET | The full wire shape of a real saved lookup — operator casing, and whether `uri`/`modelId`/`concurrencyHash` are present |
| 1c | *(best of all)* **Save any lookup**, even unchanged. Capture the POST **body** | Exactly what a create/update sends. This is the definitive answer |

If only one is possible, **1c**.

---

## Priority 2 — turns the Browse URI box into a picker

**Why:** at the event-handler stage and the lookup stage you'd currently type a Browse URI. The guide
shows QAD's own **"Resource lookup"** dialog doing this with a searchable list (class 4, pages 9–10). If
we can call whatever that dialog calls, you pick from real values instead of typing a urn.

**When needed:** before the stage-4 and stage-6 dialogs are finalised. Free text works either way, so
this is an upgrade rather than a dependency.

| # | Do this | Gives us |
|---|---|---|
| 2 | In Lookup Definition, click the **search icon on Browse URI**. Type a few letters. Capture the request the dialog fires | The browse-list endpoint + its search parameter |

---

## Priority 3 — catch a duplicate BC name *before* the write

**Why:** AUX fails at BC creation with *"already exists"*, and its own code stops there because a name
collision "cannot be repaired by editing fields" (`pipeline.py:226-231`). That failure is also the exact
thing that trips our regeneration lock — the BC now exists, so stage 2 can't be re-run.

**If we can list existing BCs, the stage-2 gate warns you before you approve**, and the whole situation
is avoided rather than recovered from.

**When needed:** before the first live run. Genuinely worth having early.

| # | Do this | Gives us |
|---|---|---|
| 3 | Open the **Business Component list** (the screen showing existing BCs). Capture the GET | A name pre-check for stage 2 |

---

## Priority 4 — the deploy gate's actual content

**Why:** `deployCheckForWarnings` is called and its response **thrown away** in AUX — never assigned,
never checked (`pipeline.py:739`). Those warnings are the entire point of your deploy gate, and we don't
know what the response looks like.

**When needed:** before the stage-7 dialog is finalised. Also obtainable from our own first live run.

| # | Do this | Gives us |
|---|---|---|
| 4 | **Deploy any BC** in QAD. Capture the `deployCheckForWarnings` **response** | What to render at the deploy gate |

---

## Priority 5 — is there a DELETE for a Business Component?

**Why:** Phase 0 found no delete path. That is why the regeneration lock tells you to *"delete it in QAD
yourself"* rather than offering to do it. If a delete API exists, the lock can offer a real way back and
a failed run stops being a dead end.

**When needed:** not urgent, but it changes what the lock can offer.

| # | Do this | Gives us |
|---|---|---|
| 5 | If QAD's BC screen has a **Delete** action, use it on a throwaway BC and capture the request | An undo path, if one exists |

---

## Not a capture — settled by behaviour on the first live run

**Which writes are idempotent.** Only `bc.create` is definitely create-only. Whether `viewMetadataV2`,
`eventhandler`, `viewResourceMetadatas` and the deploy pair can be safely re-sent is untested —
`eventhandler` carries a `concurrencyHash`, which hints at update-in-place.

This matters because **every idempotent write relaxes the regeneration lock for its stage.** If the form
save can be re-sent, you can go back and redo the form after it has been written. No capture will tell
us; only trying it will. The audit trail in `qad_writes` records every attempt, so the first live run
answers it for free.

---

## Summary — what I need, and when

| When | What | Blocks |
|---|---|---|
| **Any time** | `QAD_PASSWORD`, `OPENAI_API_KEY` in `backend/.env` | The first live call |
| Before lookups go live | **Capture 1c** (a lookup save POST body) | Live lookup writes only |
| Before the dialogs are final | Captures 2, 3 | Nothing — upgrades free text to pickers |
| Before the deploy gate is final | Capture 4 | Nothing — obtainable from our own run |
| Whenever | Capture 5 | Nothing — changes what the lock can offer |

**Right now the only thing I'd actually queue you for is capture 3** (the BC list), because catching a
duplicate name before the write is worth more than recovering from it afterwards — and it is one screen
and one Network entry.
