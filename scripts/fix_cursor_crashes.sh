#!/bin/bash
#
# Quick script to fix Cursor crashes with large repositories
# This script cleans temporary files, stops background processes, 
# cleans caches, and restarts Cursor
#

echo "🛠️ Fixing Cursor crashes..."

# Make script executable
chmod +x scripts/clean_workspace.py

# Kill any running background processes that might be using resources
echo "📱 Stopping background processes..."
pkill -f "python3 scripts/serve_checklist.py" || echo "No checklist server running"
pkill -f "python3 scripts/document_explorer.py" || echo "No document explorer running"

# Clean temporary files and caches
echo "🧹 Cleaning temporary files and caches..."
python3 scripts/clean_workspace.py --all

# Clear system caches related to Cursor
echo "🧼 Clearing system caches..."
if [[ -d ~/Library/Application\ Support/Cursor/Cache ]]; then
  rm -rf ~/Library/Application\ Support/Cursor/Cache/*
  echo "Cleared Cursor application cache"
fi

if [[ -d ~/Library/Application\ Support/Cursor/Code\ Cache ]]; then
  rm -rf ~/Library/Application\ Support/Cursor/Code\ Cache/*
  echo "Cleared Cursor code cache"
fi

if [[ -d ~/Library/Application\ Support/Cursor/GPUCache ]]; then
  rm -rf ~/Library/Application\ Support/Cursor/GPUCache/*
  echo "Cleared Cursor GPU cache"
fi

# Remind about the .cursorignore file
echo "📝 Checking .cursorignore file..."
if [[ -f .cursorignore ]]; then
  echo "✅ .cursorignore file is in place"
else
  echo "❌ .cursorignore file is missing! Creating one..."
  cat > .cursorignore << EOL
# Tell Cursor not to index these large directories
scrapers_output/
.venv/
.venv-explorer/
**/node_modules/
**/__pycache__/
**/.pytest_cache/
**/.ipynb_checkpoints/

# Large files that shouldn't be indexed
**/*.pdf
**/*.rtf
**/*.doc
**/*.docx
**/*.zip
**/*.gz
**/*.tar
**/*.mp4
**/*.mov

# Temporary and log files
**/nohup.out
**/*.log
**/*.tmp
**/all_pdfs.txt
EOL
  echo "✅ Created .cursorignore file"
fi

# Create .cursor-settings directory if it doesn't exist
if [[ ! -d .cursor-settings ]]; then
  mkdir -p .cursor-settings
fi

# Check Cursor settings
echo "⚙️ Checking Cursor settings..."
if [[ -f .cursor-settings/settings.json ]]; then
  echo "✅ Cursor settings file is in place"
else
  echo "❌ Cursor settings file is missing! Creating one..."
  cat > .cursor-settings/settings.json << EOL
{
  "editor.fontSize": 14,
  "editor.minimap.enabled": false,
  "workbench.editor.limit.enabled": true,
  "workbench.editor.limit.value": 10,
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.venv/**": true,
    "**/.venv-explorer/**": true,
    "**/scrapers_output/**": true,
    "**/*.pdf": true,
    "**/*.rtf": true,
    "**/*.doc": true,
    "**/*.docx": true,
    "**/*.zip": true,
    "**/*.tar": true,
    "**/*.gz": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/*.code-search": true,
    "**/.venv/**": true,
    "**/.venv-explorer/**": true,
    "**/scrapers_output/**": true,
    "**/*.pdf": true,
    "**/*.rtf": true,
    "**/*.doc": true,
    "**/*.docx": true
  },
  "files.exclude": {
    "**/.git": true,
    "**/.svn": true,
    "**/.hg": true,
    "**/CVS": true,
    "**/.DS_Store": true,
    "**/Thumbs.db": true,
    "**/.venv": true,
    "**/.venv-explorer": true,
    "**/scrapers_output": false
  },
  "editor.formatOnSave": false,
  "cursor.perfMode": true,
  "cursor.trainingMode": false
}
EOL
  echo "✅ Created Cursor settings file"
fi

# Make the script executable
chmod +x scripts/fix_cursor_crashes.sh

echo "✅ All done! Restart Cursor for the changes to take effect."
echo "   To fix crashes in the future, just run: ./scripts/fix_cursor_crashes.sh" 