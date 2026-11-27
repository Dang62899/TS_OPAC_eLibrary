# TS eLibrary mobile app (Capacitor)

A native Android/iOS shell that opens the deployed eLibrary at the login page. The Android project (`android/`) is already generated with the squadron seal as app icon and splash screen.

## 1. Deploy the backend on Render
1. Push the repo to GitHub.
2. Render dashboard > New > Blueprint > select the repo. It reads `render.yaml` and creates the web service and a free PostgreSQL database.
3. When prompted, set `ADMIN_USERNAME` and `ADMIN_PASSWORD` (the first admin is created during the build).
4. When it is live, note the URL, e.g. `https://ts-elibrary.onrender.com`.

Notes: the free tier sleeps after idle time (first load is slow), the free database expires after about 30 days, and uploaded files in `media/` are not persistent (add a Render disk or object storage for real use). This is fine for mock-up testing.

## 2. Point the app at your deployment
Edit `capacitor.config.json`: set `server.url` to `https://<your-service>.onrender.com/accounts/login/`, then run:

    cd mobile
    npm install
    npx cap sync

## 3. Android (Play Store / testing)
- Test now: `npx cap open android`, then Run on an emulator or a USB device in Android Studio.
- Play Store: Build > Generate Signed Bundle / APK > Android App Bundle, then upload to Play Console > Testing > Internal testing and invite testers (requires a Play Console developer account).
- Quick tester APK: Build > Build APK(s), then share the file.

## 4. iOS / Safari
- Without a Mac: open the Render URL in Safari > Share > Add to Home Screen. It installs as a full-screen app that starts at the login page.
- App Store/TestFlight needs a Mac with Xcode: `npx cap add ios; npx cap sync; npx cap open ios`, then Product > Archive > upload to TestFlight (requires an Apple Developer account).

To regenerate icons after changing the seal: edit `assets/` and run `npx capacitor-assets generate --android`.
