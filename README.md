# OpenCV 4.10 for Android arm64-v8a (abi3)

Prebuilt **CPython abi3 wheels** of OpenCV **4.10** (main + contrib) for
Android **arm64-v8a**, API 24+, built with the **Android NDK r29**.

The wheel contains a single self-contained `cv2/cv2.abi3.so` (statically
linked OpenCV, codecs and contrib modules) plus Haar/LBP cascade data. It
works on Termux, Pydroid 3 and python-for-android/Kivy, and adds Android-native
`imshow`/`waitKey` backends (pyjnius `SurfaceView` or matplotlib).

## Downloads

Grab the wheel for your runtime from the
[**v4.10.0 release**](https://github.com/Kash-KLM-001/opencv-python-android-abi3/releases/tag/v4.10.0):

| Wheel | Use for | `sysconfig.get_platform()` |
|---|---|---|
| `opencv_python_android-4.10.0-cp38-abi3-android_24_arm64_v8a.whl` | Termux, python-for-android / Kivy | `android-24-arm64_v8a` |
| `opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.whl` | Pydroid 3 | `linux-aarch64` |
| `opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.android_24_arm64_v8a.whl` | both / unknown | either |

Check your runtime with:

```python
import sysconfig
print(sysconfig.get_platform())
```

## Install

```bash
# Termux / python-for-android
pip install opencv_python_android-4.10.0-cp38-abi3-android_24_arm64_v8a.whl

# Pydroid 3
pip install opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.whl
```

If pip rejects the platform tag, force it:

```bash
pip install --no-deps \
  --platform linux_aarch64 --python-version 3.11 \
  --implementation cp --abi abi3 \
  opencv_python_android-4.10.0-cp38-abi3-linux_aarch64.whl
```

Requirements: **NumPy >= 1.25**. One binary runs on Python 3.8+ (Limited API
`0x03080000`). Pydroid ships its own OpenCV; if `import cv2` resolves to that
copy, remove/rename it or install into a virtualenv.

### Termux note

Termux keeps `libpython` out of the namespace used to `dlopen` extensions.
`cv2/init.py` automatically re-executes the interpreter once with
`LD_PRELOAD` set when the first load fails, so normal scripts and
`python -c ...` work without manual flags. Piped-stdin scripts
(`python - <<EOF`) cannot be re-executed; use:

```bash
LD_PRELOAD=$PREFIX/lib/libpython3.14.so python -
```

Set `CV2_PRELOAD_REEXEC=1` to disable the automatic re-exec.

## What is included

- OpenCV **4.10** main + contrib modules (core, imgproc, imgcodecs, videoio,
  features2d, calib3d, dnn, gapi, xfeatures2d, ximgproc, aruco, tracking,
  stitching, text, face, etc.)
- **17 Haar cascades** (`cv2.data.haarcascades`) and **5 LBP cascades**
  (`cv2.data.lbpcascades`), directly loadable with `cv2.CascadeClassifier`
- Bundled codecs: libjpeg-turbo, libpng, libtiff, libwebp, OpenJPEG, OpenEXR,
  protobuf, FlatBuffers, ADE, quirc, zlib, carotene NEON HAL
- **MediaNDK** decode/encode and **Camera2 NDK** capture
  (`cv2.CAP_ANDROID` / `ANDROID_NATIVE`)
- `libc++_static` (no `libc++_shared.so` dependency)

Only Android system libraries are required at runtime: `libandroid.so`,
`liblog.so`, `libmediandk.so`, `libcamera2ndk.so`, `libz.so`, `libdl.so`,
`libm.so`, `libc.so`. No `libpython` dependency.

## `imshow` / `waitKey`

The build has no native GUI, so the wheel replaces the highgui functions.
Select a backend with `CV2_GUI`:

| `CV2_GUI` | Backend |
|---|---|
| `auto` (default) | pyjnius `SurfaceView` on Android, else matplotlib `pyplot.ion()` |
| `android` | native `SurfaceView` via pyjnius (GPU composited, Kivy live video) |
| `mpl` | matplotlib `ion()` figures |
| `native` | compiled headless highgui, no override |

```python
import cv2

cap = cv2.VideoCapture(0, cv2.CAP_ANDROID)
while True:
    ok, frame = cap.read()
    if not ok:
        break
    cv2.imshow("camera", frame)      # SurfaceView
    if cv2.waitKey(1) == 27:
        break
cv2.destroyAllWindows()
cap.release()
```

See [`WHEEL_USAGE.md`](WHEEL_USAGE.md) for backend details, `pyjnius` knobs and
rebuild commands.

## Verified

On Termux (Android, Python 3.14.6, NumPy 2.5.4), with `LD_PRELOAD` unset:

- `cv2.__version__ == 4.10.0`
- core, imgproc, features2d, dnn
- PNG/JPEG encode + decode round-trip
- contrib `xfeatures2d`, `ximgproc`
- videoio registry includes `ANDROID_NATIVE` (MediaNDK)
- 17 Haar + 5 LBP cascades present and `CascadeClassifier` loads a cascade
- no CPython private-symbol references; only `Py_BuildValue`, `Py_DecRef`,
  `Py_IncRef` (public stable ABI) remain undefined

## Build

Built from OpenCV 4.10 + opencv_contrib with:

- `BUILD_SHARED_LIBS=OFF`, `ANDROID_STL=c++_static`
- `PYTHON3_LIMITED_API=ON`, `PYTHON3_LIMITED_API_VERSION=0x03080000`
- `WITH_ANDROID_MEDIANDK=ON`, `WITH_ANDROID_NATIVE_CAMERA=ON`
- Android NDK r29, API 24, arm64-v8a

## License

OpenCV is licensed under the **Apache License 2.0**; see [`LICENSE`](LICENSE).
Bundled third-party components retain their own licenses, reproduced in
[`THIRD-PARTY-LICENSES.txt`](THIRD-PARTY-LICENSES.txt) and inside the wheel as
`cv2/LICENSE-3RD-PARTY.txt`.
