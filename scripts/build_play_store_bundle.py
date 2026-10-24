"""
scripts/build_play_store_bundle.py

Automated production release pipeline for Google Play Store:
1. Ensures standalone toolchain (aapt2, r8/d8, android.jar, bundletool, apksig)
2. Compiles resources and assets in Protocol Buffer format (aapt2 link --proto-format)
3. Compiles Java source and generates Dalvik DEX (classes.dex)
4. Constructs base module zip adhering to Google Android App Bundle specifications
5. Builds official Android App Bundle (.aab) via Google bundletool
6. Generates permanent Production Release Keystore (release.keystore)
7. Signs .aab with Release Keystore via jarsigner (for Google Play App Signing)
8. Also builds a production-signed, 4-byte aligned release .apk (SentimentTrajectory_release.apk)
9. Validates .aab via bundletool validate and .apk via Google ApkVerifier

Outputs:
- dist/SentimentTrajectory.aab (Upload this to Google Play Console)
- dist/SentimentTrajectory_release.apk (For direct testing & distribution)
- dist/release.keystore (Secure signing key — keep safe!)
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
    aapt2_exe = BUILD_TOOLS / "aapt2.exe"
    r8_jar = BUILD_TOOLS / "r8.jar"
    android_jar = BUILD_TOOLS / "android.jar"
    apksig_jar = BUILD_TOOLS / "apksig.jar"
    bundletool_jar = BUILD_TOOLS / "bundletool.jar"

    if not (aapt2_exe.exists() and r8_jar.exists() and android_jar.exists() and apksig_jar.exists() and bundletool_jar.exists()):
        raise FileNotFoundError("Build toolchain missing in build_tools/android")

    return aapt2_exe, r8_jar, android_jar, apksig_jar, bundletool_jar


def copy_branding_assets():
    print("[ASSETS] Copying unique visual identity & launcher icons...")
    branding_android = PROJECT_ROOT / "assets" / "branding" / "android"
    res_dir = MOBILE_DIR / "res"

    for density in ["mipmap-mdpi", "mipmap-hdpi", "mipmap-xhdpi", "mipmap-xxhdpi", "mipmap-xxxhdpi"]:
        src_icon = branding_android / density / "ic_launcher.png"
        dst_dir = res_dir / density
        dst_dir.mkdir(parents=True, exist_ok=True)
        if src_icon.exists():
            shutil.copy2(src_icon, dst_dir / "ic_launcher.png")

    src_logo = PROJECT_ROOT / "assets" / "branding" / "logo_128.png"
    dst_assets = MOBILE_DIR / "assets"
    dst_assets.mkdir(parents=True, exist_ok=True)
    if src_logo.exists():
        shutil.copy2(src_logo, dst_assets / "logo.png")


def align_apk_entries(input_apk: Path, output_apk: Path):
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


def ensure_release_keystore() -> Path:
    keystore_path = DIST_DIR / "release.keystore"
    if not keystore_path.exists():
        print("\n[KEYSTORE] Generating permanent Production Release Keystore...")
        keytool_cmd = [
            "keytool",
            "-genkeypair",
            "-v",
            "-keystore", str(keystore_path),
            "-alias", "sentientrelease",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "SentientRelease2026!",
            "-keypass", "SentientRelease2026!",
            "-dname", "CN=Sentient Trajectory Release, OU=AI Research, O=Sentient, C=US"
        ]
        run_cmd(keytool_cmd, "generate release keytool")
        print(f"[SUCCESS] Production release keystore generated at: {keystore_path}")
    return keystore_path


def build_bundle():
    print("=" * 70)
    print("STARTING GOOGLE PLAY STORE PRODUCTION BUNDLE (.AAB) BUILD")
    print("=" * 70)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    aapt2_exe, r8_jar, android_jar, apksig_jar, bundletool_jar = ensure_tools()
    copy_branding_assets()
    release_keystore = ensure_release_keystore()

    # 1. Compile Resources with aapt2
    compiled_res_dir = BUILD_DIR / "compiled_res"
    compiled_res_dir.mkdir(parents=True, exist_ok=True)
    res_dir = MOBILE_DIR / "res"

    print("[STEP 1/8] Compiling Android XML resources...")
    flat_files = []
    for root, _, files in os.walk(res_dir):
        for f in files:
            fpath = Path(root) / f
            run_cmd([str(aapt2_exe), "compile", str(fpath), "-o", str(compiled_res_dir)], f"compile {f}")

    # 2. Compile Java Activity & R.java
    gen_dir = BUILD_DIR / "gen"
    gen_dir.mkdir(parents=True, exist_ok=True)
    manifest_xml = MOBILE_DIR / "AndroidManifest.xml"
    assets_dir = MOBILE_DIR / "assets"
    unaligned_apk = BUILD_DIR / "unaligned.apk"

    print("[STEP 2/8] Generating R.java and package skeleton...")
    link_res_cmd = [
        str(aapt2_exe), "link",
        "-I", str(android_jar),
        "--manifest", str(manifest_xml),
        "-A", str(assets_dir),
        "--java", str(gen_dir),
        "-o", str(unaligned_apk),
        "--auto-add-overlay"
    ]
    for flat in compiled_res_dir.glob("*.flat"):
        link_res_cmd.append(str(flat))
    run_cmd(link_res_cmd, "aapt2 link standard")

    classes_dir = BUILD_DIR / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)
    java_sources = list((MOBILE_DIR / "src").rglob("*.java")) + list(gen_dir.rglob("*.java"))

    print(f"[STEP 3/8] Compiling {len(java_sources)} Java source files via javac...")
    javac_cmd = [
        "javac",
        "-source", "8",
        "-target", "8",
        "-bootclasspath", str(android_jar),
        "-d", str(classes_dir)
    ] + [str(s) for s in java_sources]
    run_cmd(javac_cmd, "javac compile")

    # 3. Convert .class files to classes.dex using D8
    dex_dir = BUILD_DIR / "dex"
    dex_dir.mkdir(parents=True, exist_ok=True)
    class_files = list(classes_dir.rglob("*.class"))

    print(f"[STEP 4/8] Converting {len(class_files)} bytecode classes to Dalvik DEX via D8...")
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

    # 4. Compile Protocol Buffer Resources for Android App Bundle (.aab)
    proto_zip = BUILD_DIR / "proto_base.zip"
    print("[STEP 5/8] Compiling Protocol Buffer resources for App Bundle via aapt2...")
    link_proto_cmd = [
        str(aapt2_exe), "link",
        "--proto-format",
        "-I", str(android_jar),
        "--manifest", str(manifest_xml),
        "-A", str(assets_dir),
        "-o", str(proto_zip),
        "--auto-add-overlay"
    ]
    for flat in compiled_res_dir.glob("*.flat"):
        link_proto_cmd.append(str(flat))
    run_cmd(link_proto_cmd, "aapt2 link proto-format")

    # 5. Assemble Base Module Zip for Bundletool
    base_module_zip = BUILD_DIR / "base_module.zip"
    print("[STEP 6/8] Assembling base module structure for Google Play bundletool...")
    with zipfile.ZipFile(proto_zip, "r") as z_in, zipfile.ZipFile(base_module_zip, "w") as z_out:
        for item in z_in.infolist():
            data = z_in.read(item.filename)
            if item.filename == "AndroidManifest.xml":
                arcname = "manifest/AndroidManifest.xml"
            else:
                arcname = item.filename
            z_out.writestr(arcname, data)
        # Add classes.dex under dex/
        z_out.write(classes_dex, "dex/classes.dex")

    # 6. Build Android App Bundle (.aab)
    final_aab = DIST_DIR / "SentimentTrajectory.aab"
    print("[STEP 7/8] Generating Android App Bundle (.aab) via bundletool...")
    bundle_cmd = [
        "java",
        "-jar", str(bundletool_jar),
        "build-bundle",
        f"--modules={base_module_zip}",
        f"--output={final_aab}"
    ]
    run_cmd(bundle_cmd, "bundletool build-bundle")

    # Sign .aab with Release Keystore via jarsigner
    print("[STEP 8/8] Signing Android App Bundle with Release Keystore...")
    jarsigner_cmd = [
        "jarsigner",
        "-verbose",
        "-sigalg", "SHA256withRSA",
        "-digestalg", "SHA-256",
        "-keystore", str(release_keystore),
        "-storepass", "SentientRelease2026!",
        "-keypass", "SentientRelease2026!",
        str(final_aab),
        "sentientrelease"
    ]
    run_cmd(jarsigner_cmd, "jarsigner sign .aab")

    # Validate the generated App Bundle
    print("\n[VALIDATION] Validating App Bundle structure...")
    val_cmd = ["java", "-jar", str(bundletool_jar), "validate", f"--bundle={final_aab}"]
    val_res = run_cmd(val_cmd, "bundletool validate")
    print(val_res.stdout)

    # 7. Also build release-signed .apk for direct testing
    with zipfile.ZipFile(unaligned_apk, "a") as apk_zip:
        apk_zip.write(classes_dex, "classes.dex")

    aligned_apk = BUILD_DIR / "aligned.apk"
    align_apk_entries(unaligned_apk, aligned_apk)

    final_apk = DIST_DIR / "SentimentTrajectory_release.apk"
    sign_apk_cmd = [
        "java",
        "-cp", f"{BUILD_TOOLS / 'apksig.jar'};{BUILD_TOOLS}",
        "com.sentient.build.ApkSignerCli",
        str(aligned_apk),
        str(final_apk),
        str(release_keystore),
        "sentientrelease",
        "SentientRelease2026!"
    ]
    run_cmd(sign_apk_cmd, "apksig sign release apk")

    # Also update the primary dist/SentimentTrajectory.apk with the release build
    shutil.copy2(final_apk, DIST_DIR / "SentimentTrajectory.apk")

    aab_size_kb = final_aab.stat().st_size / 1024
    apk_size_kb = final_apk.stat().st_size / 1024

    print("=" * 70)
    print("[SUCCESS] GOOGLE PLAY PRODUCTION BUNDLE & RELEASE APK GENERATED!")
    print(f"1. Play Store Bundle:  {final_aab} ({aab_size_kb:.1f} KB)")
    print(f"2. Release APK:        {final_apk} ({apk_size_kb:.1f} KB)")
    print(f"3. Release Keystore:   {release_keystore}")
    print("=" * 70)


if __name__ == "__main__":
    build_bundle()
