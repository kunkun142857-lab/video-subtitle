from __future__ import annotations

import multiprocessing
import platform

from gui import SubtitleRemoverGUI


def patch_gui_for_macos() -> None:
    if platform.system() != "Darwin":
        return

    original_init = SubtitleRemoverGUI.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.icon = None

    SubtitleRemoverGUI.__init__ = patched_init


def main() -> None:
    multiprocessing.freeze_support()
    try:
        multiprocessing.set_start_method("spawn")
    except RuntimeError:
        pass

    patch_gui_for_macos()
    gui = SubtitleRemoverGUI()
    gui.run()


if __name__ == "__main__":
    main()
