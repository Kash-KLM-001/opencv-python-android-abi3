# Credits

This project is a repackaging effort: OpenCV is the work of the OpenCV
community, and the Android abi3 wheels here were produced by the people below.

## Who did what

Two contributors, one human and one AI agent. The split is deliberately
explicit so the history is auditable:

* **Kash-KLM-001** owns the project, decides what "done" means, and is the only
  one with physical hardware. Every claim about Android behaviour was confirmed
  on a real device by Kash-KLM-001.
* **Big Pickle** (an OpenCode agent) did the build engineering, the native and
  Python implementation, the packaging and the documentation, driven by those
  device results.

The working loop was: device test → real log/traceback → root-cause analysis →
patch → rebuild → device test again. Nothing was marked fixed on the agent's
say-so alone; the camera fixes in particular were only accepted after the
symptom reproduced (and then disappeared) on the phone.

## Project

### Kash-KLM-001 — project owner, device testing, decisions

- Defined the goal: one arm64-v8a `abi3` `cv2` wheel for Android that works on
  Termux, Pydroid 3 and python-for-android/Kivy.
- Set the requirements: OpenCV 4.10 **main + contrib**, no modules removed,
  codecs, MediaNDK, Camera2, bundled Haar/LBP cascades, and an Android
  `imshow`/`waitKey`.
- Chose the toolchain constraints (NDK r29, Python 3.11 build host, API 24)
  and the target runtimes.
- Ran every on-device test, and supplied the real Pydroid tracebacks
  (`_Py_NoneStruct`, then `PyType_GenericAlloc`) that drove the loader design.
- Reported the camera failure precisely (`isOpened()` true, `read()` false) and
  rejected the workaround in favour of a **native** fix after comparing the
  C, looper-pump and Java/pyjnius options.
- Diagnosed the second camera defect (grey, sideways, glitched bottom) and
  supplied the saved JPEG whose 640×720 single-component header proved the
  frames were raw NV21.
- Decided the publish policy (no uploads until explicitly approved) and
  approved each release step.
- Owns and maintains the GitHub repository and release
  ([Kash-KLM-001/opencv-python-android-abi3](https://github.com/Kash-KLM-001/opencv-python-android-abi3)).
- Spotted and patched a real bug in the diagnostic script on device: `say()`
  was called with two arguments but defined with one, which is why the first
  `camera_check.txt` had blank values.

### Big Pickle (OpenCode agent) — build, implementation, packaging, docs

- Prepared and patched the OpenCV + opencv_contrib build for the NDK r29
  Python toolchain (`OPENCV_PYTHON3_FORCE`, NDK r29 linker-flag handling).
- Configured a static, limited-API (`0x03080000`) arm64-v8a build with
  MediaNDK, Camera2 NDK and contrib enabled.
- Wrote `pycompat_shim.h` and the matching `cv2.cpp` changes so the extension
  references only public CPython entry points (`Py_BuildValue`, `Py_DecRef`,
  `Py_IncRef`) instead of private macros.
- Wrote the wheel loader (`cv2/init.py`, `cv2/__init__.py`), including the
  Termux one-time `LD_PRELOAD` re-exec and the Pydroid
  `DT_NEEDED libpython3.13.so` + `$ORIGIN` RUNPATH variant.
- Wrote `make_wheel.py`, the `imshow` backends (pyjnius SurfaceView, Tkinter
  and matplotlib), the smoke tests, and the packaging/documentation scripts.
- Fixed the Camera2 NDK capture path: prepared and pumped an `ALooper` so
  callbacks fire from a plain Python thread, defaulted `fourCC` to BGR instead
  of raw NV21, and applied `ACAMERA_SENSOR_ORIENTATION` so frames arrive
  upright.
- Wrote `CAMERA.md`, `CHANGELOG.md`, `examples/camera_capture.py`,
  `examples/camera_check.py` and the backend/usage documentation.
- Built, stripped, packaged and verified the wheels and checksums, and
  performed the release uploads once approved.

## Upstream and third parties

- **OpenCV 4.10** and **opencv_contrib** — Apache License 2.0,
  © OpenCV Foundation and contributors. This project is an unmodified
  packaging of their work plus the compatibility shim described above.
- **Android NDK r29** and **libc++** — © The Android Open Source Project,
  Apache License 2.0.
- **libjpeg-turbo**, **libpng**, **libtiff**, **libwebp**, **OpenJPEG**,
  **OpenEXR**, **zlib**, **protobuf**, **FlatBuffers**, **ADE**, **quirc**,
  **carotene** — see [`THIRD-PARTY-LICENSES.txt`](THIRD-PARTY-LICENSES.txt)
  and `cv2/LICENSE-3RD-PARTY.txt` inside the wheel.
- **CPython** — © Python Software Foundation, PSF License.
- **NumPy** — BSD-3-Clause, © NumPy developers.
- **matplotlib** — PSF-based matplotlib license, © Matplotlib Development Team.
- **pyjnius** — MIT, © Kivy team.
- **Termux** — © Termux contributors, for the Android-native Python runtime
  used to build and validate the generic wheel.
- **Pydroid 3** (IIEC) — the Android Python runtime targeted by the
  `linux_aarch64` wheel.
- **python-for-android / Kivy** — the packaging target for the SurfaceView
  backend.
- **GitHub** — repository hosting and release distribution.

If you believe an attribution is missing or incorrect, please open an issue.
