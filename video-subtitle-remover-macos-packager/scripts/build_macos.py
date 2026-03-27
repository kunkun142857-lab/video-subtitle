from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from fsplit.filesplit import Filesplit


APP_NAME = "Video Subtitle Remover"
DEFAULT_REPO = "YaoFANGUK/video-subtitle-remover"


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print(f"$ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, env=env, check=True)


def download_upstream_tarball(repo: str, ref: str, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    tarball_path = destination / f"{repo.replace('/', '-')}-{ref}.tar.gz"
    url = f"https://codeload.github.com/{repo}/tar.gz/{ref}"
    print(f"Downloading upstream source from {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "video-subtitle-remover-macos-packager"})
    with urllib.request.urlopen(request) as response, tarball_path.open("wb") as output:
        shutil.copyfileobj(response, output)
    return tarball_path


def extract_upstream_tarball(tarball_path: Path, destination: Path) -> Path:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball_path, "r:gz") as archive:
        archive.extractall(destination, filter="data")
    extracted_roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(extracted_roots) != 1:
        raise RuntimeError(f"Expected a single extracted root, got: {extracted_roots}")
    return extracted_roots[0]


def extract_version(source_root: Path) -> str:
    config_text = (source_root / "backend" / "config.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION = "([^"]+)"', config_text, re.MULTILINE)
    if not match:
        raise RuntimeError("Failed to extract VERSION from backend/config.py")
    return match.group(1)


def merge_split_file(directory: Path, target_name: str, cleanup_patterns: list[str]) -> None:
    target_path = directory / target_name
    if not target_path.exists():
        print(f"Merging split files into {target_path}")
        Filesplit().merge(input_dir=str(directory))
    if not target_path.exists():
        raise RuntimeError(f"Expected merged file to exist after merge: {target_path}")
    for pattern in cleanup_patterns:
        for path in directory.glob(pattern):
            if path.is_file():
                path.unlink()


def prepare_models(source_root: Path) -> None:
    merge_split_file(
        source_root / "backend" / "models" / "big-lama",
        "big-lama.pt",
        ["big-lama_*.pt", "fs_manifest.csv"],
    )
    merge_split_file(
        source_root / "backend" / "models" / "V4" / "ch_det",
        "inference.pdiparams",
        ["inference_*.pdiparams", "fs_manifest.csv"],
    )
    merge_split_file(
        source_root / "backend" / "models" / "video",
        "ProPainter.pth",
        ["ProPainter_*.pth", "fs_manifest.csv"],
    )


def patch_backend_config_for_macos(source_root: Path) -> None:
    config_path = source_root / "backend" / "config.py"
    config_text = config_path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"if 'ffmpeg\.exe' not in os\.listdir\(os\.path\.join\(BASE_DIR, '', 'ffmpeg', 'win_x64'\)\):\n"
        r"\s+fs = Filesplit\(\)\n"
        r"\s+fs\.merge\(input_dir=os\.path\.join\(BASE_DIR, '', 'ffmpeg', 'win_x64'\)\)\n"
        r"# 将ffmpeg添加可执行权限\n"
        r"os\.chmod\(FFMPEG_PATH, stat\.S_IRWXU \+ stat\.S_IRWXG \+ stat\.S_IRWXO\)\n?"
    )
    replacement = (
        "if sys_str == \"Windows\" and 'ffmpeg.exe' not in os.listdir(os.path.join(BASE_DIR, '', 'ffmpeg', 'win_x64')):\n"
        "    fs = Filesplit()\n"
        "    fs.merge(input_dir=os.path.join(BASE_DIR, '', 'ffmpeg', 'win_x64'))\n"
        "# 将ffmpeg添加可执行权限\n"
        "if os.path.exists(FFMPEG_PATH):\n"
        "    os.chmod(FFMPEG_PATH, stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO)\n"
    )
    config_text, replaced = pattern.subn(replacement, config_text, count=1)

    if replaced != 1:
        raise RuntimeError("Failed to patch backend/config.py for macOS ffmpeg handling.")

    config_path.write_text(config_text, encoding="utf-8")


def ensure_macos_ffmpeg_executable(source_root: Path) -> None:
    ffmpeg_path = source_root / "backend" / "ffmpeg" / "macos" / "ffmpeg"
    ffmpeg_path.chmod(0o755)


def create_icns(source_root: Path, output_path: Path) -> None:
    source_image = source_root / "design" / "demo.png"
    if not source_image.exists():
        raise RuntimeError(f"Missing source image for icon generation: {source_image}")

    with tempfile.TemporaryDirectory(prefix="vsr-iconset-") as temp_dir:
        iconset_dir = Path(temp_dir) / "VideoSubtitleRemover.iconset"
        iconset_dir.mkdir()
        icon_specs = [
            (16, "icon_16x16.png"),
            (32, "icon_16x16@2x.png"),
            (32, "icon_32x32.png"),
            (64, "icon_32x32@2x.png"),
            (128, "icon_128x128.png"),
            (256, "icon_128x128@2x.png"),
            (256, "icon_256x256.png"),
            (512, "icon_256x256@2x.png"),
            (512, "icon_512x512.png"),
            (1024, "icon_512x512@2x.png"),
        ]
        for size, name in icon_specs:
            run(
                [
                    "sips",
                    "-z",
                    str(size),
                    str(size),
                    str(source_image),
                    "--out",
                    str(iconset_dir / name),
                ]
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_path)])


def build_app(root_dir: Path, source_root: Path, icon_path: Path, arch: str, version: str) -> Path:
    dist_dir = root_dir / "dist"
    work_dir = root_dir / "build" / "pyinstaller-work"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["VSR_SOURCE_DIR"] = str(source_root)
    env["VSR_APP_ICON"] = str(icon_path)
    env["VSR_APP_NAME"] = APP_NAME
    env["VSR_BUNDLE_ID"] = "uk.yaofang.video-subtitle-remover"
    env["VSR_DIST_DIR"] = str(dist_dir)
    env["VSR_BUILD_DIR"] = str(work_dir)
    env["VSR_TARGET_ARCH"] = arch
    env["VSR_APP_VERSION"] = version

    spec_path = root_dir / "build" / "macos" / "VideoSubtitleRemover.spec"
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
            str(spec_path),
        ],
        cwd=root_dir,
        env=env,
    )

    app_path = dist_dir / f"{APP_NAME}.app"
    if not app_path.exists():
        raise RuntimeError(f"Expected app bundle to exist after build: {app_path}")
    return app_path


