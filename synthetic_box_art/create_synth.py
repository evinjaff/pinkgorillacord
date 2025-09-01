import os
import random
from PIL import Image

# Input directories
BACKGROUND_DIR = "backgrounds"
COVER_DIRS = ["game_covers_NES", "game_covers_SNES"]  # add more if needed
OUTPUT_DIR = "output"
DIVISON_SIZE = 5

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_random_image(path):
    """Pick a random JPEG image from a folder."""
    files = [f for f in os.listdir(path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        return None
    img_path = os.path.join(path, random.choice(files))
    return Image.open(img_path).convert("RGBA")

def place_covers_on_background(bg_img, num_covers=4):
    """Overlay random covers on a background image."""
    bg_w, bg_h = bg_img.size
    min_dim = min(bg_w, bg_h)
    target_size = min_dim // DIVISON_SIZE  # ~1/9th of smaller dimension

    # Copy so we don’t overwrite original
    composed = bg_img.convert("RGBA")

    for _ in range(num_covers):
        # Pick random cover directory
        cover_dir = random.choice(COVER_DIRS)
        cover = get_random_image(cover_dir)
        if cover is None:
            continue

        # Scale proportionally
        c_w, c_h = cover.size
        scale = target_size / max(c_w, c_h)
        new_size = (int(c_w * scale), int(c_h * scale))
        cover = cover.resize(new_size, Image.LANCZOS)

        # Pick random location (ensure it fits)
        max_x = max(0, bg_w - new_size[0])
        max_y = max(0, bg_h - new_size[1])
        pos_x = random.randint(0, max_x)
        pos_y = random.randint(0, max_y)

        # Paste with transparency handling
        composed.alpha_composite(cover, (pos_x, pos_y))

    return composed.convert("RGB")  # drop alpha for saving as JPEG

def generate_synthetic_data(num_images=10):
    bg_files = [f for f in os.listdir(BACKGROUND_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    for i in range(num_images):
        bg_path = os.path.join(BACKGROUND_DIR, random.choice(bg_files))
        bg_img = Image.open(bg_path).convert("RGBA")

        result = place_covers_on_background(bg_img, num_covers=4)

        out_path = os.path.join(OUTPUT_DIR, f"synthetic_{i+1:03d}.jpg")
        result.save(out_path, "JPEG", quality=95)
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    generate_synthetic_data(num_images=50)  # change number of images here

