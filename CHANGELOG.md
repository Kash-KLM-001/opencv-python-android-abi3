# Changelog

All notable changes to this wheel. Each entry follows the same template:
**symptom → root cause → fix → how to verify**.

## Unreleased

### Fixed — native camera produced no frames

* **Symptom:** `cv2.VideoCapture(0)` reports `isOpened() == True` but every
  `read()` fails after 2 s with `Failed to grab image from camera`.
* **Root cause:** Camera2 NDK dispatches its callbacks on the looper of the
  thread that created the camera. A Python thread has no `ALooper`, so
  `OnSessionReady` / `OnCaptureCompleted` never ran and `grabFrame()` always
  timed out.
* **Fix:** `cap_android_camera.cpp` now prepares an `ALooper` in `initCapture()`
  and pumps it with `ALooper_pollOnce` while waiting for the session and for
  each frame. No extra thread, no JNI copy per frame.
* **Verify:** `examples/camera_capture.py` saves
  `/storage/emulated/0/camera_capture.jpg`; `nm -D cv2.abi3.so | grep ALooper_`
  lists `ALooper_forThread`, `ALooper_prepare`, `ALooper_pollOnce`.
  Details: [`CAMERA.md`](CAMERA.md).

### Docs

* Added [`CAMERA.md`](CAMERA.md) and [`examples/camera_capture.py`](examples/camera_capture.py).
* README / `WHEEL_USAGE.md` gained a Camera section.

## v4.10.0 — RGBA color fix

* **Symptom:** pyjnius `SurfaceView` preview showed red and blue swapped.
* **Root cause:** Android `ARGB_8888` `copyPixelsFromBuffer` expects **RGBA**
  bytes, but OpenCV frames are BGR.
* **Fix:** `_android_gui.py` gained `_rgba()` (BGR→RGBA reorder); the
  `setPixels` fallback packs `0xAARRGGBB` correctly; `_tk_highgui._rgb` uses
  `_rgba(...)[:, :, :3]`.
* **Verify:** a pure-red frame displays as `[255, 0, 0, 255]`; also checked
  blue, green, gray, BGRA and float inputs.

Also in this release:

* pyjnius nested-class lookups (`$LayoutParams`, `$ScaleType`) via `autoclass`.
* UI-thread exceptions re-raised in `_run_on_ui()` instead of swallowed.
* `SurfaceView` waits up to 2 s for the surface before drawing.
* Decor-view fallback when `addContentView` fails on Pydroid.
* `CV2_GUI_LOG` diagnostics in every backend.

## Earlier

* Tk backend encodes frames as PNG (Pydroid's Tk rejects PPM `data=`).
* `pycompat_shim.h` redirects CPython private symbols to stable-ABI entry
  points; Pydroid wheel links `libpython3.13.so` with a relative RUNPATH.
* Termux one-time `LD_PRELOAD` re-exec in `cv2/init.py`.
