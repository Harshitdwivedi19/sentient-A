"""
scripts/generate_branding.py

Generates a 100% unique, distinct visual identity and logo for the
"Context-Aware Conversation Sentiment & Trajectory Studio" project.

Visual Concept:
"Resonance Trajectory & Inflection Node"
- Non-derivative, purely mathematical & conversational symbology.
- Parametric emotional polarity waveform (s_t) undulating from negative trough to positive crest.
- Contextual resonance echo wave forming a harmonic envelope.
- Golden inflection diamond (turning point) with dynamic acoustic ripple rings.
- Discrete conversational utterance nodes along the path.
- Renders high-res 1024x1024 master, downsamples to 512, 256, multi-resolution Windows .ICO,
  and Android mipmap densities (mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi).
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def create_distinct_logo(size=1024) -> Image.Image:
    # Work on 2x super-sampled canvas for pristine antialiasing
    scale = 2
    w = size * scale
    h = size * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center_x = w / 2
    center_y = h / 2

    # 1. Background Rounded Squircle with Dark Indigo Radial Glow
    pad = 60 * scale
    corner_radius = 220 * scale

    # Draw base dark squircle
    draw.rounded_rectangle(
        [pad, pad, w - pad, h - pad],
        radius=corner_radius,
        fill=(11, 15, 25, 255), # Deep Space Navy
        outline=(30, 41, 59, 255),
        width=int(6 * scale)
    )

    # Ambient radial glow inside squircle
    glow_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_overlay)
    
    # Positive crest glow (Top Right - Emerald/Cyan)
    for r in range(int(350 * scale), int(50 * scale), -int(15 * scale)):
        alpha = int(35 * (1 - r / (350 * scale)))
        glow_draw.ellipse(
            [w * 0.7 - r, h * 0.32 - r, w * 0.7 + r, h * 0.32 + r],
            fill=(16, 185, 129, alpha)
        )

    # Turning Point glow (Center Pivot - Amber Gold)
    for r in range(int(260 * scale), int(30 * scale), -int(12 * scale)):
        alpha = int(45 * (1 - r / (260 * scale)))
        glow_draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=(245, 158, 11, alpha)
        )

    # Negative trough glow (Bottom Left - Deep Violet/Fuchsia)
    for r in range(int(320 * scale), int(50 * scale), -int(15 * scale)):
        alpha = int(30 * (1 - r / (320 * scale)))
        glow_draw.ellipse(
            [w * 0.3 - r, h * 0.68 - r, w * 0.3 + r, h * 0.68 + r],
            fill=(139, 92, 246, alpha)
        )

    img = Image.alpha_composite(img, glow_overlay)
    draw = ImageDraw.Draw(img)

    # 2. Conversational Equilibrium Horizon Line (Dotted Neutral Axis s=0)
    axis_y = center_y
    axis_start = pad + 80 * scale
    axis_end = w - pad - 80 * scale
    
    dash_len = int(14 * scale)
    gap_len = int(12 * scale)
    curr_x = axis_start
    while curr_x < axis_end:
        draw.line(
            [(curr_x, axis_y), (min(curr_x + dash_len, axis_end), axis_y)],
            fill=(51, 65, 85, 180),
            width=int(3 * scale)
        )
        curr_x += dash_len + gap_len

    # 3. Wave B: Contextual Resonance Echo Wave (Violet/Indigo, subtle opacity)
    echo_points = []
    num_steps = 300
    for i in range(num_steps + 1):
        t = i / num_steps
        x = axis_start + t * (axis_end - axis_start)
        # S-shape harmonic
        phase = t * 2 * math.pi
        y = center_y + (math.sin(phase - 0.4) * 220 * scale * (0.8 + 0.3 * math.sin(t * math.pi)))
        echo_points.append((x, y))

    for idx in range(len(echo_points) - 1):
        p1 = echo_points[idx]
        p2 = echo_points[idx + 1]
        draw.line([p1, p2], fill=(129, 140, 248, 110), width=int(5 * scale))

    # 4. Wave A: Primary Sentiment Polarity Trajectory (s_t)
    # Undulating from negative trough (left) -> inflection through center -> positive crest (right)
    traj_points = []
    traj_colors = []
    for i in range(num_steps + 1):
        t = i / num_steps
        x = axis_start + t * (axis_end - axis_start)
        # Dynamic cubic / sinusoidal trajectory
        norm_t = (t - 0.5) * 2 # -1 to +1
        # Polarity score function: inflection at center, rising from -0.8 to +0.85
        s_val = math.tanh(norm_t * 2.2) + 0.35 * math.sin(norm_t * math.pi * 1.5)
        y = center_y - (s_val * 240 * scale)
        traj_points.append((x, y))

        # Color gradient: Negative (Rose/Violet) -> Neutral (Cyan) -> Positive (Emerald)
        if s_val < -0.15:
            # Violet/Magenta #A855F7 -> #EC4899
            r = int(168 + (236 - 168) * (-s_val))
            g = int(85 * (1 - (-s_val) * 0.3))
            b = int(247 - 94 * (-s_val))
        elif s_val > 0.15:
            # Cyan -> Emerald #06B6D4 -> #10B981
            ratio = min(1.0, (s_val - 0.15) / 0.7)
            r = int(6 + (16 - 6) * ratio)
            g = int(182 + (185 - 182) * ratio)
            b = int(212 - (212 - 129) * ratio)
        else:
            # Transition Gold/Cyan
            r = 56
            g = 189
            b = 248

        traj_colors.append((min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)), 240))

    # Draw thick multi-line glow and core line
    for width_mul, alpha_mul in [(14, 0.25), (8, 0.55), (4, 1.0)]:
        for idx in range(len(traj_points) - 1):
            p1 = traj_points[idx]
            p2 = traj_points[idx + 1]
            c = traj_colors[idx]
            draw.line([p1, p2], fill=(c[0], c[1], c[2], int(c[3] * alpha_mul)), width=int(width_mul * scale))

    # 5. Discrete Dialogue Utterance Nodes along trajectory
    turn_fractions = [0.12, 0.28, 0.50, 0.72, 0.88]
    for idx, tf in enumerate(turn_fractions):
        step_idx = int(tf * num_steps)
        nx, ny = traj_points[step_idx]
        col = traj_colors[step_idx]
        
        # Outer ring
        draw.ellipse(
            [nx - 14 * scale, ny - 14 * scale, nx + 14 * scale, ny + 14 * scale],
            outline=(col[0], col[1], col[2], 255),
            width=int(3 * scale)
        )
        # Inner white core
        draw.ellipse(
            [nx - 6 * scale, ny - 6 * scale, nx + 6 * scale, ny + 6 * scale],
            fill=(255, 255, 255, 255)
        )

    # 6. Central Turning-Point Resonance Node (Focal Inflection Pivot)
    tp_x = center_x
    tp_y = center_y - (0.0 * 240 * scale)

    # Acoustic wave ripples around turning point
    for ripple_r, r_alpha in [(80 * scale, 90), (125 * scale, 55), (175 * scale, 25)]:
        draw.ellipse(
            [tp_x - ripple_r, tp_y - ripple_r, tp_x + ripple_r, tp_y + ripple_r],
            outline=(245, 158, 11, r_alpha),
            width=int(2.5 * scale)
        )

    # Dynamic 4-pointed golden inflection diamond
    d_size = 32 * scale
    diamond_poly = [
        (tp_x, tp_y - d_size * 1.3),
        (tp_x + d_size * 0.9, tp_y),
        (tp_x, tp_y + d_size * 1.3),
        (tp_x - d_size * 0.9, tp_y)
    ]
    draw.polygon(diamond_poly, fill=(245, 158, 11, 255), outline=(254, 240, 138, 255))
    # Core diamond spark
    spark_size = 14 * scale
    spark_poly = [
        (tp_x, tp_y - spark_size * 1.2),
        (tp_x + spark_size * 0.7, tp_y),
        (tp_x, tp_y + spark_size * 1.2),
        (tp_x - spark_size * 0.7, tp_y)
    ]
    draw.polygon(spark_poly, fill=(255, 255, 255, 255))

    # Downsample super-sampled image using Lanczos for flawless edges
    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    return final_img


def generate_all_branding_assets(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    branding_dir = output_dir / "branding"
    branding_dir.mkdir(parents=True, exist_ok=True)

    print("[BRANDING] Generating Unique Project Visual Identity & Master Logo...")
    master_512 = create_distinct_logo(size=512)
    master_512.save(branding_dir / "logo_master_512.png", "PNG")

    master_256 = master_512.resize((256, 256), Image.Resampling.LANCZOS)
    master_256.save(branding_dir / "logo_256.png", "PNG")

    master_128 = master_512.resize((128, 128), Image.Resampling.LANCZOS)
    master_128.save(branding_dir / "logo_128.png", "PNG")

    # Windows .ICO file with all standard layer resolutions
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_layers = [master_512.resize(s, Image.Resampling.LANCZOS) for s in ico_sizes]
    ico_path = branding_dir / "app_icon.ico"
    ico_layers[0].save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"[SUCCESS] Generated Windows Icon (.ico): {ico_path}")

    # Android mipmap launcher icons
    android_dir = branding_dir / "android"
    densities = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    for folder_name, px in densities.items():
        folder_path = android_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        icon_img = master_512.resize((px, px), Image.Resampling.LANCZOS)
        icon_img.save(folder_path / "ic_launcher.png", "PNG")

    print(f"[SUCCESS] Generated Android Mipmap Icons: {android_dir}")


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "assets"
    generate_all_branding_assets(out_path)
