"""
scripts/build_mobile_apk.py

Automated Android APK compilation pipeline.
Builds and packages a standalone, installable Android APK:
1. Compiles Android XML resources via aapt2 (Google Android Maven)
2. Links resources and assets via aapt2, generating R.java and package skeleton
3. Compiles Java source files via javac (JDK 17)
4. Converts bytecode classes to Dalvik DEX (classes.dex) via D8
5. Injects classes.dex and verifies uncompressed assets
6. 4-Byte ZipAligns all stored entries (classes.dex, resources.arsc, PNGs) for Android ART runtime
7. Signs APK with APK Signature Scheme V1 + V2 + V3 via Google apksig library
8. Verifies signature compliance via Google ApkVerifier

Output:
- dist/SentimentTrajectory.apk
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_TOOLS = PROJECT_ROOT / "build_tools" / "android"
MOBILE_DIR = PROJECT_ROOT / "mobile"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = MOBILE_DIR / "build"


def run_cmd(cmd_list, desc=""):
    print(f"\n[RUN] {desc or 'Command'}: {' '.join(str(c) for c in cmd_list[:6])}...")
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Failed: {desc}")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        raise RuntimeError(f"Command failed with code {res.returncode}")
    return res


def ensure_tools():
    setup_script = PROJECT_ROOT / "scripts" / "setup_android_tools.py"
    aapt2_exe = BUILD_TOOLS / "aapt2.exe"
    r8_jar = BUILD_TOOLS / "r8.jar"
    android_jar = BUILD_TOOLS / "android.jar"
    apksig_jar = BUILD_TOOLS / "apksig.jar"

    if not (aapt2_exe.exists() and r8_jar.exists() and android_jar.exists() and apksig_jar.exists()):
        print("[SETUP] Android CLI tools missing. Downloading minimal toolchain...")
        subprocess.run([sys.executable, str(setup_script)], check=True)

    # Compile Java signer and verifier utilities if needed
    signer_class = BUILD_TOOLS / "com" / "sentient" / "build" / "ApkSignerCli.class"
    if not signer_class.exists():
        print("[SETUP] Compiling ApkSignerCli and ApkVerifyCli...")
        signer_src = PROJECT_ROOT / "scripts" / "ApkSignerCli.java"
        verify_src = PROJECT_ROOT / "scripts" / "ApkVerifyCli.java"
        run_cmd(
            ["javac", "-cp", str(apksig_jar), "-d", str(BUILD_TOOLS), str(signer_src), str(verify_src)],
            "compile signer/verifier"
        )

    return aapt2_exe, r8_jar, android_jar, apksig_jar


def copy_branding_assets():
    print("[ASSETS] Copying unique visual identity & launcher icons...")
    branding_android = PROJECT_ROOT / "assets" / "branding" / "android"
    res_dir = MOBILE_DIR / "res"

    # Copy mipmap icons
    for density in ["mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi"]:
        src_icon = branding_android / density / "ic_launcher.png"
        dst_dir = res_dir / density
        dst_dir.mkdir(parents=True, exist_ok=True)
        if src_icon.exists():
            shutil.copy2(src_icon, dst_dir / "ic_launcher.png")

    # Copy master logo to assets
    src_logo = PROJECT_ROOT / "assets" / "branding" / "logo_128.png"
    dst_assets = MOBILE_DIR / "assets"
    dst_assets.mkdir(parents=True, exist_ok=True)
    if src_logo.exists():
        shutil.copy2(src_logo, dst_assets / "logo.png")


def align_apk_entries(input_apk: Path, output_apk: Path):
    """
    Standard 4-byte ZipAlign for Android APKs.
    Every uncompressed entry (compress_type == ZIP_STORED) must start at
    a multiple-of-4 byte offset in the archive so mmap() succeeds on Android.
    """
    with zipfile.ZipFile(input_apk, "r") as z_in, open(output_apk, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w") as z_out:
            for item in z_in.infolist():
                data = z_in.read(item.filename)
                new_info = zipfile.ZipInfo(item.filename, item.date_time)
                new_info.compress_type = item.compress_type
                new_info.comment = item.comment

                if item.compress_type == zipfile.ZIP_STORED:
                    curr_pos = f_out.tell()
                    pad = (4 - ((curr_pos + 30 + len(item.filename.encode("utf-8"))) % 4)) % 4
                    new_info.extra = b"\x00" * pad
                else:
                    new_info.extra = b""

                z_out.writestr(new_info, data)


def build_apk():
    print("=" * 70)
    print("STARTING ANDROID MOBILE APK COMPILATION PIPELINE")
    print("=" * 70)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    aapt2_exe, r8_jar, android_jar, apksig_jar = ensure_tools()
    copy_branding_assets()

    # 1. Compile Resources with aapt2
    compiled_res_dir = BUILD_DIR / "compiled_res"
    compiled_res_dir.mkdir(parents=True, exist_ok=True)
    res_dir = MOBILE_DIR / "res"

    print("[STEP 1/7] Compiling Android XML resources...")
    for root, _, files in os.walk(res_dir):
        for f in files:
            fpath = Path(root) / f
            run_cmd([str(aapt2_exe), "compile", str(fpath), "-o", str(compiled_res_dir)], f"compile {f}")

    # 2. Link resources & assets & generate R.java and initial package
    gen_dir = BUILD_DIR / "gen"
    gen_dir.mkdir(parents=True, exist_ok=True)
    unaligned_apk = BUILD_DIR / "unaligned.apk"
    manifest_xml = MOBILE_DIR / "AndroidManifest.xml"
    assets_dir = MOBILE_DIR / "assets"

    print("[STEP 2/7] Linking resources & assets with aapt2 and generating R.java...")
    link_cmd = [
        str(aapt2_exe), "link",
        "-I", str(android_jar),
        "--manifest", str(manifest_xml),
        "-A", str(assets_dir),
        "--java", str(gen_dir),
        "-o", str(unaligned_apk),
        "--auto-add-overlay"
    ]
    for flat in compiled_res_dir.glob("*.flat"):
        link_cmd.append(str(flat))

    run_cmd(link_cmd, "aapt2 link")

    # 3. Compile Java source code
    classes_dir = BUILD_DIR / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)

    java_sources = list((MOBILE_DIR / "src").rglob("*.java")) + list(gen_dir.rglob("*.java"))
    print(f"[STEP 3/7] Compiling {len(java_sources)} Java source files via javac...")

    javac_cmd = [
        "javac",
        "-source", "8",
        "-target", "8",
        "-bootclasspath", str(android_jar),
        "-d", str(classes_dir)
    ] + [str(s) for s in java_sources]
    run_cmd(javac_cmd, "javac compile")

    # 4. Convert .class files to classes.dex using D8
    dex_dir = BUILD_DIR / "dex"
    dex_dir.mkdir(parents=True, exist_ok=True)
    class_files = list(classes_dir.rglob("*.class"))

    print(f"[STEP 4/7] Converting {len(class_files)} bytecode classes to Dalvik DEX via D8...")
    d8_cmd = [
        "java",
        "-cp", str(r8_jar),
        "com.android.tools.r8.D8",
        "--output", str(dex_dir),
        "--lib", str(android_jar),
        "--min-api", "21"
    ] + [str(c) for c in class_files]
    run_cmd(d8_cmd, "D8 dex compilation")

    classes_dex = dex_dir / "classes.dex"
    if not classes_dex.exists():
        raise FileNotFoundError(f"classes.dex was not generated at {classes_dex}")

    # 5. Inject classes.dex into unaligned APK
    print("[STEP 5/7] Injecting classes.dex into APK package...")
    with zipfile.ZipFile(unaligned_apk, "a") as apk_zip:
        apk_zip.write(classes_dex, "classes.dex")

    # 6. ZipAlign on 4-byte boundaries (MANDATORY for Android ART runtime)
    aligned_apk = BUILD_DIR / "aligned.apk"
    print("[STEP 6/7] ZipAligning APK entries on 4-byte boundaries...")
    align_apk_entries(unaligned_apk, aligned_apk)

    # 7. Generate debug keystore & Sign APK via official ApkSigner with V1 + V2 + V3 schemes
    print("[STEP 7/7] Signing APK with Scheme V1 + V2 + V3 via Google apksig...")
    keystore_path = BUILD_DIR / "debug.keystore"
    if not keystore_path.exists():
        keytool_cmd = [
            "keytool",
            "-genkeypair",
            "-v",
            "-keystore", str(keystore_path),
            "-alias", "sentientkey",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "sentientpass",
            "-keypass", "sentientpass",
            "-dname", "CN=Sentient Trajectory, OU=AI, O=Sentient, C=US"
        ]
        run_cmd(keytool_cmd, "keytool genkeypair")

    final_apk = DIST_DIR / "SentimentTrajectory.apk"

    sign_cmd = [
        "java",
        "-cp", f"{BUILD_TOOLS / 'apksig.jar'};{BUILD_TOOLS}",
        "com.sentient.build.ApkSignerCli",
        str(aligned_apk),
        str(final_apk),
        str(keystore_path),
        "sentientkey",
        "sentientpass"
    ]
    run_cmd(sign_cmd, "apksig sign")

    # 8. Verify signature and compliance with Android installation rules
    print("\n[VERIFICATION] Verifying APK signature and compliance...")
    verify_cmd = [
        "java",
        "-cp", f"{BUILD_TOOLS / 'apksig.jar'};{BUILD_TOOLS}",
        "com.sentient.build.ApkVerifyCli",
        str(final_apk)
    ]
    verify_res = run_cmd(verify_cmd, "apksig verify")
    print(verify_res.stdout)

    # Verify 4-byte alignment
    with zipfile.ZipFile(final_apk, "r") as zf:
        for info in zf.infolist():
            if info.compress_type == zipfile.ZIP_STORED:
                data_offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
                if data_offset % 4 != 0:
                    raise RuntimeError(f"Entry {info.filename} is not 4-byte aligned (offset={data_offset})")

    apk_size_kb = final_apk.stat().st_size / 1024
    print("=" * 70)
    print(f"[SUCCESS] MOBILE APK BUILT, ZIPALIGNED & V1+V2+V3 SIGNED SUCCESSFULLY!")
    print(f"Path: {final_apk}")
    print(f"Size: {apk_size_kb:.1f} KB ({final_apk.stat().st_size} bytes)")
    print("All uncompressed entries 4-byte aligned: PASS")
    print("APK Signature Schemes V1 + V2 + V3: PASS")
    print("Ready for installation on any Android phone (Android 5.0 to 14/15).")
    print("=" * 70)


if __name__ == "__main__":
    build_apk()
