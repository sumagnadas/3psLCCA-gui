# """
# gui\components\global_info\main.py
# """

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap

from ..base_widget import ScrollableForm
from ..utils.form_builder.form_definitions import FieldDef, Section
from ..utils.form_builder.form_builder import build_form, _IMG_PREVIEWS_ATTR, freeze_img_uploads
from ..utils.validation_helpers import clear_field_styles, freeze_form, freeze_widgets, validate_form
from ..utils.countries_data import CURRENCIES, COUNTRIES


from ..utils.doc_handler import make_doc_opener
_DOC_OPENER = make_doc_opener("general")


GENERAL_FIELDS = [
    # ── Project Information ──────────────────────────────────────────────
    Section("Project Information"),
    FieldDef(
        "project_name",
        "Project Name",
        "The official name of the bridge project. Appears in all reports and exports.",
        "text",
        required=True,
        doc_slug="project-name",
    ),
    FieldDef(
        "project_code",
        "Project Code",
        "A short identifier or reference code for internal tracking.",
        "text",
        doc_slug="project-code",
    ),
    FieldDef(
        "project_description",
        "Project Description",
        "A free-text summary of the project scope, objectives, and context.",
        "textarea",
        doc_slug="project-description",
    ),
    FieldDef(
        "remarks",
        "Remarks",
        "Additional notes or observations. Does not affect any calculations.",
        "textarea",
        doc_slug="remarks",
    ),
    # ── Evaluating Agency ────────────────────────────────────────────────
    Section("Evaluating Agency"),
    FieldDef(
        "agency_name",
        "Agency Name",
        "The name of the organisation or department responsible for this project. Appears in the report header.",
        "text",
        # required=True,
        doc_slug="agency-name",
    ),
    FieldDef(
        "contact_person",
        "Contact Person",
        "The name of the primary point of contact for this project within the agency.",
        "text",
        doc_slug="contact-person",
    ),
    FieldDef(
        "agency_address",
        "Agency Address",
        "The postal address of the agency or office handling this project. Appears in the report footer.",
        "text",
        doc_slug="agency-address",
    ),
    FieldDef(
        "agency_country",
        "Country",
        "Country where the evaluating agency is based. Used for report localisation.",
        "combo",
        options=COUNTRIES,
        doc_slug="agency-country",
    ),
    FieldDef(
        "agency_email",
        "Email",
        "The official email address for the agency or project team.",
        "text",
        doc_slug="agency-email",
    ),
    FieldDef(
        "agency_phone",
        "Phone",
        "The contact phone number for the agency or project team. Include country code where applicable.",
        "phone",
        doc_slug="agency-phone",
    ),
    FieldDef(
        "agency_logo",
        "Agency Logo",
        "Upload agency logo (JPG or PNG). Auto-resized to fit a 3 cm × 3 cm print area. Transparent PNG recommended.",
        "upload_img",
        options="default",
        doc_slug="agency-logo",
    ),
    # ── Project Settings ─────────────────────────────────────────────────
    Section("Project Settings"),
    FieldDef(
        "project_country",
        "Country",
        "Country where the bridge project is located. Set at project creation.",
        "text",
        doc_slug="project-country",
    ),
    FieldDef(
        "project_currency",
        "Currency",
        "Currency used for all cost inputs and outputs. Set at project creation.",
        "text",
        doc_slug="project-currency",
    ),
    FieldDef(
        "unit_system",
        "Unit System",
        "Measurement system for all dimensional inputs (Metric or Imperial). Set at project creation.",
        "text",
        doc_slug="unit-system",
    ),
    FieldDef(
        "sor_database",
        "Material Suggestions",
        "Schedule of Rates database used to auto-suggest material names, rates, and emission factors in the Material Dialog.",
        "combo",
        options=[],
        doc_slug="sor-database",
    ),
    # FieldDef(
    #     "currency_to_usd_rate",
    #     "Exchange Rate to USD",
    #     "Conversion rate from the selected currency to USD (1 unit of selected currency equals X USD).",
    #     "float",
    #     options=(0.0001, 1000.0, 6),
    #     unit="(USD)",
    #     required=True,
    #     doc_slug="currency-to-usd-rate",
    # ),
]


