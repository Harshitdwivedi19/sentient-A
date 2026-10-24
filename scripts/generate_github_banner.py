"""
scripts/generate_github_banner.py

Generates a wide GitHub README header banner (1280x420)
following the AI research visual theme:
- Deep navy, indigo, and subtle teal ambient gradient
- Prominent Title: SENTIMENT TRAJECTORY ANALYSIS
- Tagline: Understand How Sentiment Changes Across a Conversation
- Trajectory Waveform graph with inflection stars
- Chat bubble motifs with polarity chips
- High-contrast typography and subtle glassmorphic container
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "assets" / "sentiment-trajectory-banner.png"

def generate_banner():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 420
    img = Image.new("RGBA", (w, h), (11, 17, 32, 255))
    draw = ImageDraw.Draw(img)

    # 1. Deep navy & indigo linear gradient background
    for y in range(h):
        ratio = y / h
        # Gradient from #0B1120 (11, 17, 32) to #1E293B (30, 41, 59)
        r = int(11 + (22 - 11) * ratio)
        g = int(17 + (32 - 17) * ratio)
        b = int(32 + (55 - 32) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # 2. Ambient glow circles (teal on right, gold/indigo on left)
    glow_teal = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_gt = ImageDraw.Draw(glow_teal)
    draw_gt.ellipse([w - 400, -100, w + 200, 350], fill=(90, 174, 145, 35))
    draw_gt.ellipse([50, h - 250, 450, h + 150], fill=(99, 102, 241, 30))
    draw_gt.ellipse([w // 2 - 200, 50, w // 2 + 200, 350], fill=(243, 216, 106, 18))
    img = Image.alpha_composite(img, glow_teal)
    draw = ImageDraw.Draw(img)

    # 3. Ambient Grid Lines
    for gx in range(0, w, 40):
        draw.line([(gx, 0), (gx, h)], fill=(255, 255, 255, 8), width=1)
    for gy in range(0, h, 40):
        draw.line([(0, gy), (w, gy)], fill=(255, 255, 255, 8), width=1)

    # 4. Trajectory Waveform across the bottom
    points = []
    num_pts = 70
    for i in range(num_pts):
        x = int(i * (w / (num_pts - 1)))
        sine1 = math.sin(i * 0.12) * 55
        sine2 = math.cos(i * 0.07) * 35
        sine3 = math.sin(i * 0.25) * 18
        y = int(310 - (sine1 + sine2 + sine3))
        points.append((x, y))

    # Shaded Polarity Area
    poly = [(0, h)] + points + [(w, h)]
    draw.polygon(poly, fill=(56, 189, 248, 18))

    # Trajectory Line
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=(56, 189, 248, 190), width=3)

    # Turning Point Inflection Nodes
    tp_indices = [10, 24, 42, 58]
    for idx in tp_indices:
        cx, cy = points[idx]
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(243, 216, 106, 255))
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(11, 17, 32, 255))
        # Callout line
        draw.line([(cx, cy - 10), (cx, cy - 25)], fill=(243, 216, 106, 200), width=1)
        draw.rounded_rectangle([cx - 30, cy - 42, cx + 30, cy - 26], radius=4, fill=(30, 41, 59, 230), outline=(243, 216, 106, 180))

    # 5. Load and paste Master Emblem on the left
    emblem_path = PROJECT_ROOT / "assets" / "branding" / "logo_master_512.png"
    if emblem_path.exists():
        emblem = Image.open(emblem_path).convert("RGBA")
        emblem_thumb = emblem.resize((120, 120), Image.Resampling.LANCZOS)
        # Background card behind emblem
        draw.rounded_rectangle([75, 75, 215, 215], radius=24, fill=(15, 23, 42, 230), outline=(56, 189, 248, 80), width=1)
        img.paste(emblem_thumb, (85, 85), emblem_thumb)

    # 6. Typography
    font_large = None
    font_sub = None
    font_chips = None
    for f in ["segoeui.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]:
        try:
            font_large = ImageFont.truetype(f, 44)
            font_sub = ImageFont.truetype(f, 19)
            font_chips = ImageFont.truetype(f, 13)
            break
        except Exception:
            pass

    if not font_large:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_chips = ImageFont.load_default()

    # Draw Title & Tagline
    tx = 240
    draw.text((tx, 88), "SENTIMENT TRAJECTORY ANALYSIS", fill=(255, 255, 255, 255), font=font_large)
    draw.text((tx, 146), "Understand How Sentiment Changes Across a Conversation", fill=(148, 163, 184, 255), font=font_sub)

    # Technical Feature Chips
    chips = [
        ("Context-Aware RoBERTa", (56, 189, 248)),
        ("Candidate Turning Points", (243, 216, 106)),
        ("Windows Desktop .EXE", (168, 85, 247)),
        ("Android Mobile .APK / .AAB", (52, 211, 153)),
        ("100% On-Device Privacy", (90, 174, 145))
    ]

    cx_pos = tx
    cy_pos = 186
    for label, col in chips:
        ch_w = len(label) * 8 + 18
        draw.rounded_rectangle([cx_pos, cy_pos, cx_pos + ch_w, cy_pos + 26], radius=6, fill=(15, 23, 42, 220), outline=(col[0], col[1], col[2], 140), width=1)
        draw.text((cx_pos + 9, cy_pos + 5), label, fill=(col[0], col[1], col[2], 255), font=font_chips)
        cx_pos += ch_w + 10

    img.save(OUTPUT_PATH, "PNG")
    print(f"[SUCCESS] Banner created at: {OUTPUT_PATH} ({w}x{h})")

if __name__ == "__main__":
    generate_banner()
