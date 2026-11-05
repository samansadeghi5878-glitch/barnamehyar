[app]

title = BarnameYar
package.name = barnamehyar
package.domain = ir.barnamehyar

source.dir = .
source.include_exts = py,kv,png,jpg,atlas,ttf,json
source.include_patterns = fonts/*.ttf
source.exclude_dirs = .git,venv,.venv,__pycache__,bin

version = 1.0.0

requirements = python3,kivy,arabic-reshaper,python-bidi,jdatetime

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.bootstrap = sdl2

[buildozer]

log_level = 2
warn_on_root = 1
