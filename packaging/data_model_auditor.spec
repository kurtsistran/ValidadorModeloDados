# PyInstaller spec for the local MVP. Build with packaging/build_installer.ps1.
# The rules folder is copied next to the executable by the build script, because
# default_rules_path() looks for it there and analysts may need to find it.

from pathlib import Path

ROOT = Path(SPECPATH).parent

# The desktop flow uses neither the API stack nor the developer tools.
EXCLUDED = [
    "fastapi",
    "starlette",
    "uvicorn",
    "httpx",
    "pytest",
    "mypy",
    "ruff",
    "tkinter",
    "matplotlib",
    "IPython",
]

analysis = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    excludes=EXCLUDED,
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="DataModelAuditor",
    console=False,
    upx=False,
)
COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    name="DataModelAuditor",
    upx=False,
)
