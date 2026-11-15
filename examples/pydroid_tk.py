"""Show an image on Pydroid 3 through Tkinter (works without pyjnius/Kivy).

Run this from the Pydroid **IDE** (play button), not its Terminal.
``CV2_GUI=auto`` picks this backend on Pydroid already; the variable is set
explicitly here so the intent is obvious.
"""

import os

os.environ["CV2_GUI"] = "tk"

import cv2

IMAGE = "/storage/emulated/0/test.jpg"  # change to your file

print("backend:", cv2.gui_backend)
img = cv2.imread(IMAGE)
if img is None:
    raise SystemExit("cannot read %s" % IMAGE)
print("image:", img.shape)

cv2.imshow("frame", img)
print("press a key / close the window")
cv2.waitKey(0)
cv2.destroyAllWindows()
