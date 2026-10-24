"""
scripts/generate_feature_graphic.py

Generates the official 1024 x 500 Google Play Store Feature Graphic.
Features:
- Warm ivory (#F8F6EF) and soft cream (#FFFDF6) backdrop
- Brand title: "Sentient Trajectory"
- Subtitle: "Explainable Sentiment & Trajectory Analysis"
- Resonance Inflection Waveform motif
- Centered brand emblem
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "assets" / "branding"

def generate_feature_graphic():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    w, h = 1024, 500
    img = Image.new("RGBA", (w, h), (248, 246, 239, 255))
    draw = ImageDraw.Draw(img)

    # 1. Subtle radial/horizontal gradient background
    for y in range(h):
        ratio = y / h
        r = int(248 + (255 - 248) * (1 - ratio * 0.4))
        g = int(246 + (253 - 246) * (1 - ratio * 0.4))
        b = int(239 + (246 - 239) * (1 - ratio * 0.4))
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # 2. Draw aesthetic sentiment trajectory curve & nodes in background
    points = []
    num_points = 64
    for i in range(num_points):
        x = int(i * (w / (num_points - 1)))
        # Multi-frequency emotional wave
        sine_val = math.sin(i * 0.14) * 55 + math.cos(i * 0.08) * 35 + math.sin(i * 0.28) * 20
        y = int(320 - sine_val)
        points.append((x, y))

    # Draw shaded soft zone
    poly = [(0, 500)] + points + [(w, 500)]
    draw.polygon(poly, fill=(243, 216, 106, 24))

    # Draw curve
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=(41, 42, 45, 140), width=3)

    # Highlight turning points on curve
    tp_indices = [8, 22, 38, 52]
    for idx in tp_indices:
        cx, cy = points[idx]
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(201, 169, 74, 255))
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 253, 246, 255))

    # 3. Paste Brand Logo Emblem
    logo_path = OUTPUT_DIR / "logo_master_512.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo_thumb = logo.resize((140, 140), Image.Resampling.LANCZOS)
        # Place logo on the left/center
        lx = 90
        ly = 100
        # Draw soft shadow card behind logo
        draw.rounded_rectangle([lx - 10, ly - 10, lx + 150, ly + 150], radius=24, fill=(255, 253, 246, 240), outline=(232, 228, 217, 255), width=2)
        img.paste(logo_thumb, (lx, ly), logo_thumb)

    # 4. Typography
    # Try system fonts or default
    font_title = None
    font_sub = None
    font_badge = None
    for font_name in ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]:
        try:
            font_title = ImageFont.truetype(font_name, 52)
            font_sub = ImageFont.truetype(font_name, 22)
            font_badge = ImageFont.truetype(font_name, 15)
            break
        except Exception:
            pass

    if not font_title:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # Draw Text
    tx = 270
    draw.text((tx, 115), "Sentient Trajectory", fill=(41, 42, 45, 255), font=font_title)
    draw.text((tx, 185), "Explainable Conversation Sentiment & Emotion Modeling", fill=(119, 120, 115, 255), font=font_sub)

    # Badges
    badges = [
        ("🛡️ 100% On-Device Privacy", (90, 174, 145)),
        ("⚡ Candidate Turning Points", (201, 169, 74)),
        ("💬 WhatsApp & Text Import", (41, 42, 45)),
    ]
    bx = tx
    by = 235
    for label, col in badges:
        bw = len(label) * 9 + 20
        draw.rounded_rectangle([bx, by, bx + bw, by + 28], radius=8, fill=(255, 253, 246, 240), outline=(232, 228, 217, 255), width=1)
        draw.text((bx + 10, by + 6), label, fill=(col[0], col[1], col[2], 255), font=font_badge)
        bx += bw + 12

    out_file = OUTPUT_DIR / "play_store_feature_graphic_1024x500.png"
    img.save(out_file, "PNG")
    print(f"[SUCCESS] Feature Graphic generated at: {out_file} (1024x500)")

if __name__ == "__main__":
    generate_feature_graphic()
