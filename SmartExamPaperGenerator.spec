# PyInstaller build recipe. Build this on the operating system you target.
# Command: pyinstaller --clean --noconfirm SmartExamPaperGenerator.spec

from PyInstaller.utils.hooks import collect_all

fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all('fitz')
docx_datas, docx_binaries, docx_hiddenimports = collect_all('docx')
reportlab_datas, reportlab_binaries, reportlab_hiddenimports = collect_all('reportlab')

analysis = Analysis(
    ['app.py'],
    pathex=[],
    binaries=fitz_binaries + docx_binaries + reportlab_binaries,
    datas=fitz_datas + docx_datas + reportlab_datas,
    hiddenimports=fitz_hiddenimports + docx_hiddenimports + reportlab_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name='SmartExamPaperGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
