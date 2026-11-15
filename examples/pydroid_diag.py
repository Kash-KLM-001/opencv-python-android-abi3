"""Write Tk + cv2 diagnostics to /storage/emulated/0/cv2_diag.txt.

Pydroid GUI apps often show no stdout in the IDE, so everything (including
tracebacks) goes to a file you can open with any file manager.

It first opens a plain Tkinter window for 8 s ("TK WORKS"), then asks cv2 for a
Tk window showing /storage/emulated/0/test.jpg.  Run from the Pydroid **IDE**.
"""

import os
import sys
import traceback

LOG = "/storage/emulated/0/cv2_diag.txt"
os.environ["CV2_GUI"] = "tk"          # try the Tk backend
os.environ["CV2_GUI_LOG"] = LOG       # wheel logs backend selection here

import tkinter as tk  # noqa: F401  # literal import: Pydroid picks GUI mode from it


def log(text):
    with open(LOG, "a") as handle:
        handle.write(str(text).rstrip() + "\n")
        handle.flush()


open(LOG, "w").close()
log("python: %s" % sys.version.replace("\n", " "))
log("prefix: %s" % sys.prefix)
log("exe: %s" % sys.executable)

# 1. Plain Tkinter: does *any* window open on this device?
try:
    root = tk.Tk()
    root.title("Tk test")
    root.update()
    log("tk ok: %dx%d" % (root.winfo_screenwidth(), root.winfo_screenheight()))
    tk.Label(root, text="TK WORKS", font=("Arial", 40)).pack()
    root.update()
    root.after(8000, root.destroy)
    root.mainloop()
    log("tk window closed")
except BaseException:
    log("tk FAILED\n" + traceback.format_exc())

# 2. cv2's Tk backend on the same image.
try:
    import cv2

    log("cv2: %s  %s" % (cv2.__version__, cv2.__file__))
    log("backend: %s" % cv2.gui_backend)

    path = "/storage/emulated/0/test.jpg"
    img = cv2.imread(path)
    log("imread %s -> %r" % (path, None if img is None else img.shape))

    cv2.imshow("frame", img)
    log("imshow returned; holding the window for 10 s")
    cv2.waitKey(10000)
    cv2.destroyAllWindows()
    log("done")
except BaseException:
    log("cv2 FAILED\n" + traceback.format_exc())

log("log written to %s" % LOG)
