"""
scripts/setup_android_tools.py

Downloads minimal standalone Android CLI toolchain:
- aapt2.exe (from Google Android Maven repository)
- d8 / r8.jar (from Google Android Maven repository)
- android.jar (Android platform stub jar)

Enables compiling pure Android APKs without requiring 5GB Android Studio installation.
"""

import os
import sys
import zipfile
import urllib.request
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "build_tools" / "android"

AAPT2_URL = "https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.2.2-10154469/aapt2-8.2.2-10154469-windows.jar"
R8_URL = "https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.2.33/r8-8.2.33.jar"
# Official android-30 platform stub jar
ANDROID_JAR_URL = "https://github.com/Sable/android-platforms/raw/master/android-30/android.jar"


def download_with_progress(url: str, dest_path: Path):
    if dest_path.exists() and dest_path.stat().st_size > 1000:
        print(f"[EXISTS] {dest_path.name} already downloaded.")
        return

    print(f"[DOWNLOADING] {url} -> {dest_path.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out_file:
        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 64 * 1024
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = downloaded * 100 / total_size
                sys.stdout.write(f"\r  Downloaded: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.0f}%)")
                sys.stdout.flush()
    print("\n[COMPLETE]")


def setup():
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download and extract aapt2.exe
    aapt2_jar = TOOLS_DIR / "aapt2.jar"
    download_with_progress(AAPT2_URL, aapt2_jar)
    
    aapt2_exe = TOOLS_DIR / "aapt2.exe"
    if not aapt2_exe.exists():
        print("Extracting aapt2.exe from jar...")
        with zipfile.ZipFile(aapt2_jar, "r") as z:
            with z.open("aapt2.exe") as src, open(aapt2_exe, "wb") as dst:
                dst.write(src.read())
        print(f"[SUCCESS] Extracted {aapt2_exe}")

    # 2. Download r8.jar (provides d8)
    r8_jar = TOOLS_DIR / "r8.jar"
    download_with_progress(R8_URL, r8_jar)

    # 3. Download android.jar
    android_jar = TOOLS_DIR / "android.jar"
    download_with_progress(ANDROID_JAR_URL, android_jar)

    print("\n[VERIFICATION]")
    print(f"aapt2:       {aapt2_exe} (exists: {aapt2_exe.exists()})")
    print(f"r8 / d8:     {r8_jar} (exists: {r8_jar.exists()})")
    print(f"android.jar: {android_jar} (exists: {android_jar.exists()})")
    print("Android standalone build toolchain ready!")


if __name__ == "__main__":
    setup()
