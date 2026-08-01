# Security Posture

Living document, updated as each phase changes what's true. Last updated: Phase 4.5.

## Implemented

| Control | How | Where |
|---|---|---|
| CSRF protection | `CsrfViewMiddleware` (on since Phase 1) + `{% csrf_token %}` on every form + `hx-headers` on `<body>` for HTMX requests | `core/settings/base.py`, `templates/base.html` |
| XSS protection | Django template auto-escaping; `\|safe`/`mark_safe` never used anywhere in this project | all templates |
| SQL injection prevention | ORM only (`filter`, `Q`, `get`, `select_related`) - no `.raw()`/`.extra()` anywhere | all `selectors.py`/`services.py` |
| Authentication | Custom `User` model, Django session auth, passwords hashed via Django's default hasher | `apps/accounts/` |
| Site-wide default-deny | `LoginRequiredMiddleware` - every view requires auth unless explicitly `login_not_required` | `core/settings/base.py` |
| Role-based access | `RoleRequiredMixin` / `role_required`, policy centralized per-app in each `permissions.py` | `core/permissions/`, every app's `permissions.py` |
| Data-level isolation | Parent dashboard query scoped to the parent's own children, not role-gated alone | `apps/parents/selectors.py::get_children_for_parent` |
| Login brute-force protection | `django-axes` - locks (username, IP) combination after 5 failed attempts, 1hr cooloff | `core/settings/base.py`, `apps/accounts/tests/test_lockout.py` |
| Secure headers (prod) | `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS, `X_FRAME_OPTIONS=DENY` | `core/settings/production.py` |
| Secrets via environment | `SECRET_KEY`/`DATABASE_URL`/`REDIS_URL` via `django-environ`, `.env` gitignored | `core/settings/base.py`, `.env.example` |
| Temp password entropy | `secrets.token_urlsafe(10)` - cryptographically random, never logged/stored in plaintext | `apps/students/services.py`, `apps/parents/services.py` |
| Data-integrity at the DB layer | `UniqueConstraint` (incl. conditional) rather than app-code-only checks | `apps/parents/models.py::Guardianship.Meta` |
| Atomic multi-model writes | `transaction.atomic` on every operation that creates/mutates more than one model | every `services.py` |
| Object-level permissions | `check_role_or_owner()` - grants access if role OR ownership passes. Used by Teacher self-edit (Phase 5), Staff self-edit (Phase 6), Attendance's "own arm only" check (Phase 11) | `core/permissions/checks.py` |
| "At most one current X" | `clear_current_flag()` + a conditional `UniqueConstraint`. Used by Guardianship (primary contact), ClassEnrollment (current class), Term (current term) | `core/services.py`, each model's `Meta.constraints` |

## Known gaps - not yet addressed

| Gap | Status |
|---|---|
| Audit logging | Still deferred to the dedicated "Audit Logs" module later in the module order |
| Content-Security-Policy | Django's `SecurityMiddleware` headers are on; CSP itself needs `django-csp`, not added |
| Forced password change on first login | Temp passwords are issued but nothing requires changing them |
| File upload security | N/A yet - no file uploads exist in the system yet (student photos, documents, etc.) |

## Notes for future phases

- Every new domain app should get its own `permissions.py` (policy) using the shared `core/permissions/` mixin/decorator (mechanism) - established in Phase 3, followed in Phase 4 and 5.
- Any new operation touching more than one model should be wrapped in `transaction.atomic` inside `services.py` - never left to the view.
- Any new uniqueness/integrity rule that matters should be a DB `UniqueConstraint`, not just a form/service check, per the primary-contact lesson in Phase 4.
- When a role needs to manage/view "their own" record but not others' (Teacher in Phase 5, Staff in Phase 6, Attendance's own-arm check in Phase 11), use `core/permissions/checks.py::check_role_or_owner()` rather than a fourth inline copy - extracted once the third occurrence confirmed the shape was genuinely recurring, not before.
- Shared abstractions (models, validators) get extracted once a SECOND real example confirms genuine overlap - never speculatively for one example alone. See `docs/ARCHITECTURE_DECISIONS.md` for the `EmploymentProfileBase` extraction as the worked example of this rule.
- Last updated: Phase 11.
