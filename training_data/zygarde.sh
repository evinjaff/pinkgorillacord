#!/bin/bash
# Simple script to get JPEGs put into PNGs to mantain order for real_assets folder

# Check if a directory path is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <directory_path>"
    exit 1
fi

DIR="$1"

# Navigate to the specified directory
if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$DIR' not found."
    exit 1
fi
cd "$DIR" || exit

# Loop through all JPEG files in the directory
for i in *.jpeg *.jpg; do
    # Check if the file exists (to handle cases where no JPEGs are present)
    if [ -f "$i" ]; then
        # Construct the new filename with .png extension
        j="${i%.*}.png"
        echo "Converting \"$i\" to \"$j\"..."
        # Convert the image using sips
        sips -s format png "$i" --out "$j"
    fi
done

echo "Conversion complete."
