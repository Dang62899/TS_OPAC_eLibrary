# TS eLibrary Group Commander Briefing

Presenter: 9532

The presentation uses the repository's configured name, `TS eLibrary`, and logo. The project is available for local demonstration; no production deployment has been performed.

## Demo Sequence

1. Search publications using author, subject, type, year, class, unit, resource type, format, and download access filters.
2. Browse research papers by year and class.
3. Show a publication with a video, downloadable resource, and protected resource.
4. Preview a PDF with date/name watermark and the optional first-two-pages-on-one-sheet setting.
5. In account management, show the Admin Staff role and borrower account creation controls.
6. Show agreement acceptance, administrator account-management controls, and the branded login page.

## Readiness Statement

Local Django checks and automated tests pass. Live deployment remains pending actual PostgreSQL, Redis, SMTP, domain/TLS, and server configuration. OTP email delivery and production storage behavior must be demonstrated in staging after those services are configured.

## Handover References

- Server sizing and software: [SERVER_REQUIREMENTS.md](SERVER_REQUIREMENTS.md)
- Administrator workflow: [ADMIN_TRAINING.md](ADMIN_TRAINING.md)
- Manual validation: [QA_CHECKLIST.md](QA_CHECKLIST.md)
- Acceptance status: [FEATURES_ACCEPTANCE.md](FEATURES_ACCEPTANCE.md)
