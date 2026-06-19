# setup_wizard.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QVBoxLayout, QHBoxLayout, QApplication, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt

# FIXED imports
from GUI.config_manager import AppConfig, ensure_tree
from GUI.ollama_manager import (
    list_ollama_models,
    is_ollama_installed,
    open_ollama_download_page,
    DEFAULT_MODEL
)

from pathlib import Path
import sys


class SetupWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhiRAG - Setup Wizard")
        self.setFixedSize(820, 430)
        self.result = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel(
            "Choose runtime paths. These folders persist across restarts and reinstalls."
        ))
        self.root_edit = QLineEdit()
        browse_btn = QPushButton("Browse Root...")
        browse_btn.clicked.connect(lambda: self.browse_folder(self.root_edit, self.apply_root_defaults))
        row = QHBoxLayout()
        row.addWidget(self.root_edit)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        form = QFormLayout()
        self.runtime_data_edit = self._path_row(form, "Runtime data folder:")
        self.faiss_edit = self._path_row(form, "FAISS index location:")
        self.backend_edit = self._path_row(form, "Backend ingestion folder:")
        self.watchdog_edit = self._path_row(form, "Watchdog monitored folder:")
        self.logs_edit = self._path_row(form, "Logs folder:")
        layout.addLayout(form)

        layout.addWidget(QLabel("Ollama status / model:"))
        model_row = QHBoxLayout()
        self.model_combo = QComboBox()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ollama_models)
        model_row.addWidget(self.model_combo)
        model_row.addWidget(refresh_btn)
        layout.addLayout(model_row)

        self.install_btn = QPushButton("Install Ollama (Open download page)")
        self.install_btn.clicked.connect(open_ollama_download_page)
        self.install_btn.setEnabled(not is_ollama_installed())
        layout.addWidget(self.install_btn)

        self.refresh_ollama_models()

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

    def _path_row(self, form, label):
        edit = QLineEdit()
        button = QPushButton("Browse...")
        button.clicked.connect(lambda: self.browse_folder(edit))
        row = QHBoxLayout()
        row.addWidget(edit)
        row.addWidget(button)
        form.addRow(QLabel(label), row)
        return edit

    def browse_folder(self, target_edit, callback=None):
        d = QFileDialog.getExistingDirectory(
            self, "Select folder"
        )
        if d:
            target_edit.setText(d)
            if callback:
                callback()

    def apply_root_defaults(self):
        root = self.root_edit.text().strip()
        if not root:
            return
        root_p = Path(root).resolve()
        defaults = {
            self.runtime_data_edit: root_p / "runtime_data",
            self.faiss_edit: root_p / "faiss_index",
            self.backend_edit: root_p / "watchdog",
            self.watchdog_edit: root_p / "watchdog",
            self.logs_edit: root_p / "logs",
        }
        for edit, path in defaults.items():
            if not edit.text().strip():
                edit.setText(str(path))

    def refresh_ollama_models(self):
        models = list_ollama_models()
        if models:
            self.model_combo.clear()
            self.model_combo.addItems(models)
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
        self.apply_root_defaults()
        try:
            ensure_tree(root_p)
            paths = {
                "runtime_data_path": Path(self.runtime_data_edit.text().strip()).resolve(),
                "faiss_path": Path(self.faiss_edit.text().strip()).resolve(),
                "faiss_backend_path": Path(self.faiss_edit.text().strip()).resolve(),
                "watchdog_path": Path(self.watchdog_edit.text().strip()).resolve(),
                "backend_ingestion_path": Path(self.backend_edit.text().strip()).resolve(),
                "logs_path": Path(self.logs_edit.text().strip()).resolve(),
                "metadata_path": root_p / "metadata",
            }
            for path in paths.values():
                path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Creating Folder Structure",
                f"Failed to create the required folders under '{root}':\n{e}\n\nPlease choose a different folder or run as administrator."
            )
            return

        model_choice = self.model_combo.currentText().strip()
        if model_choice.startswith("(none detected)"):
            model_choice = DEFAULT_MODEL

        self.result = {
            "root": str(root_p),
            "watchdog_path": str(paths["watchdog_path"]),
            "backend_ingestion_path": str(paths["backend_ingestion_path"]),
            "faiss_path": str(paths["faiss_path"]),
            "faiss_backend_path": str(paths["faiss_backend_path"]),
            "runtime_data_path": str(paths["runtime_data_path"]),
            "metadata_path": str(paths["metadata_path"]),
            "logs_path": str(paths["logs_path"]),
            "ollama_model": model_choice,
            "ollama_url": "http://127.0.0.1:11434",
        }
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


