# `opencv-python-android` wheel

OpenCV 4.10 (main + contrib) for Android **arm64-v8a**, API 24+, packaged as a
single CPython **abi3** wheel with an Android-native `imshow`.

```
output/opencv_python_android-4.10.0-cp38-abi3-android_24_arm64_v8a.whl   # Termux / p4a
output/opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.whl         # Pydroid 3
output/opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.android_24_arm64_v8a.whl  # both
```

## Install

On an Android-native Python runtime (Kivy/python-for-android, Chaquopy,
Pydroid, Termux):

```bash
pip install opencv_python_android-4.10.0-cp38-abi3-android_24_arm64_v8a.whl
```

### Which platform tag?

Different Android Python runtimes report different tags:

| Runtime | `sysconfig.get_platform()` | wheel to use |
|---|---|---|
| Termux (modern pip) | `android-24-arm64_v8a` | `...android_24_arm64_v8a.whl` |
| python-for-android | `android_24_arm64_v8a` | `...android_24_arm64_v8a.whl` |
| **Pydroid 3** | **`linux-aarch64`** | **`...linux_aarch64.whl`** |
| unknown / mixed | – | `...linux_aarch64.android_24_arm64_v8a.whl` |

Check in the target runtime:

```python
import sysconfig; print(sysconfig.get_platform())
```

The dual-tag wheel declares both platforms in its filename and `WHEEL`
metadata, so pip accepts it in Termux and Pydroid alike.

If the host pip rejects the tag, force it:

```bash
pip install --no-deps \
  --platform linux_aarch64 --python-version 3.11 \
  --implementation cp --abi abi3 \
  opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.whl
```

### Pydroid 3

Pydroid reports `linux_aarch64`, so install the tagged wheel:

```bash
pip install /storage/emulated/0/opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.whl
```

Pydroid does **not** expose CPython symbols to extension modules (`dlopen`
cannot resolve even public ones such as `PyType_GenericAlloc`). The Pydroid
wheel therefore ships a different `cv2/cv2.abi3.so` that declares:

```
NEEDED  libpython3.13.so
RUNPATH $ORIGIN/../../../../lib
```

`$ORIGIN` is `.../lib/python3.13/site-packages/cv2`, so the RUNPATH resolves to
Pydroid's own `<python-root>/lib/libpython3.13.so` — the exact library already
loaded by the running interpreter, not a copy. If your Pydroid updates to a
different Python (say 3.16), either use the generic wheel with the manual
`LD_PRELOAD` described below, or rebuild with the matching `CV2_SO` variant.

Pydroid ships its own OpenCV build; if `import cv2` still resolves to that
one, remove/rename it first or install this wheel into a virtualenv. The
NumPy in Pydroid must be **1.25 or newer**.

Dependencies: `numpy>=1.25`, `matplotlib>=3.5`. One binary runs on
Python 3.8+ (limited API `0x03080000`).

## `imshow` backends

This OpenCV build has no native GUI (`GUI: NONE`), so the wheel replaces the
highgui functions. Pick a backend with `CV2_GUI`:

| `CV2_GUI` | Backend | Use case |
|---|---|---|
| `auto` (default) | pyjnius/SurfaceView on Android, else matplotlib | normal |
| `android` | native `SurfaceView` via pyjnius (GPU composited) | Kivy live video |
| `mpl` | matplotlib `pyplot.ion()` figures | notebooks / IDE |
| `native` | compiled (headless) highgui, no override | headless |

`cv2.gui_backend` reports what was selected.

### Android / Kivy (fast path)

`pyjnius` is available automatically inside python-for-android. Frames are
converted to a reusable `ARGB_8888` `Bitmap` and blitted into a
`SurfaceView`, with Android key codes mapped to `cv2.waitKey` values.

```python
import cv2

cap = cv2.VideoCapture(0, cv2.CAP_ANDROID)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    cv2.imshow("camera", frame)          # SurfaceView, no matplotlib
    if cv2.waitKey(1) == 27:             # BACK / ESC
        break

cv2.destroyAllWindows()
cap.release()
```

Environment knobs:

