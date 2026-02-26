from datetime import date

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
from ..utils.countries_data import COUNTRIES
from gui.components.base_widget import ScrollableForm


BASE_DOCS_URL = "https://yourdocs.com/bridge/"

# (key, title, explanation, field_type, options_or_range, unit, is_required, doc_slug)
# field_type: "text" | "int" | "float" | "combo"
BRIDGE_FIELDS = [
    (
        "bridge_name",
        "Name of Bridge",
        "The official or commonly used name identifying the bridge.",
        "text",
        None,
        "",
        True,
        "bridge-name",
    ),
    (
        "user_agency",
        "Owner",
        "Name of the owner, client, or responsible agency for this bridge.",
        "text",
        None,
        "",
        True,
        "user-agency",
    ),
    (
        "location_country",
        "Location — Country",
        "Country in which the bridge is situated.",
        "combo",
        COUNTRIES,
        "",
        True,
        "location-country",
    ),
    (
        "location_address",
        "Location — Address",
        "Full address or site description of the bridge location.",
        "text",
        None,
        "",
        False,
        "location-address",
    ),
    (
        "bridge_type",
        "Type of Bridge",
        "Structural classification of the bridge (e.g. Girder, Arch, Cable-stayed).",
        "combo",
        [
            "Girder",
            "Arch",
            "Cable-Stayed",
            "Suspension",
            "Truss",
            "Box Girder",
            "Slab",
            "Other",
        ],
        "",
        True,
        "bridge-type",
    ),
    (
        "span",
        "Span",
        "Total span length of the bridge between supports.",
        "float",
        (0.0, 99999.0, 2),
        "(m)",
        True,
        "span",
    ),
    (
        "num_lanes",
        "Number of Lanes",
        "Total number of traffic lanes on the bridge deck.",
        "int",
        (0, 20),
        "",
        True,
        "num-lanes",
    ),
    (
        "footpath",
        "Footpath",
        "Indicates whether a dedicated pedestrian footpath is provided.",
        "combo",
        ["Yes", "No"],
        "",
        True,
        "footpath",
    ),
    (
        "wind_speed",
        "Wind Speed",
        "Design wind speed used for structural analysis at the bridge site.",
        "float",
        (0.0, 999.0, 2),
        "(m/s)",
        True,
        "wind-speed",
    ),
    (
        "carriageway_width",
        "Carriageway Width",
        "Clear width of the roadway portion of the bridge deck.",
        "float",
        (0.0, 9999.0, 2),
        "(m)",
        True,
        "carriageway-width",
    ),
    (
        "year_of_construction",
        "Year of Construction / Present Year",
        "Year the bridge was (or is planned to be) constructed, used as the "
        "baseline for life cycle cost assessment.",
        "int",
        (1900, 2200),
        "",
        True,
        "year-of-construction",
    ),
    (
        "duration_construction_months",
        "Duration of Construction",
        "Construction duration expressed in months (alternative or complement to years).",
        "int",
        (0, 1200),
        "(months)",
        False,
        "duration-construction-months",
    ),
    (
        "working_days_per_month",
        "Working Days per Month",
        "Number of working days assumed per month for scheduling purposes.",
        "int",
        (0, 31),
        "(days)",
        False,
        "working-days-per-month",
    ),
    (
        "design_life",
        "Design Life",
        "Expected operational lifetime of the bridge structure.",
        "int",
        (0, 999),
        "(years)",
        True,
        "design-life",
    ),
    (
        "service_life",
        "Service Life",
        "Actual or anticipated years the bridge remains in serviceable condition.",
        "int",
        (0, 999),
        "(years)",
        True,
        "service-life",
    ),
]


