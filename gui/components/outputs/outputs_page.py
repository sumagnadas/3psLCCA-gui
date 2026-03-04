"""
gui/components/outputs/outputs_page.py
"""

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from gui.components.base_widget import ScrollableForm
from gui.components.utils.form_builder.form_definitions import ValidationStatus

CHUNK = "outputs_data"


class OutputsPage(ScrollableForm):

    navigate_requested = Signal(str)

    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name=CHUNK)
        self._pages = {}
        self._build_ui()

    def _build_ui(self):
        f = self.form
        header = QLabel("Outputs")
        bold = QFont()
        bold.setBold(True)
        bold.setPointSize(13)
        header.setFont(bold)
        f.addRow(header)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 8, 0, 8)

        self.btn_calculate = QPushButton("Validate  ▶")
        self.btn_calculate.setMinimumHeight(38)
        self.btn_calculate.setFixedWidth(160)
        self.btn_calculate.clicked.connect(self.run_validation)
        btn_layout.addWidget(self.btn_calculate)
        btn_layout.addStretch()
        f.addRow(btn_row)

        self._status_widget = QWidget()
        self._status_layout = QVBoxLayout(self._status_widget)
        self._status_layout.setContentsMargins(0, 0, 0, 0)
        f.addRow(self._status_widget)

        self._show_idle()

    # ── Status area ───────────────────────────────────────────────────────────

    def _clear_status(self):
        while self._status_layout.count():
            item = self._status_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)

    def _show_idle(self):
        self._clear_status()
        note = QLabel("Press Calculate to validate all pages.")
        note.setStyleSheet("color: gray; font-style: italic;")
        self._status_layout.addWidget(note)

    def show_results(self, all_errors: dict, all_warnings: dict):
        """Show errors and warnings together. Proceed button only when no errors."""
        self._clear_status()

        if all_errors:
            banner = QGroupBox()
            banner.setStyleSheet("QGroupBox { border: 2px solid #dc3545; padding: 8px; }")
            layout = QVBoxLayout(banner)
            title = QLabel("🛑  Calculation Blocked — Please fix the errors below.")
            title.setStyleSheet("color: #b02a37; font-weight: bold;")
            layout.addWidget(title)
            self._status_layout.addWidget(banner)
            self._status_layout.addSpacing(10)

            for page, issues in all_errors.items():
                self._status_layout.addWidget(self._create_card(page, issues, "❌"))

        if all_warnings:
            if all_errors:
                self._status_layout.addSpacing(12)
            banner = QGroupBox()
            banner.setStyleSheet("QGroupBox { border: 2px solid #ffc107; padding: 8px; }")
            layout = QVBoxLayout(banner)
            label = "⚠️  Warnings — fix errors above before proceeding." if all_errors \
                else "⚠️  Warnings — Data looks unusual but you can proceed."
            title = QLabel(label)
            title.setStyleSheet("color: #856404; font-weight: bold;")
            layout.addWidget(title)
            self._status_layout.addWidget(banner)
            self._status_layout.addSpacing(10)

            for page, issues in all_warnings.items():
                self._status_layout.addWidget(self._create_card(page, issues, "🟡"))

        if not all_errors and all_warnings:
            run_btn = QPushButton("Proceed with Calculation ▶")
            run_btn.setMinimumHeight(35)
            run_btn.clicked.connect(self._on_proceed)
            self._status_layout.addWidget(run_btn)

        self._status_layout.addStretch()
        self._save_state("issues", {"errors": all_errors, "warnings": all_warnings})

    def show_success(self):
        self._clear_status()
        banner = QGroupBox()
        banner.setStyleSheet("QGroupBox { border: 2px solid #198754; padding: 8px; }")
        layout = QVBoxLayout(banner)
        layout.addWidget(QLabel("✅  All checks passed — Ready to calculate."))
        self._status_layout.addWidget(banner)
        self._status_layout.addStretch()
        self._save_state("success", {"errors": {}, "warnings": {}})

    # ── Validation / calculation ───────────────────────────────────────────────

    def register_pages(self, widget_map: dict):
        self._pages = {
            name: page
            for name, page in widget_map.items()
            if name != "Outputs" and hasattr(page, "validate")
        }

    def run_validation(self):
        all_errors = {}
        all_warnings = {}

        for name, page in self._pages.items():
            result = page.validate()

            if isinstance(result, dict):
                errors = result.get("errors", [])
                warnings = result.get("warnings", [])
                if errors:
                    all_errors[name] = errors
                if warnings:
                    all_warnings[name] = warnings
            else:
                # legacy tuple format (status, issues)
                status, issues = result
                if status == ValidationStatus.ERROR and issues:
                    all_errors[name] = issues
                elif status == ValidationStatus.WARNING and issues:
                    all_warnings[name] = issues

        if all_errors or all_warnings:
            self.show_results(all_errors, all_warnings)
        else:
            self.show_success()
            self.run_calculation()

    def run_calculation(self):
        all_data = {}
        for name, page in self._pages.items():
            if hasattr(page, "get_data"):
                result = page.get_data()
                all_data[result["chunk"]] = result["data"]
        # TODO: pass all_data to calculator
        print("Calculation data:", all_data)

    def _on_proceed(self):
        self.run_calculation()

    # ── Card widget ───────────────────────────────────────────────────────────

    def _create_card(self, page_name, issues, icon):
        card = QGroupBox()
        card.setStyleSheet(
            "QGroupBox { border: 1px solid #dee2e6; border-radius: 4px; }"
        )
        layout = QVBoxLayout(card)

        h_row = QWidget()
        h_lay = QHBoxLayout(h_row)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.addWidget(QLabel(f"<b>{page_name}</b>"))
        h_lay.addStretch()

        go_btn = QPushButton("Go →")
        go_btn.setFixedWidth(60)
        go_btn.clicked.connect(
            lambda checked=False, p=page_name: self.navigate_requested.emit(p)
        )
        h_lay.addWidget(go_btn)

        layout.addWidget(h_row)
        for msg in issues:
            layout.addWidget(QLabel(f"{icon} {msg}"))
        return card

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_state(self, status: str, data: dict):
        if self.controller and self.controller.engine:
            self.controller.engine.stage_update(
                chunk_name=self.chunk_name, data={"status": status, "data": data}
            )

    def on_refresh(self):
        if not self.controller or not self.controller.engine:
            return
        state = self.controller.engine.fetch_chunk(CHUNK) or {}
        status = state.get("status", "idle")
        data = state.get("data", {})
        if status == "issues":
            self.show_results(data.get("errors", {}), data.get("warnings", {}))
        elif status == "success":
            self.show_success()
        else:
            self._show_idle()
