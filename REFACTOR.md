## Mobile Expansion Design Spec for `voca_test`

### Purpose

This document defines a practical, low-risk design to make `voca_test` usable on phones while preserving the current architecture and CLI workflow.

The key idea is simple.

* Keep the C++ core as the single source of truth for learning logic
* Add a mobile UI as a thin layer that talks to the core through a stable interface
* Keep offline-first behavior and easy deck management (CSV import/export)

---

## Goals

* Run vocabulary sessions on mobile with a fast, minimal “memory trainer” UX
* Preserve the existing C++ engine behavior and test coverage
* Support offline use
* Make deck management easy (import CSV, export wrong list, export stats)
* Enable the “immediate retry + progressive hints” learning behavior on mobile

---

## Non-goals

* Full-featured flashcard app with accounts, social, marketplace
* Rewriting the engine in Kotlin/Swift
* Complex server infrastructure as a requirement

---

## Mobile UX Requirements

* One-handed friendly UI
* Keyboard-first input, minimal taps
* Clear hint progression when the user fails
* Immediate retry behavior is explicit and predictable
* “Focus mode” option that reduces extra text and distractions
* Quick session presets

  * short burst (10–20 questions)
  * wrong-only review

---

## Architecture Overview

A layered architecture, where the mobile layer never re-implements learning logic.

* Core Layer (C++)

  * deck loading
  * question selection
  * answer checking
  * retry/hint progression state
  * result and wrong tracking
  * stats update (optional but recommended)

* Interface Layer (stable boundary)

  * JSON-based session protocol
  * deterministic inputs/outputs for testing

* UI Layer (mobile)

  * PWA / mobile web UI
  * local storage + import/export
  * optional sync

---

## Recommended Delivery Path

### PWA + WebAssembly (WASM)

Why this is the best first mobile step.

* Runs on both Android and iOS
* Installable like an app (Add to Home Screen)
* Offline-first is straightforward
* You can compile the existing core into WASM and call it from JavaScript
* No app store required to iterate quickly

High-level structure.

* `voca_core` compiled to WASM
* PWA UI calls core functions and renders state

This keeps one learning brain and avoids duplication.

---

## Core API Design for Mobile

The mobile UI needs a session-oriented API, not a “print to stdout” API.

### Core Concepts

* Deck

  * list of entries (word, meaning, optional metadata)
* Session

  * current question
  * attempt count
  * hint level
  * queues (main + retry/delay)
  * result summary
* Engine Output

  * a structured “what to display” payload

### Minimal C++ Interface (conceptual)

* `loadDeckFromCSV(csv_text) -> deck_id`
* `startSession(deck_id, config) -> session_id`
* `getPrompt(session_id) -> Prompt`
* `submitAnswer(session_id, answer) -> Feedback`
* `getSummary(session_id) -> Summary`
* `exportWrongCSV(session_id) -> csv_text`

This can be exposed to JS (WASM) without leaking internal classes.

---

## Session Protocol

Use JSON as the single boundary format so the same protocol can be used for CLI testing, WASM, and native apps.

### `Prompt` JSON

* `question_id`
* `question_text`
* `direction`

  * `en_to_kr`
  * `kr_to_en` (future)
* `hint`
* `attempt`
* `progress`

  * `done`
  * `total`

Example fields (format can be adjusted).

* `question_text`: `"apple"`
* `hint`: `"a____ (5 letters)"`
* `attempt`: `2`

### `Feedback` JSON

* `is_correct`
* `correct_answer`
* `next_action`

  * `retry_same`
  * `next_question`
  * `show_summary`
* `hint_level`

The mobile UI can render this consistently without knowing internals.

---

## Hint Policy Design

Mobile needs hints that are fast to read and easy to type against.

Recommended hint levels for spelling recall.

* show letter count
* show first letter
* reveal prefix gradually
* show full answer but require re-typing to pass

This policy should live in the core session state so behavior matches CLI.

---

## Data Model and Storage

### Deck Format

