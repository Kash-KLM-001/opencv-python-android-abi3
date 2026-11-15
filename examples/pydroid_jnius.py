"""Show an image on Pydroid 3 through pyjnius (Android SurfaceView).

Run this from the Pydroid **IDE** (play button), not its Terminal.

Pydroid's pyjnius has no ``JNIEnv`` in a plain script: the JVM is attached to
the process that Pydroid starts for a **Kivy app**, and it only becomes usable
once Kivy is running.  So:

* keep ``from kivy.app import App`` at the top of the file (Pydroid scans the
  source for it to pick its GUI process), and
* create the SurfaceView from ``App.on_start``, not at import time.

Do not call ``cv2.waitKey(0)`` here: it would block Kivy's event loop.  The
SurfaceView keeps showing the last frame on its own.
"""

import os

os.environ["CV2_GUI"] = "android"  # before importing cv2

from kivy.app import App
from kivy.clock import Clock

import cv2

IMAGE = "/storage/emulated/0/test.jpg"  # change to your file


class TestApp(App):
    def on_start(self):
        print("backend:", cv2.gui_backend)
        img = cv2.imread(IMAGE)
        if img is None:
            print("cannot read %s" % IMAGE)
            self.stop()
            return
        print("image:", img.shape)
        cv2.imshow("frame", img)  # pyjnius SurfaceView over the Kivy window
        Clock.schedule_once(self._close, 30)

    def _close(self, _dt):
        cv2.destroyAllWindows()
        self.stop()


if __name__ == "__main__":
    TestApp().run()