* `CV2_ACTIVITY_CLASS` – activity class (default
  `org.kivy.android.PythonActivity`).
* `CV2_ANDROID_VIEW=surface|image` – `surface` (default, fastest) or
  `ImageView` + `Bitmap`.

### Matplotlib

```python
import cv2
img = cv2.imread("photo.jpg")
cv2.imshow("photo", img)     # BGR/BGRA converted, plt.ion() enabled
cv2.waitKey(0)
```

Centered 2D/3D images, gray/color, 8/16-bit and float (0..1 or 0..255) inputs
are supported. Key events feed `waitKey`.

## Termux / Pydroid note

Older builds of this wheel referenced CPython private symbols such as
`_Py_NoneStruct`, which some Android Python runtimes (notably Pydroid) do not
expose to extensions:

```
ImportError: dlopen failed: cannot locate symbol "_Py_NoneStruct"
```

The extension itself is built with a small compatibility shim
(`pycompat_shim.h`) that redirects private macros to public/stable-ABI entry
points, so it references only `Py_BuildValue`, `Py_DecRef`, and `Py_IncRef`
(no `libpython` dependency). Nothing in OpenCV is removed by the shim.

Runtime behavior:

* **Pydroid 3** does not export CPython symbols to `dlopen`ed extensions at
  all. The `linux_aarch64` wheel handles this with a hard
  `DT_NEEDED libpython3.13.so` plus the relative RUNPATH
  `$ORIGIN/../../../../lib`, so no `LD_PRELOAD` or re-exec is involved.
* **Termux** keeps `libpython` out of the namespace used for extension
  `dlopen` and bionic cannot promote an already-loaded library with
  `RTLD_GLOBAL`. The generic wheel stays free of any `libpython` dependency;
  `cv2/init.py` re-executes the interpreter once with `LD_PRELOAD` set when
  the first load fails. This is transparent for normal scripts and
  `python -c`.
* Piped-stdin scripts (`python - <<EOF` / `python -`) cannot be re-executed
  because the input is already consumed; launch those with
  `LD_PRELOAD=$PREFIX/lib/libpython3.14.so python -`.
* Set `CV2_PRELOAD_REEXEC=1` to suppress the automatic re-exec.

## What is inside

* OpenCV 4.10 main + contrib modules, statically linked into `cv2/cv2.abi3.so`
* **17 Haar cascades** (`cv2.data.haarcascades`) and **5 LBP cascades**
  (`cv2.data.lbpcascades`), loadable directly with `cv2.CascadeClassifier`
* libjpeg-turbo, libpng, libtiff, libwebp, OpenJPEG, OpenEXR, protobuf,
  FlatBuffers, ADE, quirc, zlib, carotene (NEON HAL)
* MediaNDK video decode/encode and Camera2 NDK capture
* `libc++_static` (no `libc++_shared.so` dependency)

Only Android system libraries are needed at runtime: `libandroid.so`,
`liblog.so`, `libmediandk.so`, `libcamera2ndk.so`, `libz.so`, `libdl.so`,
`libm.so`, `libc.so`.

## Rebuild the wheel

```bash
# requires output/cv2.abi3.so from build_abi3.sh
PY=android/androif-ndk-r29/toolchains/llvm/prebuilt/linux-x86_64/python3/bin/python3.11

$PY make_wheel.py                                                   # Termux / p4a
CV2_WHEEL_PLATFORM=linux_aarch64 $PY make_wheel.py                  # Pydroid 3
CV2_WHEEL_PLATFORM=linux_aarch64.android_24_arm64_v8a $PY make_wheel.py  # both
```

For the Pydroid wheel, first create the linked extension variant:

```bash
cp output/cv2.abi3.so output/cv2.abi3.pydroid.so
patchelf --set-rpath '$ORIGIN/../../../../lib' \
         --add-needed libpython3.13.so output/cv2.abi3.pydroid.so
CV2_SO=output/cv2.abi3.pydroid.so \
CV2_WHEEL_PLATFORM=linux_aarch64 $PY make_wheel.py
```

`CV2_WHEEL_PLATFORM` accepts comma- or dot-separated platform tags; each tag
is written to the wheel's `WHEEL` metadata.
