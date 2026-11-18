# Changelog

All notable changes to this wheel. Each entry follows the same template:
**symptom → root cause → fix → how to verify**.

## Unreleased

### Added — `cv2.base_runner()`

* **What:** `from cv2 import base_runner` executes a Python source string (or
  a `.py` path) with `cv2` pre-bound, `__name__ == "__main__"`, and returns the
  resulting namespace. Useful on a phone, where keeping a long snippet in the
  launching file is awkward.
* **Why in `cv2`:** the package is always imported before the snippet can run,
  so the helper costs nothing until called and needs no extra module name.
* **Android display:** `CV2_GUI=android` needs a live Activity plus a running
  Kivy process (pyjnius is unavailable in Termux). When a snippet calls
  `imshow` and doesn't start an app itself, `base_runner` wraps it in a minimal
  Kivy app and runs the snippet on a worker thread, so a blocking
  `while True: ... imshow(); waitKey(1)` loop works unchanged.
  `app=True` forces the wrapper, `app=False` keeps plain `exec`.
* **Verify:** `base_runner("x = 6 * 7")["x"] == 42`; `base_runner(123)` raises
  `TypeError`; a path argument reads and runs the file; with a stub Kivy, the
  snippet sees a running app, an own `class A(App)` snippet is not wrapped,
  `app=False` leaves `App.get_running_app()` as `None`, and exceptions are
  re-raised with their original traceback.
* **Caveat:** plain `exec`, not a sandbox.

### Fixed — camera preview was grayscale, rotated and glitched

* **Symptom:** `CV2_GUI=android` showed a grey, 90°-rotated frame with a
  corrupted band; the saved JPEG was 640×720 with one component.
* **Root cause:** `fourCC` defaulted to `FOURCC_UNKNOWN`, so `grabFrame()` chose
  `FOURCC_NV21` and `retrieveFrame()` returned the raw NV21 buffer
  (`1.5 × H` rows, single channel: luma plane plus a chroma band). The sensor
  orientation was also never applied.
* **Fix:** default to `FOURCC_BGR`; read `ACAMERA_SENSOR_ORIENTATION` and rotate
  in `retrieveFrame()`; report the rotated frame size; expose
  `CAP_PROP_ORIENTATION_META` / `CAP_PROP_ORIENTATION_AUTO`.
* **Verify:** `cap.read()[1].shape == (640, 480, 3)`, FOURCC `BGR3`, and
  `examples/camera_check.py` reports `is colour BGR: True`.

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
