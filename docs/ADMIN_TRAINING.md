# Administrator Training Guide

Use a local or staging installation for training. Do not use the sample credentials or local SQLite data in production.

## Accounts and Roles

1. Public account creation is disabled. Only Administrator and Admin Staff accounts may create borrower/student accounts.
2. Admin Staff has in-app administrator permissions but cannot access Django superuser administration or create privileged accounts. Administrator accounts may create staff and administrator roles.
3. Use **Reset password** to issue a temporary password through the approved secure channel. Do not place passwords in tickets or presentation materials.
4. Review the profile photo and contact details on the account screens.

## Publications and Resources

1. Create or select a publication, then upload a resource as a presentation, curriculum, unit briefing, signed SOP, instructional video, or other file.
2. Add unit, class, year, description, and duration metadata when relevant.
3. Select whether the resource is directly downloadable or protected by an OTP.
4. For a PDF, optionally enable the first-two-pages-on-one-sheet preview. Set a per-resource download password for downloadable files; PDF, DOCX, PPTX, and MP4 download copies receive date/name watermarks.
5. For video, use an MP4 upload for inline playback or a trusted external link. Protected video playback requires OTP authorization.

## Audit and OTP

- View records include user, timestamp, IP address, and the viewed publication/attachment.
- Records are retained for `VIEW_LOG_RETENTION_DAYS` (default 365) and purged daily by Celery Beat.
- Protected downloads use a single-use code. The default expiry is 15 minutes and is configurable with `DOWNLOAD_OTP_TIMEOUT_MINUTES`.
- Email delivery requires working SMTP, Redis, and Celery worker configuration. Verify delivery in staging; local fallback display is for testing only.

## Before Production

- Confirm production secrets and environment variables with the system owner.
- Verify PostgreSQL migrations, media storage, static files, HTTPS, SMTP, Celery worker, and Celery Beat in staging.
- Complete [QA_CHECKLIST.md](QA_CHECKLIST.md) and record results before launch.