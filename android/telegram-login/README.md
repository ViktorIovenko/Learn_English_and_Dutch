# Telegram Login SDK

Vendored MIT-licensed SDK from https://github.com/TelegramMessenger/telegram-login-android
at commit `f9d5ec36ba2433bc5f103b5cd8289f43a05f9336` (SDK 1.0.0).
The local module avoids requiring GitHub Packages credentials for Android builds.

Local adaptations in `TelegramLogin.kt`:

- `startLogin` takes a verifier generated and encrypted by the host application.
- `handleLoginResponse` accepts that saved verifier to recover after process death.
- Automatic browser fallback is replaced with the supplied error callback; users
  without an available Telegram client can choose email or Google in the app.
- Cross-app URLs must use the `tg` scheme, so an HTTP URL cannot open a browser.
- The unused browser dependency and verifier generator are removed.

`build.gradle` uses this project's Android/Kotlin plugins and SDK versions.
Other Kotlin sources and Android manifest are unchanged. Preserve `LICENSE`.
