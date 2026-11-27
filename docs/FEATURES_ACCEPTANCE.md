# TS eLibrary — Canonical Feature Acceptance Criteria

This is the single source of truth for feature scope and verification. `FEATURE_ACCEPTANCE.md` is a pointer to this document to avoid duplicate, conflicting criteria.

1) Catalog Search & Filters
- Feature: Free-text search over title, author, ISBN, subjects, description.
- Field-specific search: allow limiting a query to title, author, subject, call number, ISBN, or description.
- Filters: type (book/presentation/video/paper), year, class, unit, format, downloadable (yes/no).
- Checkbox UI: support multi-select checkboxes like Ieduc for subjects/genres.
- Acceptance: all-fields search remains the default; field-specific search restricts matches to the selected field; search returns results within 2s for 1000 records; filters combine with AND semantics; checkboxes persist when paginating.

2) Research Papers Separation
- Feature: Tagging by `year` and `class` metadata; browse view grouped or filtered by these.
- Acceptance: user can select a year or class and see only papers matching that metadata.

3) Account Creation & Roles
- Public account creation is disabled; only administrators and Admin Staff can create borrower/student accounts.
- Admin Staff has in-app admin permissions but cannot create privileged accounts or manage/access superusers.
- Acceptance: borrower account creation and role boundaries are covered by UI/API permission tests.

4) Admin Capabilities & Training
- Admin features: create accounts, reset passwords, and manage in-app library operations.
- Acceptance: admin role pages with create/edit/reset actions secured by permission checks and covered by training doc.

5) Profile Enhancements
- Profile: `photo` upload and basic contact-detail editing.
- Acceptance: photo displays on profile and in user lists; size limits and validation enforced.

6) Document Uploads
- Types: presentation, curriculum, unit briefing, signed SOP.
- Metadata: uploader, upload date, unit, year, class, tags, allow_download (bool).
- Acceptance: upload form accepts file types (pdf, pptx, docx, mp4) and stores metadata.

7) Instructional Videos
- Options: upload actual video file OR provide external link (YouTube/Vimeo/internal CDN).
- Fields: choice of `upload` or `link`, duration, description, access restrictions.
- Acceptance: player able to stream uploaded files and open external links in a safe new tab.

8) View Audit Log
- Feature: log each document view with `user_id` (or anonymous), timestamp (UTC), IP, document id.
- Monitoring: every preview, video play, and download is recorded with its action type, file type, and a username/resource snapshot that survives deletion; staff and admin review it, with filters and CSV export, at Reports > Resource Access Monitor.
- Acceptance: staff and admin can query and export the access log; borrowers cannot reach it; denied attempts are not recorded; logs stored for 1 year (configurable).

9) Download Protection & Checkout Password
- Feature: for protected items, user requests checkout; system generates/accepts a one-time password (OTP) to unlock download.
- Acceptance: downloads require OTP when `allow_download=false` is set; OTP expires in configurable window.

10) Merge Document Pages
- Feature: optional server-side merge of first and second pages into a single PDF for viewing/printing.
- Acceptance: merged PDF generated on-demand and cached for 24 hours.

11) User Agreement & Signed SOP
- Feature: present user agreement on first login; store signed SOP files with searchable unit/class metadata.
- Acceptance: users must accept agreement before using restricted features; signed SOP can be filtered by resource type and metadata.

12) Branding, Logo, Name, Watermark
- Feature: central config for final Elibrary name and logo; watermark generation that stamps current date on documents.
- Acceptance: watermark shows formatted date and branding on PDF previews and PDF, DOCX, PPTX, and MP4 downloads; if watermarking fails, the original file is not served.
- Scope: externally hosted resources cannot be watermarked by this application. Legacy DOC/PPT uploads are rejected for downloadable resources because no safe processor is configured.

13) UI: Merge first/second page, Add Date to Watermark, Add Downloadable Toggle
- Acceptance: UI options available where relevant; toggles persist per-item.

14) Server Requirements (draft)
- Minimum: 4 vCPU, 8GB RAM, 100GB SSD, public IP, TLS cert; optional CPU/GPU for video transcoding.
- Acceptance: provide a short `requirements.md` with recommended specs and scaling notes.

15) Presentation & Handover
- Create a short slide deck describing features, demo steps, and `9532` talking points for Group Commander.

Testing & QA
- Unit tests for model changes and permissions; integration tests for search, upload, and OTP flows.
- Acceptance: CI runs tests and lint; manual QA checklist for admin workflows and video playback.

Implementation notes
- Break work into migration-safe increments: models → admin UI → search → uploads → audit → OTP.
- Respect existing Django architecture and use `media/` for uploads; use Celery for heavy tasks (PDF merge, transcoding).

## Completion Record (2026-10-20)

Implemented and covered by local tests: role-restricted account creation; Admin Staff in-app permissions; profile photo display and size limit; checkbox and field-specific catalog search; research year/class browse controls; attachment unit/class/type/format/access filters; upload type/size checks; uploaded and external video workflows with OTP protection; view audit and configurable retention; configurable OTP expiry; optional first-two-pages-on-one-sheet PDF preview with 24-hour cache; agreement acceptance; branding/date watermarks on PDF, DOCX, PPTX, and MP4 downloads; hash-only per-resource download passwords; admin account actions; and migrations for resource metadata.

Local verification: `python manage.py check`, `pytest`, and correctness lint pass. CI runs pytest and focused flake8 correctness checks on pushes and pull requests; comprehensive style lint and the 1,000-record performance target are not CI gates.

Requires staging or stakeholder confirmation: SMTP/Celery OTP delivery, external video provider behavior, production media/static serving, real PostgreSQL/Redis/HTTPS deployment, measured search performance at 1,000+ records, and final commander/user acceptance. The project is not deployed to production.
