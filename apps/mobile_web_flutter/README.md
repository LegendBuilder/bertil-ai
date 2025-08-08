Android emulator run guide

Prereqs
- Android Studio with SDK/emulator installed
- Flutter in PATH (stable)

Run backend locally
- In repo root: `uvicorn services.api.app.main:app --reload`
- Or PowerShell: `./scripts/dev/run_backend.ps1`

Prepare platforms (first time)
- `cd apps/mobile_web_flutter`
- `flutter create .`  (generates `android/` and `ios/` folders)

Allow cleartext HTTP (debug)
- Edit `android/app/src/main/AndroidManifest.xml` and add to `<application>`:
  `android:usesCleartextTraffic="true"`

Run app in emulator
- `flutter pub get`
- `flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000`

Notes
- `10.0.2.2` routes Android emulator to host `localhost`.
- For iOS simulator, use `http://localhost:8000`.

