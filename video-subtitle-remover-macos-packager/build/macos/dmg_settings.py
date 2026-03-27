import os
from pathlib import Path


app_name = os.environ["VSR_DMG_APP_NAME"]
stage_dir = Path(os.environ["VSR_DMG_STAGE_DIR"]).resolve()

application = f"{app_name}.app"
files = [str(stage_dir / application)]
symlinks = {"Applications": "/Applications"}

format = "UDZO"
default_view = "icon-view"
show_toolbar = False
show_status_bar = False
show_tab_view = False
show_pathbar = False
show_sidebar = False
window_rect = ((120, 120), (640, 400))
icon_size = 128
text_size = 14

icon_locations = {
    application: (180, 190),
    "Applications": (460, 190),
}
