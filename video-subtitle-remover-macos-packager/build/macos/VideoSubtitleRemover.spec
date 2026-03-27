# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


project_root = Path(__file__).resolve().parents[2]
source_root = Path(os.environ["VSR_SOURCE_DIR"]).resolve()
dist_root = Path(os.environ["VSR_DIST_DIR"]).resolve()
work_root = Path(os.environ["VSR_BUILD_DIR"]).resolve()
app_name = os.environ.get("VSR_APP_NAME", "Video Subtitle Remover")
app_icon = os.environ.get("VSR_APP_ICON")
bundle_identifier = os.environ.get("VSR_BUNDLE_ID", "uk.yaofang.video-subtitle-remover")
app_version = os.environ.get("VSR_APP_VERSION", "1.0")

datas = []
binaries = []
hiddenimports = []


def include_tree(root: Path, destination_prefix: str):
    results = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        target_dir = Path(destination_prefix) / file_path.relative_to(root).parent
        results.append((str(file_path), str(target_dir)))
    return results


def add_package(package_name: str) -> None:
    package_datas, package_binaries, package_hiddenimports = collect_all(package_name)
    datas.extend(package_datas)
    binaries.extend(package_binaries)
    hiddenimports.extend(package_hiddenimports)
    try:
        datas.extend(copy_metadata(package_name))
    except Exception:
        pass


datas.extend(include_tree(source_root / "backend" / "models", "backend/models"))
datas.extend(include_tree(source_root / "backend" / "ffmpeg" / "macos", "backend/ffmpeg/macos"))

for package in [
    "albumentations",
    "av",
    "filesplit",
    "imgaug",
    "onnxruntime",
    "paddle",
    "paddle2onnx",
    "paddleocr",
    "shapely",
    "skimage",
    "torch",
    "torchvision",
]:
    add_package(package)

hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    [str(project_root / "build" / "macos" / "app_launcher.py")],
    pathex=[str(project_root), str(source_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=app_icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)
app = BUNDLE(
    coll,
    name=f"{app_name}.app",
    icon=app_icon,
    bundle_identifier=bundle_identifier,
    info_plist={
        "CFBundleName": app_name,
        "CFBundleDisplayName": app_name,
        "CFBundleShortVersionString": app_version,
        "CFBundleVersion": app_version,
        "NSHighResolutionCapable": True,
    },
)
