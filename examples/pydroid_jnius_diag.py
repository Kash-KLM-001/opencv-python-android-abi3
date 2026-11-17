"""Check whether pyjnius can attach on Pydroid, then try the SurfaceView.

Writes everything to /storage/emulated/0/cv2_jnius_diag.txt because Pydroid
GUI apps usually hide stdout.  Run from the Pydroid **IDE**.

Keep ``from kivy.app import App`` at the top: Pydroid chooses its GUI process
by scanning the script, and its pyjnius only gets a JNIEnv inside a running
Kivy app.
"""

import os
import sys
import traceback

LOG = "/storage/emulated/0/cv2_jnius_diag.txt"
os.environ["CV2_GUI"] = "android"      # force the pyjnius backend
os.environ["CV2_GUI_LOG"] = LOG

from kivy.app import App
from kivy.clock import Clock


def log(text):
    with open(LOG, "a") as handle:
        handle.write(str(text).rstrip() + "\n")
        handle.flush()


open(LOG, "w").close()
log("python: %s" % sys.version.replace("\n", " "))
log("prefix: %s" % sys.prefix)
log("exe: %s" % sys.executable)


class TestApp(App):
    def on_start(self):
        # 1. Can pyjnius attach at all?
        try:
            import jnius

            log("jnius: %s" % jnius.__file__)
            from jnius import autoclass

            log("ActivityThread: %r" % (autoclass("android.app.ActivityThread"),))
            log("JNIUS OK")
        except BaseException:
            log("JNIUS FAILED\n" + traceback.format_exc())

        # 2. cv2's SurfaceView backend.
        try:
            import cv2

            log("cv2: %s" % cv2.__version__)
            log("backend: %s" % cv2.gui_backend)

            img = cv2.imread("/storage/emulated/0/test.jpg")
            log("imread -> %r" % (None if img is None else img.shape,))

            cv2.imshow("frame", img)
            log("imshow returned (SurfaceView should be visible)")
        except BaseException:
            log("CV2 FAILED\n" + traceback.format_exc())

        Clock.schedule_once(lambda dt: self.stop(), 20)


if __name__ == "__main__":
    TestApp().run()
