[app]
title = Spaceness
package.name = spaceness
package.domain = org.spaceness
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.exclude_dirs = tests, bin, backend, website, .venv
source.exclude_patterns = buildozer.log, gradle*, .git, *.idea
version = 1.0.1

requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,certifi

orientation = portrait
fullscreen = 0

# Permissions reseau
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.icon = img/logo.png

# Langue par defaut
android.accept_sdk_license = True
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
