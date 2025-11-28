# setup_wizard.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QVBoxLayout, QHBoxLayout, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt
from config_manager import ensure_tree, AppConfig, default_subfolders
from ollama_manager import list_ollama_models, is_ollama_installed, open_ollama_download_page, DEFAULT_MODEL
from pathlib import Path
import sys

class SetupWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhiRAG - Setup Wizard")
        self.setFixedSize(720, 240)
        self.result = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Choose root folder for PhiRAG data (we will create the canonical subfolders):"))
        self.root_edit = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        row = QHBoxLayout()
        row.addWidget(self.root_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        layout.addWidget(QLabel("Ollama status / model:"))
        model_row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.refresh_ollama_models()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ollama_models)
        model_row.addWidget(self.model_combo)
        model_row.addWidget(refresh_btn)
        layout.addLayout(model_row)

        self.install_btn = QPushButton("Install Ollama (Open download page)")
        self.install_btn.clicked.connect(open_ollama_download_page)
        self.install_btn.setEnabled(not is_ollama_installed())
        layout.addWidget(self.install_btn)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.on_cancel)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def browse_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select root folder (or choose an existing folder)")
        if d:
            self.root_edit.setText(d)

    def refresh_ollama_models(self):
        models = list_ollama_models()
        if models:
            self.model_combo.clear()
            self.model_combo.addItems(models)
            # try to select DEFAULT_MODEL if present
            try:
                idx = models.index(DEFAULT_MODEL)
                self.model_combo.setCurrentIndex(idx)
            except ValueError:
                pass
            self.install_btn.setEnabled(False)
        else:
            self.model_combo.clear()
            self.model_combo.addItem(f"(none detected) - default: {DEFAULT_MODEL}")
            self.install_btn.setEnabled(True)

    def on_ok(self):
        root = self.root_edit.text().strip()
        if not root:
            QMessageBox.critical(self, "Missing folder", "Please choose a root folder.")
            return
        root_p = Path(root).resolve()
        # force-create standard tree
        created = ensure_tree(root_p)
        # determine model choice
        model_choice = self.model_combo.currentText().strip()
        if model_choice.startswith("(none detected)"):
            model_choice = DEFAULT_MODEL
        cfg = {
            "root": created["root"],
            "watchdog_path": created["watchdog_path"],
            "faiss_path": created["faiss_path"],
            "metadata_path": created["metadata_path"],
            "logs_path": created["logs_path"],
            "ollama_model": model_choice,
            "ollama_url": "http://127.0.0.1:11434"
        }
        self.result = cfg
        self.close()

    def on_cancel(self):
        self.result = None
        self.close()

def run_wizard_sync():
    app = QApplication.instance() or QApplication(sys.argv)
    w = SetupWizard()
    w.show()
    app.exec()
    return w.result
