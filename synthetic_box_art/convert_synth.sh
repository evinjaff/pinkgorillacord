#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting synthetic data generation pipeline...${NC}"

# Clean output folders before running
echo -e "${YELLOW}Cleaning output directories...${NC}"
rm -rf output/*
rm -rf labelme_output/*
rm -rf yolo_output
rm -rf yolo_val_output

# Ensure directories exist
mkdir -p output
mkdir -p labelme_output
mkdir -p yolo_output/images
mkdir -p yolo_output/labels

echo -e "${GREEN}Output directories cleaned and prepared${NC}"

# Generate synthetic data
echo -e "${BLUE}Generating synthetic training data...${NC}"
python3 create_synth.py

# Check if generation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Synthetic data generation failed!${NC}"
    exit 1
fi

# Count generated files
image_count=$(find output -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
label_count=$(find output -name "*.txt" | wc -l)

echo -e "${GREEN}Generated $image_count images and $label_count annotation files${NC}"

# Copy Images and Plaintexts to labelme to look at
echo -e "${BLUE}Copying files to labelme output...${NC}"
cp output/*.jpg labelme_output/ 2>/dev/null
cp output/*.jpeg labelme_output/ 2>/dev/null
cp output/*.png labelme_output/ 2>/dev/null

# Convert YOLO annotations to LabelMe format
echo -e "${BLUE}Converting YOLO annotations to LabelMe format...${NC}"
python3 auto_yolo_to_labelme.py --yolo output --labelme labelme_output --classes classes.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Warning: YOLO to LabelMe conversion had issues${NC}"
fi

# Copy files to YOLO output structure
echo -e "${BLUE}Setting up YOLO output structure...${NC}"
cp output/*.jpg yolo_output/images/ 2>/dev/null
cp output/*.jpeg yolo_output/images/ 2>/dev/null
cp output/*.png yolo_output/images/ 2>/dev/null
cp output/*.txt yolo_output/labels/ 2>/dev/null

# Create train/validation split (75%/25%)
echo -e "${BLUE}Creating train/validation split (75%/25%)...${NC}"
rm -rf yolo_val_output
mkdir -p yolo_val_output/train/images
mkdir -p yolo_val_output/train/labels
mkdir -p yolo_val_output/val/images
mkdir -p yolo_val_output/val/labels

# Get list of all image files (without extensions) for consistent splitting
image_files=($(find yolo_output/images -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | xargs -n1 basename | sed 's/\.[^.]*$//' | sort | uniq))
total_files=${#image_files[@]}
train_count=$((total_files * 75 / 100))

echo -e "${YELLOW}Total files: $total_files, Train: $train_count, Val: $((total_files - train_count))${NC}"

# Shuffle the array for random split
shuffled_files=($(printf '%s\n' "${image_files[@]}" | shuf))

# Split files
for i in "${!shuffled_files[@]}"; do
    base_name="${shuffled_files[$i]}"
    
    if [ $i -lt $train_count ]; then
        # Training set
        dest_dir="yolo_val_output/train"
    else
        # Validation set
        dest_dir="yolo_val_output/val"
    fi
    
    # Copy image files (handle multiple extensions)
    cp yolo_output/images/${base_name}.jpg "$dest_dir/images/" 2>/dev/null
    cp yolo_output/images/${base_name}.jpeg "$dest_dir/images/" 2>/dev/null
    cp yolo_output/images/${base_name}.png "$dest_dir/images/" 2>/dev/null
    
    # Copy corresponding label file
    cp yolo_output/labels/${base_name}.txt "$dest_dir/labels/" 2>/dev/null
done

# Final count verification
yolo_images=$(find yolo_output/images -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
yolo_labels=$(find yolo_output/labels -name "*.txt" | wc -l)
labelme_files=$(find labelme_output -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)

train_images=$(find yolo_val_output/train/images -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
train_labels=$(find yolo_val_output/train/labels -name "*.txt" | wc -l)
val_images=$(find yolo_val_output/val/images -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
val_labels=$(find yolo_val_output/val/labels -name "*.txt" | wc -l)

echo -e "${GREEN}Pipeline completed successfully!${NC}"
echo -e "${GREEN}YOLO format: $yolo_images images, $yolo_labels labels${NC}"
echo -e "${GREEN}LabelMe format: $labelme_files files${NC}"
echo -e "${GREEN}Training set: $train_images images, $train_labels labels${NC}"
echo -e "${GREEN}Validation set: $val_images images, $val_labels labels${NC}"
echo -e "${BLUE}Files are ready for training and review${NC}"