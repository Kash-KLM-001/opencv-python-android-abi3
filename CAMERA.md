# Camera capture (`cv2.VideoCapture(0)`)

The wheel's Camera2 NDK backend works from a plain Python script on Pydroid 3,
Termux and python-for-android. This document records the bug, the fix, and how
to verify it — it doubles as the template we use for every change in this repo.

## Symptom

```python
cap = cv2.VideoCapture(0)
print(cap.isOpened())   # True
ret, frame = cap.read() # False
# [ WARN] No Buffer Available error occurred - waiting for callback
# [ERROR] Failed to grab image from camera
```

The camera opened and the session was created, but no frame ever arrived.

## Root cause

`cap_android_camera.cpp` registers Camera2 NDK callbacks
(`OnDeviceDisconnect`, `OnSessionReady`, `OnCaptureCompleted`, …). Android
dispatches those callbacks on the **looper of the thread that created the
camera**. A Python interpreter thread has no `ALooper`, so the callbacks were
queued and never run:

* `OnSessionReady` never fired, so the repeating capture request was armed
  before the session was ready.
* `OnCaptureCompleted` never fired, so `captureSuccess` stayed `false` and
  `grabFrame()` always hit `CAPTURE_TIMEOUT_SECONDS` (2 s).

This is not a permission problem and not a camera-index problem: a longer
`sleep()` or a different index cannot fix it.

## Fix

One looper per capturing thread, prepared once and pumped only while waiting.
No extra thread and no background CPU cost.

`modules/videoio/src/cap_android_camera.cpp`:

1. Include `<android/looper.h>`.
2. In `initCapture()`, before creating the camera manager:

   ```cpp
   if (ALooper_forThread() == nullptr) {
       if (ALooper_prepare(ALOOPER_PREPARE_ALLOW_NON_CALLBACKS) == nullptr) {
           LOGE("Cannot prepare camera looper!");
           return false;
       }
   }
   ```

3. After `createCaptureSession`, pump until the session reports ready:

   ```cpp
   auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(CAPTURE_TIMEOUT_SECONDS);
   while (sessionState == CaptureSessionState::INITIALIZING &&
          std::chrono::steady_clock::now() < deadline) {
       ALooper_pollOnce(CAPTURE_POLL_INTERVAL_MS, nullptr, nullptr, nullptr);
   }
   ```

4. In `grabFrame()`, replace the `condition.wait_for(...)` with a looper pump:

   ```cpp
   bool captured = false;
   while (!captured) {
       lock.unlock();
       ALooper_pollOnce(CAPTURE_POLL_INTERVAL_MS, nullptr, nullptr, nullptr);
       lock.lock();
       captured = captureSuccess;
       if (!captured && elapsedTimeFrom(start) >= CAPTURE_TIMEOUT_SECONDS) break;
   }
   ```

`ALooper_pollOnce` runs the queued Camera2 callbacks on the calling thread, so
`OnCaptureCompleted` sets `captureSuccess` and the frame is acquired normally.

### Why not Java / pyjnius?

| Path | Per-frame cost |
|------|----------------|
| Native C (this fix) | Frame stays in native memory, YUV→BGR in C++ (NEON), **zero JNI crossings** |
| Java + pyjnius | Camera → Java `byte[]` → JNI copy → Python `bytes` → NumPy → `cvtColor`; 3–4 copies per frame |

The native path is typically 2–5× faster and is what the wheel already ships.

## Build

```bash
# compile the changed file only (fast check)
cd build_android_abi3
ninja modules/videoio/CMakeFiles/opencv_videoio.dir/src/cap_android_camera.cpp.o

# relink the extension and rebuild wheels
./build_abi3.sh
bash strip_abi3.sh          # 444 MB unstripped -> ~40 MB stripped

cp output/cv2.abi3.so output/cv2.abi3.pydroid.so
patchelf --add-needed libpython3.13.so output/cv2.abi3.pydroid.so
patchelf --set-rpath '$ORIGIN/../../../../lib' output/cv2.abi3.pydroid.so

CV2_SO=output/cv2.abi3.pydroid.so CV2_WHEEL_PLATFORM=linux_aarch64 python3 make_wheel.py
CV2_SO=output/cv2.abi3.so CV2_WHEEL_PLATFORM=android_24_arm64_v8a python3 make_wheel.py
CV2_SO=output/cv2.abi3.so CV2_WHEEL_PLATFORM=linux_aarch64.android_24_arm64_v8a python3 make_wheel.py
```

Check the fix landed in the binary:

```bash
strings -a output/cv2.abi3.so | grep "Cannot prepare camera looper"
nm -D output/cv2.abi3.so | grep ALooper_   # forThread, prepare, pollOnce
```

## Verify on device

```bash
python examples/camera_capture.py                 # headless, saves a JPEG
CV2_GUI=tk python examples/camera_capture.py      # live Tk preview
CV2_GUI=android python examples/camera_capture.py # SurfaceView preview (fastest)
```

Expected headless output:

```
cv2: 4.10.0
gui_backend: native
Trying camera index 0 (default)...
Camera ready: index=0 backend=default shape=(480, 640, 3)
Frame 1: (480, 640, 3)
Saved: /storage/emulated/0/camera_capture.jpg
Size: 45123 bytes
```

If frames still fail:

1. Grant Camera permission to the app, close other camera apps.
2. `CV2_CAM_INDEX=1` selects the front camera.
3. `logcat | grep -i "AndroidCameraCapture\|NativeCamera"` shows the NDK log
   lines (`session ... ready`, `No Buffer Available`, …).
4. Confirm the installed wheel is the one containing this fix:
   `python -c "import cv2,hashlib;print(hashlib.sha256(open(cv2.__file__,'rb').read()).hexdigest())"`.

## What still does not work

| Input | Status |
|-------|--------|
| `VideoCapture(0)` — camera | ✅ works after this fix |
| `VideoCapture("file.mp4")` — local media | ✅ MediaNDK |
| `VideoWriter("out.mp4", …)` — local media | ✅ MediaNDK |
| `rtsp://`, `http://` streams | ❌ needs FFmpeg (not built) |