class BridgeData(ScrollableForm):
    def __init__(self, controller=None):
        super().__init__(controller=controller, chunk_name="bridge_data")

        self.required_keys = []

        for (
            key,
            title,
            explanation,
            field_type,
            options_or_range,
            unit,
            is_required,
            doc_slug,
        ) in BRIDGE_FIELDS:

            section = QWidget()
            layout = QVBoxLayout(section)
            layout.setContentsMargins(0, 10, 0, 10)
            layout.setSpacing(4)

            # --- Title ---
            title_label = QLabel(f"{title} *" if is_required else title)
            title_label.setStyleSheet("font-weight: 600;")
            layout.addWidget(title_label)

            # --- Explanation with inline docs link ---
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

            # --- Input widget ---
            if field_type == "text":
                widget = QLineEdit()
                widget.setMinimumHeight(30)
                setattr(self, key, self.field(key, widget))
                if is_required:
                    self.required_keys.append(key)
                widget.textChanged.connect(lambda _, w=widget: w.setStyleSheet(""))

            elif field_type == "int":
                lo, hi = options_or_range
                widget = QSpinBox()
                widget.setRange(lo, hi)
                if unit:
                    widget.setSuffix(f" {unit}")
                widget.setMinimumHeight(30)
                setattr(self, key, self.field(key, widget))
                if is_required:
                    self.required_keys.append(key)
                widget.valueChanged.connect(lambda _, w=widget: w.setStyleSheet(""))

            elif field_type == "float":
                lo, hi, decimals = options_or_range
                widget = QDoubleSpinBox()
                widget.setRange(lo, hi)
                widget.setDecimals(decimals)
                if unit:
                    widget.setSuffix(f" {unit}")
                widget.setMinimumHeight(30)
                setattr(self, key, self.field(key, widget))
                if is_required:
                    self.required_keys.append(key)
                widget.valueChanged.connect(lambda _, w=widget: w.setStyleSheet(""))

            elif field_type == "combo":
                widget = QComboBox()
                widget.addItems(options_or_range)
                widget.setMinimumHeight(30)
                setattr(self, key, self.field(key, widget))
                if is_required:
                    self.required_keys.append(key)
                widget.currentIndexChanged.connect(
                    lambda _, w=widget: w.setStyleSheet("")
                )

            layout.addWidget(widget)
            self.form.addRow(section)

        # --- Buttons Row ---
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 10, 0, 10)
        btn_layout.setSpacing(10)

        self.btn_load_suggested = QPushButton("Load Suggested Values")
        self.btn_load_suggested.setMinimumHeight(35)
        self.btn_load_suggested.clicked.connect(self.load_suggested_values)

        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.setMinimumHeight(35)
        self.btn_clear_all.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_load_suggested)
        btn_layout.addWidget(self.btn_clear_all)

        self.form.addRow(btn_row)

    # ------------------------------------------------------------------
    # Suggested / default values
    # ------------------------------------------------------------------
    def load_suggested_values(self):
        defaults = {
            "bridge_type": "Girder",
            "footpath": "Yes",
            "num_lanes": 2,
            "wind_speed": 33.0,
            "carriageway_width": 7.5,
            "year_of_construction": date.today().year,
            "duration_construction_months": 24,
            "working_days_per_month": 25,
            "design_life": 100,
            "service_life": 100,
        }

        for key, val in defaults.items():
            widget = getattr(self, key, None)
            if widget is None:
                continue
            if isinstance(widget, QComboBox):
                idx = widget.findText(str(val))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(val)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(val))
            widget.setStyleSheet("")

        self._on_field_changed()

        if self.controller and self.controller.engine:
            self.controller.engine._log("Bridge: Suggested values applied.")

    # ------------------------------------------------------------------
    # Clear all fields
    # ------------------------------------------------------------------
    def clear_all(self):
        for f in BRIDGE_FIELDS:
            key = f[0]
            widget = getattr(self, key, None)
            if widget is None:
                continue
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(widget.minimum())
            widget.setStyleSheet("")

        self._on_field_changed()

        if self.controller and self.controller.engine:
            self.controller.engine._log("Bridge: All fields cleared.")

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
                empty = False  # always has a selection
            else:
                empty = widget.value() <= 0

            if empty:
                label = next(f[1] for f in BRIDGE_FIELDS if f[0] == key)
                errors.append(label)
                widget.setStyleSheet("border: 1px solid red;")

        if errors:
            msg = f"Missing required bridge data: {', '.join(errors)}"
            if self.controller and self.controller.engine:
                self.controller.engine._log(msg)
            return False, errors

        return True, []
