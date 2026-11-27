# TS eLibrary AVP Feature Progress

**Presentation date:** 30 October 2026  
**Status:** Local demonstration and testing; not production-deployed.

## Slide-by-slide feature details and narration

### 1. Opening
Introduce TS eLibrary as a catalog and digital-resource platform with staff circulation and borrower self-service.

### 2. Project progress
Summarize the delivered areas: role-restricted account creation, circulation, catalog discovery, digital resources, security/monitoring, and local validation.

### 3. Current progress
Use the live account-registration screen to show that borrower account creation is restricted to Administrator and Admin Staff accounts. Clarify that staging and production services have not yet been validated.

### 4. Accounts and circulation
Use the live user-management screen to show account roles, borrower creation, and password-reset controls. Explain checkout/check-in, renewals, holds, requests, transit, and borrower eligibility controls.

### 5. Digital resources
Use the live borrower resource page to show presentation/document downloads, instructional-video playback, and download-password controls. Explain supported PDF, DOCX, PPTX, and MP4 uploads; video links; OTP for restricted resources; and watermarked download copies. Playback and preview are separate from the download-password prompt.

### 6. Catalog search and discovery
Use the live expanded-filter screen to demonstrate all-fields and field-specific search, Boolean/phrase search, catalog filters, and research browsing by year/class.

### 7. Resource access monitoring
Use the live Resource Access Monitor screen to show views, previews, plays, downloads, filters, and CSV export. Account names and IP values are obscured in the presentation screenshot.

### 8. Research browse
Use the live year/class filter screen. The current local demo has no publications tagged for research browsing, so add representative records before presenting search results.

### 9. Borrower experience
Walk through sign-in, catalog search, filtering, reviewing availability, viewing a PDF/video, protected download, and managing loans/holds in My Account.

### 10. Staff and admin workflow
Show user management, resource uploads, transaction processing, reporting, and the Resource Access Monitor. Emphasize role-specific permissions, including Admin Staff's in-app admin role and restricted superuser access.

### 11. Readiness and next steps
State that local automated tests and Django checks pass, but production deployment has not occurred. Staging must validate PostgreSQL, Redis/Celery, SMTP, HTTPS, private media, backups/restoration, and search performance with 1,000+ records. Confirm agreement wording and branding with project owners.

### 12. Closing
Invite questions and identify staging validation and stakeholder acceptance as the next release gate.

## Accuracy notes for the presenter

- Slides 3-8 include screenshots captured from the running local application; identifying account and IP values are obscured in staff screenshots.
- The deck reuses the supplied template's Air Force crest and illustrative graphics.
- The percentage graphic was removed because it represented no verified project metric.
- The dashboard illustration is explicitly labeled as illustrative, not live application data.
- The local demo URL is not presented as a production address.
- Watermarking applies to generated download copies for PDF, DOCX, PPTX, and MP4; externally hosted resources are outside the application's watermark pipeline.
- Do not describe the project as production-ready. Real infrastructure and end-to-end staging verification remain outstanding.
