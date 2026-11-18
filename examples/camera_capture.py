#!/usr/bin/env python3
"""Capture frames from the device camera with ``cv2.VideoCapture`` and save a JPEG.

Works on Pydroid 3, Termux and python-for-android.  The wheel's Camera2 NDK
backend prepares and pumps an Android looper on the calling thread, so
``VideoCapture(0)`` delivers frames even when Python owns the thread.

Usage
-----
    # headless capture (no window), saves /storage/emulated/0/camera_capture.jpg
    python camera_capture.py

    # live preview with the Tk backend (Pydroid)
    CV2_GUI=tk python camera_capture.py

    # live preview with the SurfaceView backend (fastest, needs Kivy process)
    CV2_GUI=android python camera_capture.py

Environment
-----------
CV2_GUI          ``native`` (default here), ``tk`` or ``android``
CV2_CAM_INDEX    camera index to try first (default 0 = back camera)
CV2_CAM_OUT      output path (default /storage/emulated/0/camera_capture.jpg)
CV2_GUI_LOG      set to 1 to log backend diagnostics to logcat
"""

import os
import sys
import time

# Native capture always works; only set a GUI backend if the caller asked for one.
os.environ.setdefault("CV2_GUI", "native")

import cv2

OUT_PATH = os.environ.get("CV2_CAM_OUT", "/storage/emulated/0/camera_capture.jpg")
GUI = os.environ.get("CV2_GUI", "native").lower()
SHOW = GUI in ("tk", "android", "mpl")

# Camera2 callbacks need a moment after open before the first buffer arrives.
WARMUP_SECONDS = 0.5
READ_RETRIES = 10


def _open(index, backend):
    """Open one camera index/backend pair and return a cap with a live frame."""
    try:
        cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
    except Exception as exc:  # TypeError on old bindings, cv2.error on bad backend
        print("  VideoCapture(%s, %s) raised: %s" % (index, backend, exc))
        return None, None

    if not cap.isOpened():
        cap.release()
        return None, None

    time.sleep(WARMUP_SECONDS)
    for _ in range(READ_RETRIES):
        ret, frame = cap.read()
        if ret and frame is not None and frame.size:
            return cap, frame
        time.sleep(0.1)

    cap.release()
    return None, None


def open_camera():
    """Try the configured index first, then the other index and backend."""
    first = int(os.environ.get("CV2_CAM_INDEX", "0"))
    candidates = [
        (first, None),
        (first, cv2.CAP_ANDROID),
        (1 - first, None),
        (1 - first, cv2.CAP_ANDROID),
    ]
    for index, backend in candidates:
        name = "default" if backend is None else "CAP_ANDROID"
        print("Trying camera index %d (%s)..." % (index, name))
        cap, frame = _open(index, backend)
        if cap is not None:
            print("Camera ready: index=%d backend=%s shape=%s" % (index, name, frame.shape))
            return cap, frame
        print("  no frames")
    return None, None


def save(frame):
    ok = cv2.imwrite(OUT_PATH, frame)
    if not ok:
        print("ERROR: cv2.imwrite failed for", OUT_PATH)
        return False
    print("Saved:", OUT_PATH)
    print("Size: %d bytes" % os.path.getsize(OUT_PATH))
    print("Shape: %s" % (frame.shape,))
    return True


def main():
    print("cv2:", cv2.__version__)
    print("gui_backend:", getattr(cv2, "gui_backend", "unknown"))

    cap, frame = open_camera()
    if cap is None:
        print("ERROR: no camera produced a frame.")
        print("  - grant Camera permission to the app")
        print("  - close other apps that hold the camera")
        print("  - try CV2_CAM_INDEX=1 for the front camera")
        return 1

    if not SHOW:
        # Headless: grab a few frames so exposure settles, keep the last good one.
        for i in range(5):
            ret, candidate = cap.read()
            if ret and candidate is not None and candidate.size:
                frame = candidate
                print("Frame %d: %s" % (i + 1, frame.shape))
            time.sleep(0.1)
        ok = save(frame)
        cap.release()
        return 0 if ok else 1

    # Interactive preview.  Press s to save, q to quit.
    print("Press 's' to save, 'q' to quit.")
    saved = False
    try:
        while True:
            ret, candidate = cap.read()
            if not ret or candidate is None or not candidate.size:
                print("WARNING: empty frame, retrying...")
                time.sleep(0.1)
                continue

            cv2.imshow("Camera", candidate)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("s"):
                saved = save(candidate) or saved
            elif key == ord("q"):
                break
    finally:
        cap.release()
        # The native highgui stub is not built for Android; only Tk/android
        # backends provide destroyAllWindows.
        if getattr(cv2, "gui_backend", "native") != "native":
            try:
                cv2.destroyAllWindows()
            except Exception as exc:
                print("destroyAllWindows warning:", exc)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
