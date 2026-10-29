#!/usr/bin/env bash
# First run creates a local virtual environment and installs dependencies.
set -e
cd "$(dirname "$(readlink -f "$0")")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required. Install Python 3 and Tkinter, then try again."
    read -r -p "Press Enter to close..."
    exit 1
fi

if [ ! -d .venv ]; then
    python3 -m venv .venv || {
        echo "Could not create the virtual environment. On Debian/Ubuntu try: sudo apt install python3-venv python3-tk"
        read -r -p "Press Enter to close..."
        exit 1
    }
    source .venv/bin/activate
    python -m pip install -r requirements.txt || exit 1
else
    source .venv/bin/activate
fi

exec python app.py
