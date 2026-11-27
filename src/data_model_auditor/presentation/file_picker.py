"""A labeled path field with a browse button."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget


class FilePicker(QWidget):
    """Read-only path plus buttons to choose or clear a file."""

    changed = Signal()

    def __init__(self, file_filter: str, *, optional: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._filter = file_filter
        self._path = QLineEdit()
        self._path.setReadOnly(True)
        self._path.setPlaceholderText("Opcional" if optional else "Obrigatório")
        browse = QPushButton("Escolher...")
        browse.clicked.connect(self._browse)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._path)
        layout.addWidget(browse)
        if optional:
            clear = QPushButton("Limpar")
            clear.clicked.connect(lambda: self.set_path(None))
            layout.addWidget(clear)

    def path(self) -> Path | None:
        """The chosen file, if any."""
        text = self._path.text().strip()
        return Path(text) if text else None

    def set_path(self, path: Path | None) -> None:
        """Show ``path`` and notify listeners."""
        self._path.setText("" if path is None else str(path))
        self.changed.emit()

    def _browse(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Escolher arquivo", "", self._filter)
        if chosen:
            self.set_path(Path(chosen))