def sign_if_requested(app_path: Path, root_dir: Path) -> bool:
    identity = os.environ.get("APPLE_SIGNING_IDENTITY", "").strip()
    if not identity:
        print("APPLE_SIGNING_IDENTITY not set, skipping codesign.")
        return False

    entitlements_path = root_dir / "build" / "macos" / "entitlements.plist"
    run(
        [
            "codesign",
            "--force",
            "--deep",
            "--options",
            "runtime",
            "--entitlements",
            str(entitlements_path),
            "--sign",
            identity,
            str(app_path),
        ]
    )
    run(["codesign", "--verify", "--deep", "--verbose=2", str(app_path)])
    return True


def create_dmg(root_dir: Path, app_path: Path, version: str, arch: str) -> Path:
    release_dir = root_dir / "release"
    stage_dir = release_dir / "dmg-stage"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    stage_dir.mkdir(parents=True, exist_ok=True)

    staged_app_path = stage_dir / app_path.name
    shutil.copytree(app_path, staged_app_path)

    dmg_path = release_dir / f"vsr-v{version}-macos-{arch}.dmg"
    env = os.environ.copy()
    env["VSR_DMG_APP_NAME"] = APP_NAME
    env["VSR_DMG_STAGE_DIR"] = str(stage_dir)

    settings_path = root_dir / "build" / "macos" / "dmg_settings.py"
    run(
        [
            sys.executable,
            "-m",
            "dmgbuild",
            "-s",
            str(settings_path),
            f"{APP_NAME} {version}",
            str(dmg_path),
        ],
        cwd=root_dir,
        env=env,
    )
    return dmg_path


