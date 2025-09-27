#!/bin/bash
cd "$(dirname "$0")"
/home/dian/Projects/ChemistryOS/.venv/bin/python src/chemistry_os/src/main.py
echo "Script finished. Press any key to exit..."
read -n 1 -s
