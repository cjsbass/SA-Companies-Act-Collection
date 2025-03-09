#!/bin/bash

# This script creates an optimized repository structure by:
# 1. Creating a code-only repository in your home directory
# 2. Moving large data files to an external location (optional)
# 3. Setting up symbolic links to maintain functionality

# Exit on error
set -e

# Define paths
CODE_REPO="$HOME/Documents/SA-companies-code"
DATA_DIR="$HOME/Documents/SA-companies-data"

# Create directories if they don't exist
mkdir -p "$CODE_REPO"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/scrapers_output"

echo "=== Setting up optimized repository structure ==="
echo "Code repository: $CODE_REPO"
echo "Data directory: $DATA_DIR"

# Copy code files to the code repository
echo "Copying code files to $CODE_REPO..."
rsync -av --progress \
  --exclude=".git/" \
  --exclude=".venv/" \
  --exclude="scrapers_output/" \
  --exclude="*.pdf" \
  --exclude="*.rtf" \
  --exclude="*.doc" \
  --exclude="*.docx" \
  --exclude="*.html" \
  --exclude="downloads/" \
  --exclude="logs/" \
  --exclude="__pycache__/" \
  --exclude=".cursor/" \
  ./ "$CODE_REPO/"

# Move large data directories to the data directory
echo "Moving scrapers_output to $DATA_DIR..."
if [ -d "scrapers_output" ]; then
  rsync -av --progress scrapers_output/ "$DATA_DIR/scrapers_output/"
  echo "Data files moved successfully."
else
  echo "scrapers_output directory not found, skipping."
fi

# Create symbolic links in the code repository
echo "Creating symbolic links for data directories..."
cd "$CODE_REPO"
ln -sf "$DATA_DIR/scrapers_output" scrapers_output

# Set up git in the code repository
echo "Setting up git in the code repository..."
cd "$CODE_REPO"
if [ ! -d ".git" ]; then
  git init
  git add .
  git commit -m "Initial commit of code-only repository"
  echo "Git repository initialized."
else
  echo "Git repository already exists."
fi

echo ""
echo "=== Repository setup complete ==="
echo ""
echo "To use the optimized repository:"
echo "1. Open Cursor with the code-only repository:"
echo "   cursor $CODE_REPO"
echo ""
echo "2. Your data files are now stored at:"
echo "   $DATA_DIR"
echo ""
echo "3. The symbolic links ensure that your code can still access the data files."
echo ""
echo "IMPORTANT: This is a one-time copy. Any changes you make to the original files"
echo "will not be reflected in the new repository. You should work exclusively with"
echo "the new repository from now on." 