## Smart Exam Paper Generator

A beginner-friendly, cross-platform Python + Tkinter desktop application for building examination papers from a question bank. The project is supplied both as readable source code (for learning/review) and with instructions for packaging a standalone app.

## Features

- Import text-based PDF, DOCX and TXT question banks.
- Recognize question groups under 2-, 5- and 10-mark headings.
- Add questions manually and review extracted questions.
- Configure exam details and section patterns.
- Randomly select questions without repeating identical question text in one paper.
- Edit, replace, remove and reorder selected questions.
- Preview a generated PDF using the computer's default PDF viewer.
- Export a formatted A4 PDF.
- Scrollable Exam Setup tab and built-in teacher help.

## Choose how to run it

### Option 1 — Quick test from source (requires Python)

**Linux:** double-click `launch_linux.sh` if your desktop allows shell scripts to run, or run:

```bash
chmod +x launch_linux.sh
./launch_linux.sh
```

On first launch, the script creates `.venv` and installs the packages. Later launches reuse that environment and do not reinstall packages. If dependencies in `requirements.txt` change, activate the environment and run `python -m pip install -r requirements.txt` again.

If virtual-environment creation fails on Debian/Ubuntu, install the system packages first:

```bash
sudo apt install python3-tk python3-venv
```

Other Linux distributions may use different package names.

**Windows:** double-click `launch_windows.bat`. It creates a local virtual environment and installs dependencies on first launch. Python 3 must already be installed; download it from https://www.python.org/downloads/windows/ and enable the PATH option during installation. Tkinter is normally included with the standard Windows Python installer.

**macOS:** install Python 3 with Tkinter support, then open Terminal in this folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

The source application and dependencies should work across these operating systems, but the app should be tested on the actual target OS before distributing it widely.

### Option 2 — Standalone desktop app (no manual Python/pip setup for the teacher)

PyInstaller bundles the Python runtime and project dependencies. Build a separate package on each target operating system; do not copy a Windows executable to Linux or macOS and expect it to work.

1. On the operating system you want to package, install Python 3 and Tkinter support.
2. Open a terminal in this project folder and create/activate a virtual environment as shown above.
3. Install build dependencies:

```bash
python -m pip install -r requirements-build.txt
```

4. Build the application:

```bash
pyinstaller --clean --noconfirm SmartExamPaperGenerator.spec
```

5. The output is placed in `dist/SmartExamPaperGenerator/` or `dist/SmartExamPaperGenerator` depending on the PyInstaller spec and platform. Test the result on a clean account/computer of that same OS before sharing it.

- **Windows:** build on Windows; distribute the generated app folder (or zip that folder).
- **Linux:** build on Linux; distribute the generated app folder (or zip that folder). Linux system-library compatibility can vary by distribution.
- **macOS:** build on macOS; distribute the generated `.app`/output produced there. Signing/notarization may be needed for wider distribution.

The `.spec` file is a build recipe, not the application source. `app.py` remains the main readable file teachers can review. You can still edit `app.py`, run it from source, and rebuild the standalone package.

## Project files

- `app.py` — main application and GUI logic.
- `requirements.txt` — libraries needed to run from source.
- `requirements-build.txt` — runtime dependencies plus PyInstaller for packaging.
- `SmartExamPaperGenerator.spec` — PyInstaller packaging configuration.
- `launch_linux.sh` — convenient Linux source launcher.
- `launch_windows.bat` — convenient Windows source launcher.
- `sample_bank.txt` — example question-bank format.

## Preparing a question bank

Use a clear heading for each marks category and number questions with a number followed by a period. Example:

```text
2 MARK QUESTIONS
1. Define Python.
2. What is a variable?

5 MARK QUESTIONS
1. Explain the features of Python.
2. Describe list slicing with an example.

10 MARK QUESTIONS
1. Explain object-oriented programming in Python with examples.
```

Questions inherit the marks from the recognized heading above them. A question can continue on following lines; start the next question with a number and period.

## Preview behavior

The app generates a temporary PDF and asks the operating system to open it with its default PDF viewer. Linux uses an available opener such as `xdg-open`; Windows uses the registered PDF handler; macOS uses `open`. A PDF viewer should be installed. If opening fails, export the PDF and open it manually.

## Important limitations

- Scanned/image-only PDFs are not reliably readable because OCR is not included.
- Complex tables, multi-column documents, and nested numbering may need manual cleanup.
- Extraction accuracy is not universal. Always review imported questions and the final paper.
- Standalone builds need to be built and tested separately for each operating system.

## Quick test

Import `sample_bank.txt`, configure a pattern whose required question counts are available in the sample, generate the paper, edit or reorder a question, preview it, and export a PDF.
