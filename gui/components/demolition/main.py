from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from ..base_widget import ScrollableForm
from ..utils.form_builder.form_definitions import FieldDef, Section
from ..utils.form_builder.form_builder import build_form
from ..utils.validation_helpers import clear_field_styles, validate_form

BASE_DOCS_URL = "https://yourdocs.com/demolition/"

SUGGESTED_VALUES = {
    "demolition_cost_pct": 10.0,
    "demolition_carbon_cost_pct": 10.0,
    "demolition_duration": 1,
}

DEMOLITION_FIELDS = [
    Section("End of Life"),
    FieldDef(
        "demolition_cost_pct",
        "Demolition & Disposal Cost (%)",
        "",
        "float",
        (0.0, 100.0, 1),
        unit="(%)",
        required=True,
    ),
    FieldDef(
        "demolition_carbon_cost_pct",
        "Demolition & Disposal Carbon Cost (%)",
        "",
        "float",
        (0.0, 100.0, 1),
        unit="(%)",
        required=True,
    ),
    FieldDef(
        "demolition_duration",
        "Demolition & Disposal Duration",
        "",
        "int",
        (0, 60),
        unit="(mo)",
        required=True,
    ),
    FieldDef(
        "demolition_method",
        "Demolition Method",
        "",
        "combo",
        options=["Conventional", "Implosion", "Deconstruction"],
    ),
]


class Demolition(ScrollableForm):
    created = Signal()

    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="demolition_data")
        self.required_keys = build_form(self, DEMOLITION_FIELDS, BASE_DOCS_URL)

        # ── Buttons row (Maintenance Style) ──────────────────────────────────
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 10, 0, 10)

        self.btn_load_suggested = QPushButton("Load Suggested Values")
        self.btn_load_suggested.setMinimumHeight(35)
        self.btn_load_suggested.clicked.connect(self.load_suggested_values)

        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.setMinimumHeight(35)
        self.btn_clear_all.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_load_suggested)
        btn_layout.addWidget(self.btn_clear_all)

        # Maintenance usually adds the row directly to the form
        self.form.addRow(btn_row)

        # Vertical Spacer to prevent the AttributeError from earlier
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.form.addItem(spacer)

    def load_suggested_values(self):
        for key, val in SUGGESTED_VALUES.items():
            widget = getattr(self, key, None)
            if widget:
                widget.setValue(val)
                widget.setStyleSheet("")
        self._on_field_changed()

    def clear_all(self):
        for entry in DEMOLITION_FIELDS:
            if isinstance(entry, Section):
                continue
            widget = getattr(self, entry.key, None)
            if not widget:
                continue
            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            widget.setStyleSheet("")
        self._on_field_changed()

    def validate(self):
        return validate_form(DEMOLITION_FIELDS, self)

    def clear_validation(self):
        clear_field_styles(DEMOLITION_FIELDS, self)

    def get_data(self):
        return {"chunk": "demolition_data", "data": self.get_data_dict()}

    def _on_field_changed(self):
        super()._on_field_changed()
        self.created.emit()