def sign_dmg_if_requested(dmg_path: Path) -> bool:
    identity = os.environ.get("APPLE_SIGNING_IDENTITY", "").strip()
    if not identity:
        return False
    run(["codesign", "--force", "--sign", identity, str(dmg_path)])
    return True


def notarize_dmg_if_requested(dmg_path: Path) -> bool:
    apple_id = os.environ.get("APPLE_ID", "").strip()
    password = os.environ.get("APPLE_APP_SPECIFIC_PASSWORD", "").strip()
    team_id = os.environ.get("APPLE_TEAM_ID", "").strip()

    if not all([apple_id, password, team_id]):
        print("Apple notarization credentials are incomplete, skipping notarization.")
        return False

    run(
        [
            "xcrun",
            "notarytool",
            "submit",
            str(dmg_path),
            "--apple-id",
            apple_id,
            "--password",
            password,
            "--team-id",
            team_id,
            "--wait",
        ]
    )
    run(["xcrun", "stapler", "staple", str(dmg_path)])
    return True


def write_build_info(
    release_dir: Path,
    *,
    repo: str,
    ref: str,
    version: str,
    arch: str,
    signed: bool,
    notarized: bool,
    app_path: Path,
    dmg_path: Path,
) -> None:
    build_info = "\n".join(
        [
            f"repo={repo}",
            f"ref={ref}",
            f"version={version}",
            f"arch={arch}",
            f"signed={str(signed).lower()}",
            f"notarized={str(notarized).lower()}",
            f"app={app_path}",
            f"dmg={dmg_path}",
        ]
    )
    (release_dir / "build-info.txt").write_text(build_info + "\n", encoding="utf-8")


def detect_arch() -> str:
    machine = platform.machine().lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    return machine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a macOS .app/.dmg for video-subtitle-remover.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo in owner/name format.")
    parser.add_argument("--ref", default="main", help="Git ref, tag, or branch to build from.")
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Optional cache directory for downloaded upstream tarballs.",
    )
    return parser.parse_args()


def main() -> None:
    if platform.system() != "Darwin":
        raise SystemExit("This builder currently supports running only on macOS.")
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required for this builder.")

    args = parse_args()
    root_dir = Path(__file__).resolve().parents[1]
    cache_dir = Path(args.cache_dir) if args.cache_dir else root_dir / ".cache"
    source_parent = root_dir / "build" / "upstream-src"
    arch = detect_arch()

    tarball_path = download_upstream_tarball(args.repo, args.ref, cache_dir)
    source_root = extract_upstream_tarball(tarball_path, source_parent)
    version = extract_version(source_root)

    prepare_models(source_root)
    patch_backend_config_for_macos(source_root)
    ensure_macos_ffmpeg_executable(source_root)

    icon_path = root_dir / "build" / "macos" / "VideoSubtitleRemover.icns"
    create_icns(source_root, icon_path)

    app_path = build_app(root_dir, source_root, icon_path, arch, version)
    signed = sign_if_requested(app_path, root_dir)

    dmg_path = create_dmg(root_dir, app_path, version, arch)
    if signed:
        sign_dmg_if_requested(dmg_path)
    notarized = notarize_dmg_if_requested(dmg_path)

    release_dir = root_dir / "release"
    final_app_path = release_dir / app_path.name
    if final_app_path.exists():
        shutil.rmtree(final_app_path)
    shutil.copytree(app_path, final_app_path)

    write_build_info(
        release_dir,
        repo=args.repo,
        ref=args.ref,
        version=version,
        arch=arch,
        signed=signed,
        notarized=notarized,
        app_path=final_app_path,
        dmg_path=dmg_path,
    )

    print("")
    print("Build completed.")
    print(f"App bundle: {final_app_path}")
    print(f"DMG: {dmg_path}")


if __name__ == "__main__":
    main()
