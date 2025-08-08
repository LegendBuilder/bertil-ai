Android emulator run guide

Prereqs
- Android Studio with SDK/emulator installed
- Flutter in PATH (stable)

Run backend locally
- In repo root: `uvicorn services.api.app.main:app --reload`

Run app in emulator
- `cd apps/mobile_web_flutter`
- `flutter pub get`
- `flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000`

Notes
- `10.0.2.2` routes Android emulator to host `localhost`.
- For iOS simulator, use `http://localhost:8000`.

