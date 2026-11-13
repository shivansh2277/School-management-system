import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_assets():
    assets_dir = Path("school-management-system/mobile/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Main Icon: 1024x1024
    # Deep Indigo background (#4338CA) with golden/white Sunrise School crest
    size = (1024, 1024)
    img = Image.new("RGBA", size, (67, 56, 202, 255))
    draw = ImageDraw.Draw(img)

    # Outer subtle glow ring
    draw.ellipse([(140, 140), (884, 884)], outline=(99, 102, 241, 140), width=8)

    # Main Shield / Crest Body
    # Rounded crest container
    crest_box = [(220, 220), (804, 804)]
    draw.rounded_rectangle(crest_box, radius=160, fill=(49, 46, 129, 255), outline=(238, 242, 255, 230), width=16)

    # Golden Sun Rays / Sunrise at center
    sun_center = (512, 470)
    # Sun semi-circle
    draw.pieslice([(392, 350), (632, 590)], start=180, end=360, fill=(245, 158, 11, 255), outline=(251, 191, 36, 255), width=6)
    # Sun inner glow
    draw.pieslice([(422, 380), (602, 560)], start=180, end=360, fill=(251, 191, 36, 255))

    # Horizon bar
    draw.rounded_rectangle([(360, 465), (664, 485)], radius=6, fill=(255, 255, 255, 255))

    # Open Book / Education Crest below the sun
    # Left page
    draw.polygon([(504, 520), (410, 500), (410, 590), (504, 615)], fill=(255, 255, 255, 255))
    # Right page
    draw.polygon([(520, 520), (614, 500), (614, 590), (520, 615)], fill=(255, 255, 255, 255))
    # Book spine line
    draw.line([(512, 510), (512, 625)], fill=(199, 210, 254, 255), width=6)

    # Typography: "SUNRISE"
    try:
        font_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 68)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
    except Exception:
        font_title = font_sub = ImageFont.load_default()

    # Draw Text
    draw.text((512, 690), "SUNRISE", fill=(255, 255, 255, 255), font=font_title, anchor="mm")
    draw.text((512, 755), "PUBLIC SCHOOL", fill=(217, 226, 255, 240), font=font_sub, anchor="mm")

    icon_path = assets_dir / "icon.png"
    img.save(icon_path, "PNG")
    print(f"[OK] Saved app icon: {icon_path}")

    # 2. Adaptive Icon: 1024x1024 (Android foreground)
    # Must have the logo centered in the 66% safe area (within 675x675 center)
    adaptive_img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    # Resize the crest into the safe zone
    crest_crop = img.crop((180, 180, 844, 844))
    crest_resized = crest_crop.resize((620, 620), Image.Resampling.LANCZOS)
    adaptive_img.paste(crest_resized, (202, 202), crest_resized)
    
    adaptive_path = assets_dir / "adaptive-icon.png"
    adaptive_img.save(adaptive_path, "PNG")
    print(f"[OK] Saved adaptive icon: {adaptive_path}")

    # 3. Splash Screen: 512x512 centered logo
    splash_crop = img.crop((200, 200, 824, 824))
    splash_img = splash_crop.resize((512, 512), Image.Resampling.LANCZOS)
    splash_path = assets_dir / "splash-icon.png"
    splash_img.save(splash_path, "PNG")
    print(f"[OK] Saved splash icon: {splash_path}")

if __name__ == "__main__":
    generate_assets()
