Elibrary QA Checklist

Core verification steps:

- Run unit tests: `pytest` (all tests should pass)
- Verify borrower profiles contain contact details and `photo`, with no student-registry fields or lifecycle history
- Confirm anonymous and regular staff account creation is denied; confirm administrators and Admin Staff can create borrowers
- Confirm Admin Staff cannot create privileged accounts, access Django superuser administration, or manage superusers
- Verify the login page has no site header or passkey sign-in and displays the squadron seal
- Confirm profile photos render in the user list and oversized uploads are rejected
- Verify registration flows and admin creation/reset
- Test all-fields and field-specific search (title, author, subject, call number, ISBN, description), checkbox filters, and combined search by type, author, subject, year, class, unit, resource type, format, and download access
- Verify research browse controls and pagination preserve year/class selections
- Upload presentation, curriculum, SOP, and MP4; verify type/size limits, metadata, inline playback, and external-link behavior
- Request and confirm OTP for protected downloads/videos; test configured expiry, single-use behavior, and direct-access denial
- Verify the Resource Access Monitor (Reports) shows who previewed, played, or downloaded each PDF, DOCX, PPTX, and MP4, filters by action and file type, exports CSV, and is not reachable by borrowers
- Load sample data with `python manage.py seed_demo_data` (local/demo only; refuses to run when DEBUG is off)
- Run the configured retention task and confirm only records older than `VIEW_LOG_RETENTION_DAYS` are removed
- Validate date/name watermark on every page of PDF previews and PDF, DOCX, and PPTX downloads; verify MP4 download watermark is visible and processing failures never serve the original file
- Confirm external resources are labeled as externally hosted and are not represented as locally watermarked
- Verify optional first-two-pages-on-one-sheet preview and 24-hour cache behavior
- Run performance smoke tests for search queries (sample 1000+ records)

Deployment-specific checks:

- Verify static files served and `static/images/9532_training_squadron_seal.png` displays
- Configure SMTP in env and verify OTP emails are sent by Celery worker
- Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` for background tasks

Record results and open issues in the tracker.