from PySide6.QtWidgets import (
    QLineEdit,
    QComboBox,
    QTextEdit,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Signal, Qt

from gui.components.base_widget import ScrollableForm
from ..utils.countries_data import CURRENCIES, COUNTRIES


BASE_DOCS_URL = "https://yourdocs.com/general/"

# (key, title, explanation, field_type, options, is_required, doc_slug)
GENERAL_FIELDS = [
    # ── Project Information ──────────────────────────────────────────
    (
        "_section_project",
        "Project Information",
        None,
        "section",
        None,
        False,
        None,
    ),
    (
        "project_name",
        "Project Name",
        "Official name or title of the bridge/infrastructure project.",
        "text",
        None,
        True,
        "project-name",
    ),
    (
        "project_code",
        "Project Code",
        "Unique reference code assigned to this project.",
        "text",
        None,
        False,
        "project-code",
    ),
    (
        "project_description",
        "Project Description",
        "Brief description of the project scope, objectives, or background.",
        "textarea",
        None,
        False,
        "project-description",
    ),
    (
        "remarks",
        "Remarks",
        "Any additional notes, assumptions, or comments relevant to this evaluation.",
        "textarea",
        None,
        False,
        "remarks",
    ),
    # ── Evaluating Agency ────────────────────────────────────────────
    (
        "_section_agency",
        "Evaluating Agency",
        None,
        "section",
        None,
        False,
        None,
    ),
    (
        "agency_name",
        "Agency Name",
        "Name of the organization or firm responsible for this LCCA evaluation.",
        "text",
        None,
        True,
        "agency-name",
    ),
    (
        "contact_person",
        "Contact Person",
        "Name of the primary contact or evaluator handling this project.",
        "text",
        None,
        False,
        "contact-person",
    ),
    (
        "agency_address",
        "Agency Address",
        "Street address of the evaluating agency.",
        "text",
        None,
        False,
        "agency-address",
    ),
    (
        "agency_country",
        "Country",
        "Country where the evaluating agency is based.",
        "combo",
        COUNTRIES,
        False,
        "agency-country",
    ),
    (
        "agency_email",
        "Email",
        "Official email address for correspondence regarding this evaluation.",
        "text",
        None,
        False,
        "agency-email",
    ),
    (
        "agency_phone",
        "Phone",
        "Contact phone number for the evaluating agency or person.",
        "text",
        None,
        False,
        "agency-phone",
    ),
    # ── Project Settings ─────────────────────────────────────────────
    (
        "_section_settings",
        "Project Settings",
        None,
        "section",
        None,
        False,
        None,
    ),
    (
        "currency",
        "Currency",
        "Currency used for all cost figures in this project.",
        "combo",
        CURRENCIES,
        True,
        "currency",
    ),
    (
        "unit_system",
        "Unit System",
        "Measurement system used throughout the project.",
        "combo",
        ["Metric (SI)", "Imperial (US)"],
        True,
        "unit-system",
    ),
]


class GeneralInfo(ScrollableForm):

    created = Signal()  # Kept for compatibility with ProjectWindow state management

    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="general_info")

        self.required_keys = []

        for field_def in GENERAL_FIELDS:
            key, title, explanation, field_type, options, is_required, doc_slug = (
                field_def
            )

            # ── Section Header ───────────────────────────────────────
            if field_type == "section":
                header = QLabel(title)
                header.setStyleSheet(
                    "font-size: 13px; font-weight: 700; "
                    "padding-top: 14px; padding-bottom: 2px;"
                )
                self.form.addRow(header)

                divider = QWidget()
                divider.setFixedHeight(1)
                divider.setStyleSheet("background-color: #d0d0d0;")
                self.form.addRow(divider)
                continue

            # ── Field Section ────────────────────────────────────────
            section = QWidget()
            layout = QVBoxLayout(section)
            layout.setContentsMargins(0, 8, 0, 8)
            layout.setSpacing(4)

            # Title
            title_label = QLabel(f"{title} *" if is_required else title)
            title_label.setStyleSheet("font-weight: 600;")
            layout.addWidget(title_label)

            # Explanation + docs link
            if explanation:
                doc_url = f"{BASE_DOCS_URL}{doc_slug}"
                explanation_html = (
                    explanation
                    + f' <a href="{doc_url}" style="text-decoration:none;font-weight:600;"> ⓘ</a>'
                )
                explanation_label = QLabel(explanation_html)
                explanation_label.setWordWrap(True)
                explanation_label.setTextFormat(Qt.RichText)
                explanation_label.setOpenExternalLinks(True)
                layout.addWidget(explanation_label)

            # Input
            if field_type == "text":
                widget = QLineEdit()
                widget.setMinimumHeight(30)
                setattr(self, key, self.field(key, widget))
                widget.textChanged.connect(lambda _, w=widget: w.setStyleSheet(""))

            elif field_type == "textarea":
                widget = QTextEdit()
                widget.setMinimumHeight(80)
                widget.setMaximumHeight(120)
                setattr(self, key, self.field(key, widget))

            elif field_type == "combo":
                widget = QComboBox()
                widget.addItems(options)
                widget.setMinimumHeight(30)
                setattr(self, key, self.field(key, widget))
                widget.currentIndexChanged.connect(
                    lambda _, w=widget: w.setStyleSheet("")
                )

            if is_required:
                self.required_keys.append(key)

            layout.addWidget(widget)
            self.form.addRow(section)

        # ── Buttons Row ──────────────────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 10, 0, 10)
        btn_layout.setSpacing(10)

        # self.btn_load_suggested = QPushButton("Load Suggested Values")
        # self.btn_load_suggested.setMinimumHeight(35)
        # self.btn_load_suggested.clicked.connect(self.load_suggested_values)

        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.setMinimumHeight(35)
        self.btn_clear_all.clicked.connect(self.clear_all)

        # btn_layout.addWidget(self.btn_load_suggested)
        btn_layout.addWidget(self.btn_clear_all)
        self.form.addRow(btn_row)

    # ------------------------------------------------------------------
    # Suggested values
    # ------------------------------------------------------------------
    # def load_suggested_values(self):
    #     defaults = {
    #         "currency": "USD — US Dollar",
    #         "unit_system": "Metric (SI)",
    #     }
    #     for key, val in defaults.items():
    #         widget = getattr(self, key, None)
    #         if widget is None:
    #             continue
    #         if isinstance(widget, QComboBox):
    #             idx = widget.findText(val)
    #             if idx >= 0:
    #                 widget.setCurrentIndex(idx)
    #         elif isinstance(widget, QLineEdit):
    #             widget.setText(val)
    #         widget.setStyleSheet("")

    #     self._on_field_changed()

    #     if self.controller and self.controller.engine:
    #         self.controller.engine._log("General Info: Suggested values applied.")

    # ------------------------------------------------------------------
    # Clear all
    # ------------------------------------------------------------------
    def clear_all(self):
        for field_def in GENERAL_FIELDS:
            key, _, _, field_type, _, _, _ = field_def
            if field_type == "section":
                continue
            widget = getattr(self, key, None)
            if widget is None:
                continue
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            widget.setStyleSheet("")

        self._on_field_changed()

        if self.controller and self.controller.engine:
            self.controller.engine._log("General Info: All fields cleared.")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self):
        errors = []

        for key in self.required_keys:
            widget = getattr(self, key, None)
            if widget is None:
                continue

            empty = False
            if isinstance(widget, QLineEdit):
                empty = widget.text().strip() == ""
            elif isinstance(widget, QComboBox):
                empty = False

            if empty:
                label = next(f[1] for f in GENERAL_FIELDS if f[0] == key)
                errors.append(label)
                widget.setStyleSheet("border: 1px solid red;")

        if errors:
            msg = f"Missing required general info: {', '.join(errors)}"
            if self.controller and self.controller.engine:
                self.controller.engine._log(msg)
            return False, errors

        return True, []

    # ------------------------------------------------------------------
    # Override to also emit created signal
    # ------------------------------------------------------------------
    def _on_field_changed(self):
        super()._on_field_changed()
        self.created.emit()
