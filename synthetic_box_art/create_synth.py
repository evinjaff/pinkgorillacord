import os
import random
import math
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np

# Input directories
BACKGROUND_DIR = "backgrounds"
COVER_DIRS_NEG = ["game_covers_NES_neg", "game_covers_SNES_neg"]
COVER_DIRS_POS = ["game_covers_MISC_pos", "game_covers_EBAY_pos"]
OUTPUT_DIR = "output"
DIVISION_SIZE = 5

# Augmentation parameters
ROTATION_RANGE = (-15, 15)  # degrees
SCALE_VARIATION = (0.8, 1.2)  # scale multiplier range
BRIGHTNESS_RANGE = (0.7, 1.3)
CONTRAST_RANGE = (0.8, 1.2)
SATURATION_RANGE = (0.8, 1.2)
BLUR_PROBABILITY = 0.3
BLUR_RADIUS = (0.5, 2.0)
NOISE_PROBABILITY = 0.2
NOISE_INTENSITY = (10, 30)
SHADOW_PROBABILITY = 0.4
OVERLAY_OPACITY_RANGE = (0.7, 1.0)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_random_image(path):
    """Pick a random JPEG image from a folder."""
    files = [f for f in os.listdir(path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        return None
    img_path = os.path.join(path, random.choice(files))
    return Image.open(img_path).convert("RGBA")

def add_noise(img, intensity):
    """Add random noise to an image."""
    img_array = np.array(img)
    noise = np.random.randint(-intensity, intensity + 1, img_array.shape, dtype=np.int16)
    noisy_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_array, mode=img.mode)

def create_shadow(img, offset=(5, 5), blur_radius=3, opacity=0.3):
    """Create a drop shadow effect."""
    # Create shadow by duplicating image and making it darker
    shadow = img.copy()
    shadow = ImageEnhance.Brightness(shadow).enhance(0.3)  # Make darker
    
    # Create a new image with extra space for shadow
    shadow_img = Image.new('RGBA', 
                          (img.width + abs(offset[0]), img.height + abs(offset[1])), 
                          (0, 0, 0, 0))
    
    # Paste shadow with offset
    shadow_pos = (max(0, offset[0]), max(0, offset[1]))
    shadow_img.paste(shadow, shadow_pos)
    
    # Blur the shadow
    if blur_radius > 0:
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Adjust shadow opacity
    if shadow_img.mode == 'RGBA':
        r, g, b, a = shadow_img.split()
        a = ImageEnhance.Brightness(a).enhance(opacity)
        shadow_img = Image.merge('RGBA', (r, g, b, a))
    
    # Paste original image on top
    img_pos = (max(0, -offset[0]), max(0, -offset[1]))
    shadow_img.paste(img, img_pos, img if img.mode == 'RGBA' else None)
    
    return shadow_img

def apply_perspective_transform(img, intensity=0.1):
    """Apply a subtle perspective transformation."""
    width, height = img.size
    
    # Generate random perspective distortion
    distortion = random.uniform(-intensity, intensity)
    
    # Define perspective transformation coefficients
    # This creates a subtle keystone effect
    coeffs = [
        1 + distortion * random.uniform(-0.5, 0.5), distortion * random.uniform(-0.5, 0.5), 0,
        distortion * random.uniform(-0.5, 0.5), 1 + distortion * random.uniform(-0.5, 0.5), 0,
        distortion * random.uniform(-1, 1) / width, distortion * random.uniform(-1, 1) / height
    ]
    
    return img.transform(img.size, Image.PERSPECTIVE, coeffs, Image.BILINEAR)

def augment_cover_image(cover_img):
    """Apply random augmentations to a cover image."""
    # Start with the original
    augmented = cover_img.copy()
    
    # Random rotation
    if random.random() > 0.3:  # 70% chance of rotation
        angle = random.uniform(*ROTATION_RANGE)
        augmented = augmented.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
    
    # Perspective transformation
    if random.random() > 0.6:  # 40% chance of perspective
        augmented = apply_perspective_transform(augmented, intensity=0.05)
    
    # Color adjustments
    if random.random() > 0.2:  # 80% chance of brightness adjustment
        brightness_factor = random.uniform(*BRIGHTNESS_RANGE)
        augmented = ImageEnhance.Brightness(augmented).enhance(brightness_factor)
    
    if random.random() > 0.3:  # 70% chance of contrast adjustment
        contrast_factor = random.uniform(*CONTRAST_RANGE)
        augmented = ImageEnhance.Contrast(augmented).enhance(contrast_factor)
    
    if random.random() > 0.4:  # 60% chance of saturation adjustment
        saturation_factor = random.uniform(*SATURATION_RANGE)
        augmented = ImageEnhance.Color(augmented).enhance(saturation_factor)
    
    # Blur
    if random.random() < BLUR_PROBABILITY:
        blur_radius = random.uniform(*BLUR_RADIUS)
        augmented = augmented.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Noise
    if random.random() < NOISE_PROBABILITY:
        noise_intensity = random.randint(*NOISE_INTENSITY)
        augmented = add_noise(augmented, noise_intensity)
    
    return augmented

def augment_background(bg_img):
    """Apply subtle augmentations to background image."""
    augmented = bg_img.copy()
    
    # Subtle brightness/contrast adjustments
    if random.random() > 0.4:
        brightness_factor = random.uniform(0.85, 1.15)
        augmented = ImageEnhance.Brightness(augmented).enhance(brightness_factor)
    
    if random.random() > 0.5:
        contrast_factor = random.uniform(0.9, 1.1)
        augmented = ImageEnhance.Contrast(augmented).enhance(contrast_factor)
    
    # Subtle blur occasionally
    if random.random() < 0.1:  # 10% chance
        augmented = augmented.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return augmented

def place_covers_on_background(bg_img, num_covers=4, is_positive=False):
    """Overlay random covers on a background image with augmentations and return bounding boxes."""
    bg_w, bg_h = bg_img.size
    min_dim = min(bg_w, bg_h)
    base_target_size = min_dim // DIVISION_SIZE
    
    # Apply background augmentation
    bg_img = augment_background(bg_img)
    composed = bg_img.convert("RGBA")
    bounding_boxes = []
    
    # Track placed covers to avoid too much overlap
    placed_rects = []
    
    covers_placed = 0
    attempts = 0
    max_attempts = num_covers * 3  # Allow multiple attempts to place covers
    
    while covers_placed < num_covers and attempts < max_attempts:
        attempts += 1
        
        # Pick random cover directory
        cover_dir = random.choice(COVER_DIRS_POS if is_positive else COVER_DIRS_NEG)
        cover = get_random_image(cover_dir)
        if cover is None:
            continue
        
        # Apply augmentations to cover
        cover = augment_cover_image(cover)
        
        # Random scale variation
        scale_factor = random.uniform(*SCALE_VARIATION)
        target_size = int(base_target_size * scale_factor)
        
        # Scale proportionally
        c_w, c_h = cover.size
        scale = target_size / max(c_w, c_h)
        new_size = (int(c_w * scale), int(c_h * scale))
        cover = cover.resize(new_size, Image.BILINEAR)
        
        # Try to find a position with minimal overlap
        best_pos = None
        best_overlap = float('inf')
        
        for _ in range(20):  # Try 20 random positions
            max_x = max(0, bg_w - new_size[0])
            max_y = max(0, bg_h - new_size[1])
            pos_x = random.randint(0, max_x)
            pos_y = random.randint(0, max_y)
            
            # Calculate overlap with existing covers
            current_rect = (pos_x, pos_y, pos_x + new_size[0], pos_y + new_size[1])
            total_overlap = 0
            
            for existing_rect in placed_rects:
                overlap = calculate_overlap(current_rect, existing_rect)
                total_overlap += overlap
            
            if total_overlap < best_overlap:
                best_overlap = total_overlap
                best_pos = (pos_x, pos_y)
                
                # If we found a position with no overlap, use it immediately
                if total_overlap == 0:
                    break
        
        if best_pos is None:
            continue
        
        pos_x, pos_y = best_pos
        
        # Add shadow effect
        if random.random() < SHADOW_PROBABILITY:
            shadow_offset = (random.randint(2, 8), random.randint(2, 8))
            cover_with_shadow = create_shadow(cover, shadow_offset, 
                                            blur_radius=random.uniform(1, 4), 
                                            opacity=random.uniform(0.2, 0.5))
            
            # Adjust position to account for shadow
            shadow_pos_x = max(0, min(pos_x - max(0, -shadow_offset[0]), bg_w - cover_with_shadow.width))
            shadow_pos_y = max(0, min(pos_y - max(0, -shadow_offset[1]), bg_h - cover_with_shadow.height))
            
            # Random opacity for the entire cover+shadow
            opacity = random.uniform(*OVERLAY_OPACITY_RANGE)
            if opacity < 1.0:
                r, g, b, a = cover_with_shadow.split()
                a = ImageEnhance.Brightness(a).enhance(opacity)
                cover_with_shadow = Image.merge('RGBA', (r, g, b, a))
            
            composed.alpha_composite(cover_with_shadow, (shadow_pos_x, shadow_pos_y))
        else:
            # Random opacity for the cover
            opacity = random.uniform(*OVERLAY_OPACITY_RANGE)
            if opacity < 1.0:
                r, g, b, a = cover.split()
                a = ImageEnhance.Brightness(a).enhance(opacity)
                cover = Image.merge('RGBA', (r, g, b, a))
            
            composed.alpha_composite(cover, (pos_x, pos_y))
        
        # Track placed cover
        placed_rects.append((pos_x, pos_y, pos_x + new_size[0], pos_y + new_size[1]))
        
        # Calculate YOLO format bounding box (normalized coordinates)
        if is_positive:
            center_x = (pos_x + new_size[0] / 2) / bg_w
            center_y = (pos_y + new_size[1] / 2) / bg_h
            width = new_size[0] / bg_w
            height = new_size[1] / bg_h
            
            # Class ID 0 for game covers
            bounding_boxes.append(f"0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
        
        covers_placed += 1
    
    return composed.convert("RGB"), bounding_boxes

def calculate_overlap(rect1, rect2):
    """Calculate overlap area between two rectangles."""
    x1_max = max(rect1[0], rect2[0])
    y1_max = max(rect1[1], rect2[1])
    x2_min = min(rect1[2], rect2[2])
    y2_min = min(rect1[3], rect2[3])
    
    if x2_min <= x1_max or y2_min <= y1_max:
        return 0  # No overlap
    
    return (x2_min - x1_max) * (y2_min - y1_max)

def save_yolo_annotation(annotation_path, bounding_boxes):
    """Save YOLO format annotations to file."""
    with open(annotation_path, 'w') as f:
        for box in bounding_boxes:
            f.write(box + '\n')

def generate_synthetic_data(num_images=10, is_positive=False, offset_index=0):
    """Generate synthetic training data with augmentations."""
    bg_files = [f for f in os.listdir(BACKGROUND_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    
    if not bg_files:
        print("Error: No background images found!")
        return
    
    successful_generations = 0
    
    for i in range(num_images):
        try:
            bg_path = os.path.join(BACKGROUND_DIR, random.choice(bg_files))
            bg_img = Image.open(bg_path).convert("RGBA")
            
            # Vary number of covers per image
            num_covers = random.randint(1, 6) if is_positive else random.randint(2, 8)
            
            result, bounding_boxes = place_covers_on_background(bg_img, num_covers=num_covers, is_positive=is_positive)
            
            # Save image with higher quality for training
            img_filename = f"synthetic_{i+1+offset_index:03d}.jpg"
            out_path = os.path.join(OUTPUT_DIR, img_filename)
            result.save(out_path, "JPEG", quality=92, optimize=True)
            
            # Save annotations
            annotation_filename = f"synthetic_{i+1+offset_index:03d}.txt"
            annotation_path = os.path.join(OUTPUT_DIR, annotation_filename)
            
            if is_positive and bounding_boxes:
                save_yolo_annotation(annotation_path, bounding_boxes)
                print(f"✓ Generated: {img_filename} with {len(bounding_boxes)} covers")
            else:
                save_yolo_annotation(annotation_path, [])
                print(f"✓ Generated: {img_filename} (negative sample)")
            
            successful_generations += 1
            
        except Exception as e:
            print(f"✗ Error generating image {i+1} (offset + {offset_index}): {str(e)}")
    
    print(f"\nCompleted: {successful_generations}/{num_images} images generated successfully")

if __name__ == "__main__":
    print("Starting enhanced synthetic data generation...")
    print("Positive samples (with game covers):")
    generate_synthetic_data(num_images=350, is_positive=True)
    print("\nNegative samples (without game covers):")
    generate_synthetic_data(num_images=350, is_positive=False, offset_index=351)