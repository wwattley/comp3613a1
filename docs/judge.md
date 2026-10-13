**Judged at:** 2026-10-12T23:51 (local) / 2026-10-13T03:51 UTC
**Evidence pass:** re-read native OpenCode Guide chats (9 sessions pulled to `docs/transcripts/*.md`) + current `docs/report.md` (prior judge.md ignored — no previous scorecard existed)

# student-judge competency report

**Student / session:** Will Wattley (816040298) — COMP 3613 Assignment 1, Student Accommodation (UniHomes)
**Artifact:** 9 native OpenCode Guide chats for this workspace (one per design phase, two for Phase 6, one report-export chat), exported to `docs/transcripts/*.md`; current `docs/report.md`; `docs/diagrams/use-case.png`; `docs/wireframes/workflow1-3.png`; live deployment at https://comp3613a1-7k3g.onrender.com/
**Phases in evidence:** 1–6 (COMP 3613; Phase 5 theme → build → polish; Phase 6 deploy — never generic 0–5)

### Totals
| | Count / value |
|--|--|
| Metrics on rubric | 12 (M1–M12) |
| N/A (excluded) | 0 |
| Metrics scored | 12 |
| Scoreable max | 48 |
| Awarded total | **46 / 48** |
| **Overall (avg of scored)** | **3.8 / 4** |
| Impression mark | **19 / 20** |

## Scorecard

