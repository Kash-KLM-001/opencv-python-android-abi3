"""Show an image on Pydroid 3 through pyjnius (Android SurfaceView).

Run this from the Pydroid **IDE** (play button), not its Terminal.  Pydroid
only exposes a ``JNIEnv`` to its GUI process, which it selects from the
script's imports, and its pyjnius expects ``import kivy`` **before**
``import jnius``.  Keep ``import kivy`` the very first line: moving it after
``import cv2`` is too late.
"""

import kivy  # noqa: F401  # must precede cv2/jnius on Pydroid
import os

os.environ["CV2_GUI"] = "android"  # choose pyjnius before importing cv2

import cv2

IMAGE = "/storage/emulated/0/test.jpg"  # change to your file

print("backend:", cv2.gui_backend)
img = cv2.imread(IMAGE)
if img is None:
    raise SystemExit("cannot read %s" % IMAGE)
print("image:", img.shape)

cv2.imshow("frame", img)
print("press BACK / a key to close")
cv2.waitKey(0)
cv2.destroyAllWindows()
