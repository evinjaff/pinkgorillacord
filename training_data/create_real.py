#!/usr/bin/env python3
"""
Auto LabelMe to YOLO converter that handles variable image sizes
"""

import os
import sys
import subprocess
import argparse
from PIL import Image
from collections import defaultdict

def get_image_dimensions(image_path):
    """Get image dimensions using PIL"""
    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return None, None

def find_image_for_annotation(annotation_file, yolo_dir):
    """Find corresponding image file for annotation"""
    base_name = os.path.splitext(os.path.basename(annotation_file))[0]
    
    # Common image extensions
    extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    
    for ext in extensions:
        img_path = os.path.join(yolo_dir, base_name + ext)
        if os.path.exists(img_path):
            return img_path
    return None

def group_by_dimensions(yolo_dir, classes_file):
    """Group annotation files by their corresponding image dimensions"""
    dimension_groups = defaultdict(list)
    
    # Find all .txt files
    txt_files = [f for f in os.listdir(yolo_dir) if f.endswith('.txt')]
    if len(txt_files) == 0:
        print("Warning: No txt files exist in {}".format(yolo_dir))
        print("[DEBUG] Dir Contents: {}...".format(os.listdir(yolo_dir)[0:5]))

    for txt_file in txt_files:
        txt_path = os.path.join(yolo_dir, txt_file)
        img_path = find_image_for_annotation(txt_path, yolo_dir)
        
        if img_path:
            width, height = get_image_dimensions(img_path)
            if width and height:
                dimension_groups[(width, height)].append(txt_file)
            else:
                print(f"Warning: Could not get dimensions for {img_path}")
        else:
            print(f"Warning: No corresponding image found for {txt_file}")
    
    return dimension_groups

def convert_group(yolo_dir, labelme_dir, classes_file, width, height, txt_files):
    """Convert a group of files with the same dimensions"""
    print(f"Converting {len(txt_files)} files with dimensions {width}x{height}")
    
    # Create temporary directory for this dimension group
    temp_dir = os.path.join(yolo_dir, f"temp_{width}x{height}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy txt files to temp directory
        for txt_file in txt_files:
            src = os.path.join(yolo_dir, txt_file)
            dst = os.path.join(temp_dir, txt_file)
            
            # Copy the txt file
            with open(src, 'r') as f_src, open(dst, 'w') as f_dst:
                f_dst.write(f_src.read())
        
        # Run yolotolabelme for this group
        cmd = [
            'yolotolabelme',
            '--yolo', temp_dir,
            '--labelme', labelme_dir,
            '--classes', classes_file,
            '--width', str(width),
            '--height', str(height)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error converting {width}x{height} group:")
            print(result.stderr)
        else:
            print(f"Successfully converted {len(txt_files)} files ({width}x{height})")
    
    finally:
        # Clean up temp directory
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

def main():
    parser = argparse.ArgumentParser(description='Convert YOLO annotations to LabelMe with variable image sizes')
    parser.add_argument('--yolo', required=True, help='Path to YOLO annotations directory')
    parser.add_argument('--labelme', required=True, help='Path to output LabelMe directory')
    parser.add_argument('--classes', required=True, help='Path to classes file')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.labelme, exist_ok=True)
    
    # Group files by dimensions
    print("Analyzing image dimensions...")
    dimension_groups = group_by_dimensions(args.yolo, args.classes)
    
    if not dimension_groups:
        print("No valid annotation-image pairs found!")
        return
    
    print(f"Found {len(dimension_groups)} different image dimensions:")
    for (width, height), files in dimension_groups.items():
        print(f"  {width}x{height}: {len(files)} files")
    
    # Convert each group
    total_converted = 0
    for (width, height), txt_files in dimension_groups.items():
        convert_group(args.yolo, args.labelme, args.classes, width, height, txt_files)
        total_converted += len(txt_files)
    
    print(f"\nConversion complete! Total files converted: {total_converted}")
    print(f"LabelMe JSON files saved to: {args.labelme}")

if __name__ == "__main__":
    main()
