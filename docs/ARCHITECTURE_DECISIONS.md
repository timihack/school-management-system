# Architecture Decisions

Started in Phase 6. Earlier decisions live as comments in the code and in each
phase's chat write-up rather than being retroactively backfilled here -
this file captures decisions going forward, plus this one worked example.

---

## ADR-001: Extract `EmploymentProfileBase` only after Staff confirmed real overlap with Teacher

**Context.** Teacher (Phase 5) needed `employee_id`, `date_of_birth`,
`date_joined`, `phone_number`, `address`, `is_active`, `created_at`,
`updated_at`. It seemed likely Staff (Phase 6) would need the same shape,
since both represent "an adult employed by the school."

**Decision at the time (Phase 5): don't extract a shared base yet.**
Only one real example (Teacher) existed. Designing an abstraction from a
single example risks encoding that example's specific shape as if it were
the general rule - if Staff turned out to need something Teacher's shape
didn't anticipate, the abstraction would need reworking anyway, at the cost
of an extra migration and a less obvious git history.

**Decision now (Phase 6): extract it.** Staff's real fields confirmed the
overlap. `job_title` and `employment_type` - the fields that DIDN'T overlap
- stay on the concrete `Staff` model, exactly where they belong. `core/models.py::EmploymentProfileBase` now holds the shared shape;
`apps/teachers/models.py::Teacher` was refactored to inherit it, with zero
change to Teacher's actual database columns.

**Consequence.** The same reasoning was applied to validators:
`core/validators.py::validate_adult_employee_date_of_birth` is shared
between Teacher and Staff (a genuinely identical business rule), while
Student's date-of-birth validator stays separate in `apps/students/validators.py`
(a *coincidentally* similar-looking rule with different actual bounds - sharing
that one would have been wrong).

**General rule this establishes:** extract a shared abstraction once a
SECOND real example confirms genuine overlap - not speculatively from one
example, and not by assuming two things that look similar are actually the
same rule. Check "is this the same rule" before checking "does this look
similar."

---

## ADR-002: `department` FK added to `EmploymentProfileBase`, not to Teacher and Staff individually

**Context.** Phase 7 (Departments) needed both Teacher and Staff to
reference a Department. ADR-001 had already extracted their shared shape
into `EmploymentProfileBase`.

**Decision.** Add `department` to the abstract base itself, once - not to
`apps/teachers/models.py` and `apps/staff/models.py` separately. Both
concrete models get the field automatically. `related_name` uses the
`%(class)s_set` placeholder pattern specifically because two different
concrete subclasses share one abstract base - without it, Django rejects
the migration outright (both would try to register the same reverse
accessor name on `Department`).

**This is the payoff ADR-001 predicted, arriving on schedule.** A genuine
third data point (Department needing to be referenced by both) landed
exactly where the abstraction was already in place to receive it, at the
cost of one field definition instead of two. That's the return on doing
the extraction in Phase 6 rather than earlier or never.