Keep current `word,meaning` CSV as the baseline.

Allow optional extra columns later without breaking older decks.

* `word,meaning`
* `word,meaning,example`
* `word,meaning,tag,example`

The loader can ignore unknown columns unless enabled.

### Mobile Local Storage

PWA storage choices.

* IndexedDB for decks and stats
* file import/export for CSVs
* optional “backup” zip export for all data

### Export/Import

Mobile must support.

* import deck CSV
* export wrong CSV
* export stats (CSV or JSON)

This avoids forced accounts while still enabling cross-device workflows.

---

## Sync Strategy

Start with simple and reliable.

* manual import/export
* optional “sync folder” workflow using:

  * Google Drive / iCloud / Dropbox as file storage
  * user-driven sync, not automatic background sync

Later, if needed.

* add a “merge stats” operation
* define a stable stat key (`word + deck_id`)

---

## Project Layout Changes

Add new build targets while preserving existing ones.

* `voca_core`

  * compiled library that exposes session API
* `voca_cli`

  * current binaries, uses the same core
* `voca_wasm`

  * Emscripten build output for PWA

Add a new directory.

* `web/`

  * PWA UI
  * service worker
  * offline caching
  * import/export screens
  * session screen

---

## Build and CI

CI should guarantee identical core behavior across targets.

* existing Linux build + tests remain
* add a WASM build job (optional initially)
* add golden tests for session protocol

Golden test idea.

* feed deterministic answers
* assert exact JSON outputs (prompt/feedback sequences)
* ensures mobile and CLI behave identically

---

## Testing Strategy

Keep the same philosophy you already established, but extend it to mobile.

* unit tests

  * hint generation
  * retry scheduling
  * answer normalization
* integration tests

  * session progression with scripted answers
* regression tests

  * compare old CLI transcript vs new core-backed CLI transcript
* protocol tests

  * JSON schema validity
  * stable `next_action` behavior

For the PWA.

* lightweight end-to-end test that runs a short session in headless browser (later)

---

## Implementation Plan

A staged plan that avoids big-bang changes.

* Stage: Core protocol extraction

  * make CLI call the core session API
  * keep CLI output identical
* Stage: WASM build proof

  * compile core to WASM
  * run one minimal session in a plain HTML page
* Stage: PWA UX

  * session screen
  * deck import/export screen
  * offline caching
* Stage: “Focus mode” and learning polish

  * hint formatting
  * quick session presets

---

## Deployment Plan (Incremental)

This plan keeps deployments low-risk and verifiable at each step.

### Phase 0: Core Protocol + Tests (now)

* Add a session-oriented core API that emits JSON prompts/feedback.
* Add deterministic tests for session flow and hint progression.
* Keep existing CLI behavior unchanged.

### Phase 1: WASM Proof

* Build `voca_core` with Emscripten.
* Run one minimal HTML page that calls the session API.
* Compare JSON outputs against golden tests.

### Phase 2: PWA MVP

* Add `web/` skeleton with offline cache.
* Implement deck import/export and session runner.
* Ship via static hosting (GitHub Pages or similar).

### Phase 3: UX Polish

* Focus mode toggle.
* Quick session presets.
* Stats export UI.

---

## Implementation Status (Current Repo)

* Core session API (JSON prompt/feedback) added.
* Session flow test added.

---

## Key Design Decisions to Lock Early

* JSON session protocol shape
* deck identity and word identity rules
* hint progression policy and max retry policy
* export formats for wrong/stats

Once these are stable, every UI becomes easy.

---

## Deliverables Checklist

* `voca_core` library target with a session API
* JSON protocol definitions documented in README
* PWA skeleton with:

  * deck import/export
  * session runner
  * offline support
* CI that validates:

  * core tests
  * optional wasm build
  * protocol golden tests

---

If you want, I can also write a ready-to-paste `README` section that explains the mobile architecture and usage flow (import deck → run session → export wrong/stats), plus a clean JSON schema block for the session protocol.
