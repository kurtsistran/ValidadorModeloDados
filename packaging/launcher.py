"""PyInstaller entry point for the desktop application."""

import sys

from data_model_auditor.bootstrap.desktop import main

if __name__ == "__main__":
    sys.exit(main())