class GeneralInfo(ScrollableForm):

    created = Signal()

    _LOCKED = {"project_country", "project_currency", "unit_system"}
    # sor_database is editable but should not be wiped by Clear All
    _SKIP_CLEAR = _LOCKED | {"sor_database"}

    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="general_info")

        self.required_keys = build_form(self, GENERAL_FIELDS, _DOC_OPENER)

        # Lock country and currency — disable widget so user can't edit,
        # but keep in _field_map so get_data_dict() saves them normally
        self.required_keys = [k for k in self.required_keys if k not in self._LOCKED]
        for key in self._LOCKED:
            w = getattr(self, key, None)
            if w is not None:
                w.setEnabled(False)

        # ── Clear All button ─────────────────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 10, 0, 10)

        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.setMinimumHeight(35)
        self.btn_clear_all.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_clear_all)
        self.form.addRow(btn_row)

    # ── Clear All ────────────────────────────────────────────────────────
    def clear_all(self):
        for entry in GENERAL_FIELDS:
            if isinstance(entry, Section):
                continue
            if entry.key in self._SKIP_CLEAR:
                continue  # never clear locked or settings fields

            widget = getattr(self, entry.key, None)
            if widget is None:
                continue

            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(widget.minimum())

        # Reset all upload_img previews
        for key, preview in getattr(self, _IMG_PREVIEWS_ATTR, {}).items():
            preview.setPixmap(QPixmap())
            preview.setText("No image selected")

        self._on_field_changed()

    # ── Validation ───────────────────────────────────────────────────────
    def freeze(self, frozen: bool = True):
        freeze_form(GENERAL_FIELDS, self, frozen)
        freeze_img_uploads(self, GENERAL_FIELDS, frozen)
        freeze_widgets(frozen, self.btn_clear_all)

    def clear_validation(self):
        clear_field_styles(GENERAL_FIELDS, self)

    def validate(self):
        return validate_form(GENERAL_FIELDS, self)

    _UNIT_SYSTEM_LABELS = {
        "metric":   "Metric SI",
        "imperial": "Imperial (English)",
    }

    def load_data_dict(self, data: dict):
        raw = data.get("unit_system", "metric")
        display = self._UNIT_SYSTEM_LABELS.get(raw, raw)
        data = {**data, "unit_system": display}
        super().load_data_dict(data)

        # Populate SOR combo based on project country (country is now loaded)
        country = data.get("project_country", "")
        saved_key = data.get("sor_database", "")
        self._populate_sor_combo(country, saved_key)

    def _populate_sor_combo(self, country: str, saved_key: str = "") -> None:
        """Fill the Material Suggestions combo from the registry for *country*."""
        try:
            from ..structure.widgets.material_dialog import _list_sor_options
            options = _list_sor_options(country)
        except Exception:
            options = []

        cb = getattr(self, "sor_database", None)
        if cb is None:
            return

        cb.blockSignals(True)
        cb.clear()
        for opt in options:
            cb.addItem(opt["label"], opt["db_key"])
        cb.addItem("— No suggestions —", "")

        idx = cb.findData(saved_key) if saved_key else -1
        cb.setCurrentIndex(idx if idx >= 0 else cb.count() - 1)  # default → "— No suggestions —"

        cb.setEnabled(bool(options))
        cb.blockSignals(False)

    def get_data_dict(self) -> dict:
        data = super().get_data_dict()
        cb = getattr(self, "sor_database", None)
        if cb is not None:
            data["sor_database"] = cb.currentData() or ""
        return data

    def get_data(self) -> dict:
        return {"chunk": "general_info", "data": self.get_data_dict()}

    def _on_field_changed(self):
        super()._on_field_changed()
        self.created.emit()
