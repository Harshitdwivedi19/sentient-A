"""
scripts/build_desktop_exe.py

Compiles the Desktop Application into a standalone Windows .exe package
using PyInstaller.

Output:
- dist/SentimentTrajectoryStudio/SentimentTrajectoryStudio.exe
- dist/SentimentTrajectoryStudio_Windows_x64.zip
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_desktop_app():
    print("=" * 70)
    print("BUILDING DESKTOP APPLICATION (.EXE) FOR WINDOWS")
    print("=" * 70)

    dist_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build"
    app_dir = dist_dir / "SentimentTrajectoryStudio"

    entry_script = PROJECT_ROOT / "src" / "desktop_app.py"
    icon_path = PROJECT_ROOT / "assets" / "branding" / "app_icon.ico"

    if not entry_script.exists():
        raise FileNotFoundError(f"Entry script missing: {entry_script}")

    pyinstaller_exe = PROJECT_ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_exe.exists():
        pyinstaller_exe = Path(sys.executable).parent / "pyinstaller.exe"

    cmd = [
        str(pyinstaller_exe),
        "--name=SentimentTrajectoryStudio",
        "--windowed",                 # No black terminal window
        "--noconfirm",
        "--clean",
        f"--icon={icon_path}",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--add-data={PROJECT_ROOT / 'configs'};configs",
        f"--add-data={PROJECT_ROOT / 'assets'};assets",
        "--hidden-import=PIL",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=scipy.special",
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.linear_model",
        "--hidden-import=torch",
        "--hidden-import=transformers",
        "--hidden-import=transformers.models.roberta",
        "--copy-metadata=transformers",
        "--copy-metadata=tokenizers",
        "--copy-metadata=safetensors",
        "--copy-metadata=torch",
        str(entry_script)
    ]

    print(f"Running PyInstaller command...\n{' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        raise RuntimeError(f"PyInstaller failed with return code {result.returncode}")

    print("PyInstaller packaging successful!")

    # Ensure models directory is copied into the dist application directory
    dest_models = app_dir / "models"
    src_models = PROJECT_ROOT / "models"
    if src_models.exists():
        print(f"Copying trained model checkpoints to {dest_models}...")
        if dest_models.exists():
            shutil.rmtree(dest_models)
        shutil.copytree(src_models, dest_models)

    # Ensure configs directory is present in dist
    dest_configs = app_dir / "configs"
    src_configs = PROJECT_ROOT / "configs"
    if src_configs.exists() and not dest_configs.exists():
        shutil.copytree(src_configs, dest_configs)

    target_exe = app_dir / "SentimentTrajectoryStudio.exe"
    if not target_exe.exists():
        raise FileNotFoundError(f"Expected binary not found: {target_exe}")

    exe_size_mb = target_exe.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Desktop Executable generated: {target_exe} ({exe_size_mb:.2f} MB)")

    # Create convenient distributable ZIP
    zip_target = dist_dir / "SentimentTrajectoryStudio_Windows_x64"
    print(f"Creating portable distributable archive: {zip_target}.zip ...")
    shutil.make_archive(str(zip_target), "zip", root_dir=str(dist_dir), base_dir="SentimentTrajectoryStudio")

    zip_file = dist_dir / "SentimentTrajectoryStudio_Windows_x64.zip"
    zip_size_mb = zip_file.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Portable ZIP package ready: {zip_file} ({zip_size_mb:.2f} MB)")
    print("=" * 70)


if __name__ == "__main__":
    build_desktop_app()
