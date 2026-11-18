"""Diagnose camera capture on the device and write the result to a text file.

Pydroid hides stdout, so everything is mirrored to
/storage/emulated/0/camera_check.txt.

Run from the Pydroid IDE (or Terminal - this script needs no GUI):

    python /storage/emulated/0/camera_check.py

It answers:

1. Which wheel is installed, and does it contain the Camera2 looper fix?
2. Can the camera be opened?
3. Does ``read()`` return a frame, how long does it take, and is it a proper
   colour BGR image (not a raw NV21 buffer)?
"""

import hashlib
import os
import sys
import time

os.environ["CV2_GUI"] = "native"

OUT_TXT = "/storage/emulated/0/camera_check.txt"
OUT_JPG = "/storage/emulated/0/camera_check.jpg"
_lines = []


def say(*args):
    """print() with any number of arguments, mirrored to the report file."""
    text = " ".join(str(a) for a in args)
    print(text)
    _lines.append(text)


def flush():
    try:
        with open(OUT_TXT, "w") as fh:
            fh.write("\n".join(_lines) + "\n")
    except Exception as exc:
        print("cannot write %s: %s" % (OUT_TXT, exc))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_frame(frame):
    """Report shape/colour and flag the raw-NV21 symptom explicitly."""
    h, w = frame.shape[:2]
    channels = 1 if frame.ndim == 2 else frame.shape[2]
    say("  shape:", frame.shape, "dtype:", frame.dtype)
    say("  channels:", channels)
    say("  is colour BGR:", channels == 3)
    if channels == 1 and abs(h - w * 1.5) < 2:
        say("  WARNING: this is a raw NV21 buffer, not a BGR frame")
        say("           (old wheel without the BGR default / orientation fix)")
    if channels == 3:
        mean = frame.reshape(-1, 3).mean(axis=0)
        say("  mean BGR:", [round(float(v), 1) for v in mean])
        say("  portrait:", h > w)


def main():
    say("time:", time.strftime("%Y-%m-%d %H:%M:%S"))
    say("python:", sys.version.replace("\n", " "))
    say("platform:", sys.platform)

    import cv2

    say("cv2:", cv2.__version__)
    say("cv2 package:", os.path.dirname(cv2.__file__))
    say("gui_backend:", getattr(cv2, "gui_backend", "unknown"))

    pkg_dir = os.path.dirname(cv2.__file__)
    so = os.path.join(pkg_dir, "cv2.abi3.so")
    if os.path.exists(so):
        say("cv2.abi3.so size:", os.path.getsize(so))
        say("cv2.abi3.so sha256:", sha256(so))
        try:
            with open(so, "rb") as fh:
                blob = fh.read()
            say("camera looper fix present:", b"Cannot prepare camera looper" in blob)
            say("camera BGR default present:", b"Sensor orientation: %d degrees" in blob)
            del blob
        except Exception as exc:
            say("cannot scan .so:", exc)
    else:
        say("cv2.abi3.so NOT FOUND next to", pkg_dir)

    say("")
    say("--- camera ---")
    candidates = [
        (0, None), (0, cv2.CAP_ANDROID),
        (1, None), (1, cv2.CAP_ANDROID),
    ]
    worked = False
    for index, backend in candidates:
        label = "default" if backend is None else "CAP_ANDROID"
        say("")
        say("trying index=%d backend=%s" % (index, label))
        try:
            cap = (cv2.VideoCapture(index) if backend is None
                   else cv2.VideoCapture(index, backend))
        except Exception as exc:
            say("  VideoCapture raised:", repr(exc))
            continue

        say("  isOpened:", cap.isOpened())
        if not cap.isOpened():
            cap.release()
            continue

        say("  FOURCC:", hex(int(cap.get(cv2.CAP_PROP_FOURCC))))
        say("  orientation meta:", cap.get(cv2.CAP_PROP_ORIENTATION_META))

        t0 = time.time()
        ret, frame = cap.read()
        dt = time.time() - t0
        say("  read(): ret=%s  took=%.2fs" % (ret, dt))
        if ret and frame is not None:
            describe_frame(frame)
            ok = cv2.imwrite(OUT_JPG, frame)
            say("  imwrite:", ok, OUT_JPG)
            worked = True
        cap.release()
        if worked:
            break

    say("")
    say("RESULT:", "camera works" if worked else "camera FAILED")
    if not worked:
        say("hints:")
        say("  - reinstall the latest wheel (looper + BGR + orientation fix)")
        say("  - grant Camera permission, close other camera apps")
        say("  - try CV2_CAM_INDEX=1 for the front camera")
        say("  - in a plain script, read() timing out at 2.00s means no looper")

    return 0 if worked else 1


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        import traceback
        say("")
        say(traceback.format_exc())
        code = 2
    flush()
    print("wrote", OUT_TXT)
    sys.exit(code)