**What this does NOT do:** it doesn't retroactively push `head_of_department`-style
concepts back onto the abstraction, and it doesn't add a
`department` field to `Student` (Classes, not Departments, is Student's
deferred relationship, and it still doesn't exist). Evidence-based
extraction cuts both ways - it also means not over-applying a
newly-validated pattern to cases the evidence doesn't cover.

---

## ADR-003: `ClassEnrollment` reuses Guardianship's "current" pattern, and adds no FK to Student

**Context.** Phase 8 (Classes) needed to track which class a student is
currently in, while also preserving history (needed for repeat-tracking,
per `docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md` Section 3). Phase 4's
`Guardianship` had already solved a structurally identical problem: "at
most one X is current for this student," enforced via a conditional
`UniqueConstraint` plus a service that clears the old flag before
inserting the new one.

**Decision.** `ClassEnrollment` reuses that exact pattern rather than
inventing a new one: `UniqueConstraint(fields=["student"],
condition=Q(is_current=True), ...)`, and
`services.assign_student_to_class()` clears the previous current
enrollment before creating the new one - line for line the same
structure as `link_guardianship()`.

**A second, related decision:** `Student` gets NO new FK for "current
class." `get_current_enrollment()` in `apps/classes/selectors.py` is the
only way to ask "what class is this student in" - there is no cached
field anywhere that could drift out of sync with the enrollment history.
This mirrors how Guardianship's "primary contact" was never cached on
Student either back in Phase 4.

**General rule this establishes:** when a new app needs "track the
current X, but preserve history of past X's," check for an existing
solved instance of that shape in this codebase before designing a new
one. The conditional-UniqueConstraint-plus-clearing-service pattern is
now used twice (Guardianship, ClassEnrollment) for two different
domains - a third occurrence would be a strong signal to extract a
reusable abstraction (a generic "SingleCurrentRelation" mixin or
similar), the same evidence-based threshold ADR-001 used for
`EmploymentProfileBase`.

---

## ADR-004: No school-wide "default assessment template" model - components live directly on each Subject

**Context.** Phase 9 (Subjects) needed to represent configurable CA/Exam
structure: some schools use one CA, others CA1-CA3; the CA/Exam split
can differ per subject. A natural-seeming design would be a two-tier
structure - a school-wide default template, with individual subjects
optionally overriding it.

**Decision.** Rejected the two-tier design. `AssessmentComponent` rows
attach directly and only to a specific `Subject` - there is no
"SchoolAssessmentDefaults" or template model anywhere. Every score-based
Subject defines its own components explicitly.

**Why.** A default-plus-override design needs fallback-resolution logic
checked everywhere components are read ("is this subject using its own
components, or falling back to the school default?"), and that
resolution logic would need to be correct in every selector, every
report-card computation, indefinitely. The direct-attachment design has
no such ambiguity - `subject.assessment_components.all()` is always a
complete, unambiguous answer. The cost is that creating a new
score-based subject requires re-entering CA/Exam components even if
they're identical to every other subject's - mitigated with sensible
pre-filled form defaults (see `AssessmentComponentForm`), not a database
relationship.

**When to revisit.** If, once real subjects exist in volume, re-entering
near-identical components turns out to be a genuine repetitive pain
point (not a hypothetical one), that's the evidence needed to introduce
a template mechanism - following the same evidence-over-speculation
threshold as ADR-001's `EmploymentProfileBase` extraction. Building it
now, before that evidence exists, would be guessing at a shape the real
usage pattern hasn't confirmed yet.

---

## ADR-005: Real report cards corrected two Phase 9 assumptions that speculation alone hadn't caught

**Context.** Phase 9 was designed against `docs/ACADEMIC_STRUCTURE_REQUIREMENTS.md`,
itself built from a detailed but hypothetical description of how Nigerian
school report cards work. After Phase 9 shipped, two REAL report cards
(Elon College, JSS1; AOS Montessori, Playgroup) were reviewed against
what was actually built.

**What held up:** the `GradeBand.label` + `description` pairing matched
real usage exactly - Elon College's letter grades map consistently to
descriptive remarks every time, precisely the shape already built.

**What didn't hold up:**
1. Phase 9 assumed CA+Exam always SUM. Elon College's real computation
   AVERAGES three tests, then averages that with the exam - a
   structurally different formula, not just different numbers.
2. Phase 9 treated `assessment_type` as an exclusive gate (a subject is
   EITHER score-based OR skill-based). AOS Montessori's real domains
   have BOTH a numeric score AND a skill checklist simultaneously.

**Decision.** Rather than treating these as full rewrites, both were
handled as targeted additions: a `computation_method` field on `Subject`
(#1), and relaxing a template-level display assumption that the database
never actually enforced anyway (#2). Neither required tearing up the
underlying models.

**General rule this establishes:** hypothetical requirements gathering
(even detailed, careful requirements gathering) is not a substitute for
checking against real source documents when they become available.
Speculation gave us a reasonable design; real evidence corrected two
specific assumptions within it. This is the same evidence-over-speculation
principle as ADR-001 and ADR-004, applied to REQUIREMENTS rather than to
abstraction timing - real documents are the strongest form of evidence
available, and should be sought out and checked against, not just
guessed at from a description no matter how thorough.

---

## ADR-006: `clear_current_flag` extracted on the third occurrence, exactly as ADR-003 predicted

**Context.** ADR-003 (Phase 8) identified the "at most one current X"
pattern - a conditional `UniqueConstraint` plus a service that clears
the old flag before setting the new one - appearing twice
(`Guardianship.is_primary_contact`, `ClassEnrollment.is_current`), and
explicitly said a third occurrence should trigger extraction instead of
a fourth copy-paste. Phase 10 (`Term.is_current`) is that third
occurrence.

**Decision.** `core/services.py::clear_current_flag()` was added, and -
critically - `link_guardianship` and `assign_student_to_class` were
BOTH refactored to call it, replacing their original bespoke
`.filter().update()` lines. This is the part that actually matters: an
abstraction that gets added but never retrofitted onto its own
motivating examples isn't proven to generalize, it's just been declared
to.

**What was deliberately NOT unified:** the function only extracts the
CLEARING half. The "set the new one" half differs genuinely across all
three call sites - two CREATE a brand new row with the flag already set
(Guardianship, ClassEnrollment), while Term's `activate_term` UPDATES an
EXISTING row to become current, since terms are typically created ahead
of time and activated as a separate later action. Forcing both shapes
into one function would need enough parameters to handle both that the
abstraction would stop paying for itself - a smaller, honest extraction
that only unifies the genuinely identical part beats a larger one that
papers over a real difference.

**A related, smaller decision in the same phase:** `AcademicSession` has
NO `is_current` of its own - only `Term` does, with "current session"
always derived via `current_term.academic_session`. Two independently
stored "current" flags (one on Term, one on Session) would risk drifting
out of sync with each other; one flag with the other derived from it
cannot drift by construction.

---

## ADR-007: `check_role_or_owner` extracted on the third occurrence - the same threshold applied a second time

**Context.** `docs/SECURITY.md` flagged, after Phase 6, that Teacher's
self-edit check (Phase 5) and Staff's self-edit check (Phase 6) were the
same shape twice ("if role in allowed_roles OR this-is-your-own-record,
else 403"), and explicitly said the THIRD occurrence should trigger
extracting a reusable piece instead of a third bespoke copy. Phase 11
(Attendance: "Admin/Staff can mark any arm; a Teacher only their own")
is that third occurrence.

**Decision.** `core/permissions/checks.py::check_role_or_owner()` was
added, and - same discipline as ADR-006 - `TeacherUpdateView` and
`StaffUpdateView` were BOTH refactored to call it, replacing their
original inline `if not (is_manager or is_self): raise...` checks.

**Why a plain function, not a mixin.** The three real call sites reach
"the object being checked" differently enough (a Teacher pk from the
URL, a Staff pk from the URL, a ClassArm resolved from a query parameter
with a fallback to "the requester's own arm if they're a teacher") that
a generic `get_object()`-based mixin would need close to as much
per-view configuration as just calling the function directly inside
each view's `get()`/`post()`. A plain function taking the already-
computed `is_owner: bool` sidesteps needing to standardize HOW that
boolean gets computed - which is exactly the part that keeps differing.

**General rule this reinforces (second time now, after ADR-006):** this
project has TWO recurring "extract on the third occurrence" cases in a
row - "at most one current X" and "role or owner." Both times, the
extraction only unified the genuinely identical half and left the
differing half to callers, and both times the pre-existing
implementations were retrofitted onto the new shared piece rather than
left alone. That retrofit step is what actually tests whether an
abstraction generalizes - a third occurrence that's merely SIMILAR
rather than truly identical should still be left alone, or extracted
more narrowly than instinct suggests.