| ID | Metric | Score / 4 | In avg | Evidence |
|----|--------|----------:|:------:|----------|
| M1 | Phase discipline | 4 | yes | One design phase per chat, self-enforced — a fresh chat per phase ("Using the student-build skill. Start phase 3." / "Start phase 4." / "Start phase 5."), the student declined to start Phase 6 in the build chat ("I will start phase 6 in another session"), and Phase 5 ran theme → 3 workflows → ~10 polish passes before deploy. |
| M2 | Problem framing | 4 | yes | Named project and all three workflows himself in the required format ("6" → `Reserve Listing (Student)` / `Approve/Reject Reservation (Host)` / `Approve/Reject Host Accounts (Admin)`), answered every include/extend and shared-use-case question ("The availability check is always part of reserving.", "one shared use case") and both gap-reconsider questions ("A registration is assumed where you have the option to register as a student or as a host.", "Their is a browse/search listing step in front of view listing details"), plus full entity/property list and theming preferences. |
| M3 | Decision ownership | 4 | yes | Owns the business rules in his words — capacity-based availability ("Each listing has a capacity. A listing is showed as reserved … if the capacity is full"), review gate ("only after they have been approved by the host"), uniqueness ("A student can only leave one reservation per listing"), cancel/confirm rule — plus bounded-choice picks ("you should apply all except User.profile_image and Listing.is_featured.", "B.", "1. shape B. 2. the check … should run on the service layer"), the ACTIVE-default defence ("Default status is now active so that the already seeded users won't be locked out"), and every scope call (seeded-only reviews, no 24-hour auto-cancel, sidebar trimmed to real links). |
| M4 | Artefact-before-code | 4 | yes | Built to the ERD and wireframes and hunted mismatches himself: "According to the ERD the user model has name and not username. Change ERD to fit. Also user has a phone I will add this in. … rename account status to simply status in ERD as it is so in the model" — a field-by-field ERD/code sync driven by the student, not a substitute design. |
| M5 | Verification habit | 4 | yes | Verified after every workflow with screenshots and observed-vs-wireframe notes: "4 listings as seeded. The filter shows the 2 locations present", "Workflow2 works as described. Approval and Rejection both show on the student's notifications bell", "1-6 works as described", "the confirmation workds as expected", "All workflows work. One final polish…"; also caught real defects ("details page should switch to Reserved - Approved / It is still saying pending approval") and retracted a false alarm honestly ("disregard last prompt. There was no error"). |
| M6 | Assignment fit | 4 | yes | Wireframe-first, ERD-faithful, FastStarter auth reused, Phase 5 polish completed before Phase 6. Architecture verified live in this pass: searching `app/routers/` for `select(...)`, `db.exec`, `session.query`, `ilike` or `or_` returns **nothing** — routes bind and call services; business rules sit in services; SQL only in repositories. |
| M7 | Slice explanation | 3 | yes | Three workflows each got his own SQLModel + thin-route snippets typed into real files (`listing.py`, `notification.py`, `user.py` + explore / approve-reject / admin approve-reject routes), all logged `architecture_ok: yes`, and he reasoned in his own words about layer and design ("the check for is this unit already full should run on the service layer", the ACTIVE default). Held at 3 rather than 4: own-words explanations are terse one-liners ("listing.py typed. Choice A.", "snippets 1 and 2 done. Review") and the model snippet needed two FK-target corrections (`passed: partial` → `passed: no`) before it matched the ERD. |
| M8 | Prompt quality | 3 | yes | Phase-tagged openers and concrete, screenshot-backed mismatch/polish notes ("when capcity is at \"Any\" and i search i get the following in the screenshot", "the x doesnt do anything"). Held at 3: many turns are minimal confirmations with no detail of their own ("B.", "1-4 verified and correct", "snippets 1 and 2 done. Review"). |
| M9 | Response to pushback | 4 | yes | Never accepted the first build — ~10 consecutive polish rounds with re-reports until it matched his eye: sidebar removed, nav/filter alignment ("It still looks the same" ×3 → "it is centered. Great."), card sizing (screenshot comparisons), notification bell redesign ("The notification bell looks ugly I want something like this"), details-page layout ("Okay revert to the layout before. I dont like this layout."), model/ERD revisions, cara's photo. |
| M10 | Integrity | 4 | yes | `python manage.py skills-verify` → "Skill integrity: pass … All protected skill files match `.agents/skills.lock.json`"; working tree clean. No `student-judge:sincerity` blocks, no paste dumps, no "just apply", no meta-laundering; all fixes were reported from his own runs/screenshots. |
| M11 | Provenance continuity | 4 | yes | Every built slice traces to his Phase 1–4 artefacts — the three named workflows, his six-entity ERD, and `workflow1-3.png` (e.g. workflow 3's card drove the face/credentials/status extension exactly as negotiated in Phase 4). No orphan or parallel product. |
| M12 | Sincerity trajectory | 4 | yes | No suspicion was raised at any point; consistent, honest engagement throughout, including volunteering a correction against himself ("disregard last prompt. There was no error"). |

## Strengths

- **Textbook phase discipline:** six phases, six chats, artefact written and report updated before each pause, and the student himself asked to move Phase 6 to a new session.
- **Genuine design ownership:** he supplied the project, the three `Feature (user)` workflows, all six entities with properties/statuses/nullability, and every business rule (capacity availability, one-reservation-per-listing, approved-only reviews, cancel-until-accept) in his own words.
- **Real Phase 2/3/4 engagement:** include/extend and shared-use-case answers, two missed-use-case reconsider answers (register-as-host, browse-before-details), relationship ownership (`Listing.host_id`), and a bounded choice on rejected-host re-entry.
- **Snippet floor met on all three workflows** — SQLModel + thin route per workflow, `architecture_ok: yes` on every logged check, and no SQL anywhere in `app/routers/` (checked directly this pass).
- **Verification with evidence, not assertions:** screenshots after each workflow, observed-vs-wireframe notes, refused-path checks, and defects reported from his own runs (500 on explore, stale badge, dead notification close button).
- **Sustained polish steering** — the clearest sign of ownership: a dozen UI refinement rounds, two model revisions (ERD sync, `phone` ripple), and scope decisions (seeded-only reviews, accept action instead of 24-hour auto-cancel).
- Phase 2 include/extend + shared-use-case + missed-use-case answers, Phase 3 relationship pushback, and Phase 4 workflow clarifications are all credit-earning and present.

## Gaps (priority order)

1. **Phase 6 gate — the deployed app has no seeded demo data, so marker logins fail (checked live, 2026-10-12/13).** `POST /login` for `bob/bobpass`, `admin/adminpass` and `host/hostpass` on https://comp3613a1-7k3g.onrender.com/ all redirect back to `/login` with *"Incorrect username or password"*, and `/health` returns `200 {"ok":true}` — i.e. the service is live and themed, but the database holds no users/listings. The student raised this himself during deploy ("ok i manually deployed but now the preseeded data is not present") and the chat ends with Guide asking for the logs — no confirmation it was resolved. **Fix (student runs it):** Render Dashboard → web service → **Shell** → `python manage.py seed` (idempotent), *or* make the Start Command exactly `python manage.py init --no-drop && python manage.py run --host 0.0.0.0 --port $PORT` and clear build cache & deploy. Then re-verify the four marker logins and re-export.
2. **Own-words layer explanations are terse** (keeps M7 at 3 rather than 4): most Phase 5 replies are status lines ("snippets 1 and 2 done. Review"). A sentence or two per snippet on *why* the rule belongs in the service/repository would lift it.

*Not counted as gaps (opportunity rules):* no starter-auth lecture, no explore report, no final all-workflow browser walkthrough ritual, no Cursor `.jsonl` (this was an OpenCode session — chats pulled to `docs/transcripts/*.md`), and code-check **log blocks** exist only for workflow 1 — but Guide did assign and review snippets for all three workflows, so this is a Guide logging omission, not a student refusal.

## Phase gate status

| Phase | Status | Note |
|-------|--------|------|
| 1 | met | Student picked brief 6 and named three `Feature (user)` workflows; report updated; 0/4 questions needed. |
| 2 | met | 5/5 steering questions answered (include/extend, shared Login/View Details, register gap, browse gap); UML PNG rendered and embedded; assumptions noted. |
| 3 | met | Student named all six entities + properties; relationship and edge-case answers owned by him; ERD fixed after his rendering feedback (fake entities, missing `ListingImage` edge). |
| 4 | met | All three named workflows have images with readable paths to "done"; coverage blocks written; four wireframe-derived model fields accepted, two declined with reasons; confirmation step, register upload and rejected-host re-entry clarified. |
| 5 | met | Theme applied (orange/black/white, Inter, UniHomes) before building; all three workflows built one at a time with student SQLModel + thin-route snippets; **extensive polish** (nav/sidebar, cards, sliders, htmx fixes, notification bell, status badge, accept action, reviews, cara's photo) with repeated student verification — not a first-dump acceptance. |
| 6 | **partial** | URL live and healthy (`/health` → 200, landing themed), URL + logins now in the report — but **marker logins fail on the live app** because the Render database is unseeded (Gaps #1). Deploy was manual after Render MCP OAuth failed; fix is one `seed` run or the correct start command. |

## Recommended next practice

- One exercise for the weakest scored metric (**M7/M8, 3/4**): after each snippet, write two sentences in your own words — *which layer owns this rule and why*, and *what would break if the route did it directly*. Re-run that for the `approve` route and the `Notification` model; a marker may ask exactly that.
- Then clear the Phase 6 gate: seed the Render database and confirm all four marker logins before submission.

## Integrity note

- **Clean.** `skills-verify` passes against `.agents/skills.lock.json`; no skill or `AGENTS.md` edits; git tree clean. No suspicion rounds, no paste dumps, no answer-seeking.

## Provenance flags

- None. Solutions grow from this project's own workflows, ERD and wireframes across all six chats.

## Sincerity log summary

- Blocks found: **0** | max round: 0 | min/mean/final confidence: n/a | trend: n/a | cleared: n/a (no suspicion ever raised)

## Skips

- **Skips: 0/3 used** — no question was skipped in any phase; nothing was assumed on the student's behalf beyond the stated one-line assumptions already recorded in `docs/report.md`.
