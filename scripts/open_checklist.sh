#!/bin/bash
# Script to open the SA Legal LLM Checklist

# Determine which editor to use
if command -v code &> /dev/null; then
    # Visual Studio Code is installed
    code SA_LEGAL_LLM_CHECKLIST.md
elif command -v atom &> /dev/null; then
    # Atom is installed
    atom SA_LEGAL_LLM_CHECKLIST.md
elif command -v subl &> /dev/null; then
    # Sublime Text is installed
    subl SA_LEGAL_LLM_CHECKLIST.md
elif command -v gedit &> /dev/null; then
    # Gedit is installed
    gedit SA_LEGAL_LLM_CHECKLIST.md
elif command -v nano &> /dev/null; then
    # Nano is installed
    nano SA_LEGAL_LLM_CHECKLIST.md
elif command -v vim &> /dev/null; then
    # Vim is installed
    vim SA_LEGAL_LLM_CHECKLIST.md
else
    # Default to open command on macOS
    open SA_LEGAL_LLM_CHECKLIST.md
fi

echo "Opening SA Legal LLM Checklist..." 