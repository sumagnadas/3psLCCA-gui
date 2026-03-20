from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QStyleOptionHeader,
)
from PySide6.QtCore import Qt, QSize, QTimer, QRect
from PySide6.QtGui import QColor, QPainter
import datetime

from ...utils.unit_resolver import analyze_conversion_sympy
from ...utils.definitions import UNIT_DISPLAY
from ...utils.display_format import fmt, fmt_comma
from ...utils.icons import make_icon, make_icon_btn
from ...utils.validation_helpers import freeze_widgets


def _fmt_unit(code: str) -> str:
    """Convert raw unit code to display symbol."""
    return UNIT_DISPLAY.get(code.lower(), code) if code else code


def _fmt_carbon_unit(carbon_unit: str) -> str:
    """Normalize stored carbon_unit: fix CO2e subscript and unit symbols."""
    unit = carbon_unit.replace("CO2e", "CO₂e")
    if "/" in unit:
        prefix, denom = unit.rsplit("/", 1)
        return f"{prefix}/{_fmt_unit(denom.strip())}"
    return unit


# Cache for unit analysis — keyed by (unit, carbon_denom, conv_factor)
_analysis_cache: dict = {}


def _cached_analysis(unit: str, carbon_denom: str, conv_factor) -> dict:
    key = (unit, carbon_denom, str(conv_factor))
    if key not in _analysis_cache:
        _analysis_cache[key] = analyze_conversion_sympy(unit, carbon_denom, conv_factor)
    return _analysis_cache[key]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHUNKS = [
    ("str_foundation", "Foundation"),
    ("str_sub_structure", "Sub Structure"),
    ("str_super_structure", "Super Structure"),
    ("str_misc", "Misc"),
]

# Row background states
BG_INVALID = "#f8d7da"  # red
BG_SUSPICIOUS = "#fff3cd"  # orange/yellow
BG_DISABLED = "#e9ecef"  # gray
TEXT_DARK = "#212529"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_NA = {"not_available", None, ""}


def _cf_value(v: dict) -> float:
    """Return the conversion factor, defaulting to 1.0 when not explicitly set."""
    raw = v.get("conversion_factor", "not_available")
    if raw in _NA:
        return 1.0
    try:
        val = float(raw)
        return val if val > 0 else 1.0
    except (TypeError, ValueError):
        return 1.0


def is_carbon_valid(item) -> bool:
    """Valid when carbon_emission is non-zero and CF (if explicitly set) is positive."""
    v = item.get("values", {})
    # Explicitly stored CF of 0 or negative is invalid (not just suspicious)
    cf_raw = v.get("conversion_factor", "not_available")
    if cf_raw not in _NA:
        try:
            if float(cf_raw) <= 0:
                return False
        except (TypeError, ValueError):
            pass  # unparseable CF treated as not_available → default 1.0
    try:
        emission_raw = v.get("carbon_emission", "not_available")
        if emission_raw in _NA:
            return False
        return float(emission_raw) != 0
    except (TypeError, ValueError):
        return False


def calc_carbon(item: dict) -> float:
    """Carbon = quantity × conversion_factor × carbon_emission"""
    v = item.get("values", {})
    try:
        return (
            float(v.get("quantity", 0) or 0)
            * _cf_value(v)
            * float(v.get("carbon_emission", 0) or 0)
        )
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Two-tier grouped header
# ---------------------------------------------------------------------------


class _GroupedHeader(QHeaderView):
    """Horizontal header with spanning group labels on the top tier and
    individual column labels on the bottom tier.

    groups: list of (start_col, span, label) — e.g. [(2, 2, "Qty"), (5, 2, "Emission")]
    Columns NOT in any group span the full height with their label centred.
    """

    def __init__(self, groups=(), parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._groups = list(groups)
        # Map each col → (start, span, label) for quick lookup
        self._col_group: dict[int, tuple] = {}
        for start, span, label in self._groups:
            for c in range(start, start + span):
                self._col_group[c] = (start, span, label)

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(s.width(), s.height() * 2) if self._groups else s

    def paintSection(self, painter, rect, logical_index):
        if not self._groups or logical_index not in self._col_group:
            # Non-grouped column — full height, label centred
            super().paintSection(painter, rect, logical_index)
            return

        h2 = rect.height() // 2
        bottom = QRect(rect.x(), rect.y() + h2, rect.width(), h2)

        # Bottom tier — sub-column label clipped to bottom half
        painter.save()
        painter.setClipRect(bottom)
        super().paintSection(painter, bottom, logical_index)
        painter.restore()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._groups:
            return

        painter = QPainter(self.viewport())
        h2 = self.height() // 2

        for start, span, label in self._groups:
            x = self.sectionViewportPosition(start)
            total_w = sum(self.sectionSize(start + i) for i in range(span))
            group_rect = QRect(x, 0, total_w, h2)

            opt = QStyleOptionHeader()
            self.initStyleOption(opt)
            opt.rect = group_rect
            opt.section = start
            opt.text = label
            opt.textAlignment = Qt.AlignCenter | Qt.AlignVCenter
            opt.position = QStyleOptionHeader.Middle
            opt.selectedPosition = QStyleOptionHeader.NotAdjacent
            self.style().drawControl(self.style().ControlElement.CE_Header, opt, painter, self)

        painter.end()


# ---------------------------------------------------------------------------
# Carbon Table Widget
# ---------------------------------------------------------------------------


class CarbonTable(QTableWidget):
    _L = Qt.AlignLeft | Qt.AlignVCenter
    _R = Qt.AlignRight | Qt.AlignVCenter

    # Cols 2-3 → "Qty" group;  cols 5-6 → "Emission" group
    _GROUPS = [(2, 2, "Qty"), (5, 2, "Emission")]

    _C = Qt.AlignCenter | Qt.AlignVCenter

    INCLUDED_HEADERS = [
        ("Category",      _L),  # 0
        ("Material",      _L),  # 1
        ("Value",         _C),  # 2  ┐ Qty group (sub-col → center)
        ("Unit",          _C),  # 3  ┘
        ("Conv. Factor",  _R),  # 4
        ("Value",         _C),  # 5  ┐ Emission group (sub-col → center)
        ("Unit",          _C),  # 6  ┘
        ("Total kgCO₂e", _R),  # 7
        ("Warning",       _L),  # 8
        ("Action",        _C),  # 9
    ]
    EXCLUDED_HEADERS = [
        ("Category",      _L),  # 0
        ("Material",      _L),  # 1
        ("Value",         _C),  # 2  ┐ Qty group (sub-col → center)
        ("Unit",          _C),  # 3  ┘
        ("Conv. Factor",  _R),  # 4
        ("Value",         _C),  # 5  ┐ Emission group (sub-col → center)
        ("Unit",          _C),  # 6  ┘
        ("Reason",        _L),  # 7
        ("Action",        _C),  # 8
    ]

    def __init__(self, is_included: bool, parent=None):
        super().__init__(parent)
        self.is_included = is_included

        # Install grouped header before setting column count
        grouped_header = _GroupedHeader(groups=self._GROUPS)
        self.setHorizontalHeader(grouped_header)

        headers = self.INCLUDED_HEADERS if is_included else self.EXCLUDED_HEADERS
        self.setColumnCount(len(headers))
        for col, (label, align) in enumerate(headers):
            item = QTableWidgetItem(label)
            item.setTextAlignment(align)
            self.setHorizontalHeaderItem(col, item)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setMinimumSectionSize(40)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.verticalHeader().setDefaultSectionSize(35)
        self.verticalHeader().setVisible(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._set_column_widths()

    def _set_column_widths(self):
        # Initial defaults at ~800px viewport (rest ≈ 720px)
        # Sub-column pairs are equal: qty=43px each, emission=65px each
        if self.is_included:
            for col, w in enumerate([65, 144, 43, 43, 50, 65, 65, 65, 173, 80]):
                self.setColumnWidth(col, w)
        else:
            for col, w in enumerate([72, 158, 43, 43, 50, 65, 65, 216, 80]):
                self.setColumnWidth(col, w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total = self.viewport().width()
        action_w = 80
        rest = max(1, total - action_w)

        # Sub-columns in each group are EQUAL width so the spanning label is centred.
        # Qty group (cols 2-3): each = 6%  → combined 12%
        # Emission group (cols 5-6): each = 9% → combined 18%
        qty_sub = max(45, int(rest * 0.06))
        em_sub  = max(50, int(rest * 0.09))

        if self.is_included:
            widths = {
                0: max(65,  int(rest * 0.09)),  # Category
                1: max(100, int(rest * 0.20)),  # Material
                2: qty_sub,                     # Qty › Value   (= Qty Unit sub-col 1)
                3: qty_sub,                     # Qty › Unit    (= Qty Unit sub-col 2)
                4: max(70,  int(rest * 0.09)),  # Conv. Factor
                5: em_sub,                      # Emission › Value
                6: em_sub,                      # Emission › Unit
                7: max(70,  int(rest * 0.09)),  # Total kgCO₂e
                8: max(100, int(rest * 0.23)),  # Warning
                9: action_w,
            }
        else:
            widths = {
                0: max(65,  int(rest * 0.10)),  # Category
                1: max(100, int(rest * 0.22)),  # Material
                2: qty_sub,                     # Qty › Value
                3: qty_sub,                     # Qty › Unit
                4: max(70,  int(rest * 0.09)),  # Conv. Factor
                5: em_sub,                      # Emission › Value
                6: em_sub,                      # Emission › Unit
                7: max(100, int(rest * 0.29)),  # Reason
                8: action_w,
            }

        for col, width in widths.items():
            self.setColumnWidth(col, width)

    def sizeHint(self):
        header_h = self.horizontalHeader().height() or 35
        rows_h = self.rowCount() * self.verticalHeader().defaultSectionSize()
        return QSize(super().sizeHint().width(), max(60, header_h + rows_h + 10))

    def minimumSizeHint(self):
        return self.sizeHint()

    def update_height(self):
        self.updateGeometry()

    def set_row_style(self, row: int, color_hex: str):
        bg = QColor(color_hex)
        is_highlighted = color_hex in [BG_INVALID, BG_SUSPICIOUS, BG_DISABLED]
        fg = QColor(TEXT_DARK if is_highlighted else "black")

        for col in range(self.columnCount()):
            it = self.item(row, col)
            if it:
                it.setBackground(bg)
                it.setForeground(fg)
            w = self.cellWidget(row, col)
            if w:
                w.setStyleSheet(
                    f"background-color: {color_hex}; color: {TEXT_DARK if is_highlighted else 'black'};"
                )

    def clear_rows(self):
        self.setRowCount(0)
        self.update_height()


# ---------------------------------------------------------------------------
# MaterialEmissions
# ---------------------------------------------------------------------------


class MaterialEmissions(QWidget):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self._details_visible = False
        self._frozen = False

        # Outer layout holds only the scroll area, so growing tables never
        # overlap sibling widgets — the scroll area absorbs all extra height.
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(8)

        # Summary Bar
        self.summary_bar = QWidget()
        summary_layout = QHBoxLayout(self.summary_bar)
        self.total_lbl = QLabel("Total: - kgCO₂e")
        self.count_lbl = QLabel("Included: — of — items")
        self.details_btn = QPushButton("Show Details ▼")
        self.details_btn.setFlat(True)
        self.details_btn.clicked.connect(self._toggle_details)
        summary_layout.addWidget(self.total_lbl)
        summary_layout.addWidget(self._vline())
        summary_layout.addWidget(self.count_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(self.details_btn)
        main_layout.addWidget(self.summary_bar)

        # Details Row
        self.details_widget = QWidget()
        details_layout = QHBoxLayout(self.details_widget)
        self.foundation_lbl = QLabel("Foundation: —")
        self.sub_lbl = QLabel("Sub Structure: —")
        self.super_lbl = QLabel("Super Structure: —")
        self.misc_lbl = QLabel("Misc: —")
        for lbl in [self.foundation_lbl, self.sub_lbl, self.super_lbl, self.misc_lbl]:
            details_layout.addWidget(lbl)
            details_layout.addWidget(self._vline())
        details_layout.addStretch()
        self.details_widget.setVisible(False)
        main_layout.addWidget(self.details_widget)
        main_layout.addWidget(self._hline())

        main_layout.addWidget(self._section_label("Included in Carbon Calculation"))
        self.included_table = CarbonTable(is_included=True)
        main_layout.addWidget(self.included_table)
        main_layout.addWidget(self._hline())

        main_layout.addWidget(self._section_label("Excluded from Carbon Calculation"))
        self.excluded_table = CarbonTable(is_included=False)
        main_layout.addWidget(self.excluded_table)
        main_layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(f"<b>{text}</b>")
        lbl.setStyleSheet("font-size: 13px;")
        return lbl

    def _hline(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFrameShadow(QFrame.Sunken)
        return f

    def _vline(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.VLine)
        f.setFrameShadow(QFrame.Sunken)
        return f

    def _toggle_details(self):
        self._details_visible = not self._details_visible
        self.details_widget.setVisible(self._details_visible)
        self.details_btn.setText(
            "Hide Details ▲" if self._details_visible else "Show Details ▼"
        )

    def on_refresh(self):
        if not self.controller or not getattr(self.controller, "engine", None):
            return

        included_items = []
        excluded_items = []
        cat_totals = {label: 0.0 for _, label in CHUNKS}
        total_carbon = 0.0
        total_count = 0
        included_count = 0

        for chunk_id, category in CHUNKS:
            data = self.controller.engine.fetch_chunk(chunk_id) or {}
            for comp_name, items in data.items():
                for idx, item in enumerate(items):
                    if item.get("state", {}).get("in_trash", False):
                        continue

                    total_count += 1
                    v = item.get("values", {})
                    state = item.get("state", {})

                    # Target denominator for carbon is usually the unit after the slash
                    carbon_unit = v.get("carbon_unit", "")
                    carbon_denom = (
                        carbon_unit.split("/")[-1] if "/" in carbon_unit else ""
                    )

                    # Unit resolver analysis (cached — same inputs always yield same result)
                    analysis = _cached_analysis(
                        v.get("unit", ""), carbon_denom, _cf_value(v)
                    )

                    valid = is_carbon_valid(item)
                    is_included_flag = state.get("included_in_carbon_emission", True)
                    is_confirmed = state.get("carbon_conversion_confirmed", False)
                    suspicious = analysis["is_suspicious"] and not is_confirmed

                    if valid and is_included_flag and not suspicious:
                        included_count += 1
                        carbon = calc_carbon(item)
                        total_carbon += carbon
                        cat_totals[category] += carbon
                        included_items.append(
                            (category, chunk_id, comp_name, idx, item, carbon, analysis)
                        )
                    else:
                        reason = (
                            "Missing Data"
                            if not valid
                            else ("Suspicious Data" if suspicious else "User Excluded")
                        )
                        excluded_items.append(
                            (category, chunk_id, comp_name, idx, item, reason, analysis)
                        )

        self._populate_included(included_items)
        self._populate_excluded(excluded_items)
        self._update_summary(total_carbon, included_count, total_count, cat_totals)

    def _populate_included(self, items):
        t = self.included_table
        t.setUpdatesEnabled(False)
        t.clear_rows()
        for category, chunk_id, comp_name, idx, item, carbon, analysis in items:
            v = item.get("values", {})
            row = t.rowCount()
            t.insertRow(row)

            def _ri(text):
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                return it

            t.setItem(row, 0, QTableWidgetItem(category))
            t.setItem(row, 1, QTableWidgetItem(v.get("material_name", "")))
            t.setItem(row, 2, _ri(fmt(v.get("quantity", 0))))
            t.setItem(row, 3, QTableWidgetItem(_fmt_unit(v.get("unit", ""))))
            _cf_raw = v.get("conversion_factor", "not_available")
            t.setItem(row, 4, _ri(fmt(_cf_raw) if _cf_raw not in _NA else "—"))
            t.setItem(row, 5, _ri(fmt(v.get("carbon_emission", 0))))
            t.setItem(row, 6, QTableWidgetItem(_fmt_carbon_unit(v.get("carbon_unit", ""))))

            carbon_item = QTableWidgetItem(fmt(carbon))
            carbon_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            t.setItem(row, 7, carbon_item)

            # Persistent Warnings: Check for zero qty or if the confirmed factor is still suspicious
            warnings = []
            if float(v.get("quantity", 0) or 0) == 0:
                warnings.append("Zero Qty")
            if analysis["is_suspicious"]:
                warnings.append("⚠️ Conversion Factor seems incorrect.")

            t.setItem(row, 8, QTableWidgetItem(", ".join(warnings)))

            edit_btn = make_icon_btn("edit", "Edit emission factor")
            edit_btn.clicked.connect(
                lambda _, ci=chunk_id, cn=comp_name, i=idx, it=item: self._open_emission_edit(ci, cn, i, it)
            )
            excl_btn = make_icon_btn("exclude", "Exclude from calculation", icon_color="#e74c3c", hover_color="231, 76, 60")
            excl_btn.clicked.connect(
                lambda _, ci=chunk_id, cn=comp_name, i=idx: self._toggle_inclusion(ci, cn, i, False)
            )
            freeze_widgets(self._frozen, edit_btn, excl_btn)
            t.setCellWidget(row, 9, self._btn_container(edit_btn, excl_btn))

        t.update_height()
        t.setUpdatesEnabled(True)

    def _populate_excluded(self, items):
        t = self.excluded_table
        t.setUpdatesEnabled(False)
        t.clear_rows()
        for category, chunk_id, comp_name, idx, item, reason, analysis in items:
            v = item.get("values", {})
            row = t.rowCount()
            t.insertRow(row)

            def _ri(text):
                it = QTableWidgetItem(text)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                return it

            t.setItem(row, 0, QTableWidgetItem(category))
            t.setItem(row, 1, QTableWidgetItem(v.get("material_name", "")))
            t.setItem(row, 2, _ri(fmt(v.get("quantity", 0))))
            t.setItem(row, 3, QTableWidgetItem(_fmt_unit(v.get("unit", ""))))
            _cf_raw = v.get("conversion_factor", "not_available")
            t.setItem(row, 4, _ri(fmt(_cf_raw) if _cf_raw not in _NA else "—"))
            t.setItem(row, 5, _ri(fmt(v.get("carbon_emission", 0))))
            t.setItem(row, 6, QTableWidgetItem(_fmt_carbon_unit(v.get("carbon_unit", ""))))
            t.setItem(row, 7, QTableWidgetItem(reason))

            edit_btn = make_icon_btn("edit", "Edit emission factor")
            edit_btn.clicked.connect(
                lambda _, ci=chunk_id, cn=comp_name, i=idx, it=item: self._open_emission_edit(ci, cn, i, it)
            )
            freeze_widgets(self._frozen, edit_btn)

            if reason in ["Missing Data", "Suspicious Data"]:
                t.set_row_style(
                    row, BG_INVALID if reason == "Missing Data" else BG_SUSPICIOUS
                )
                t.setCellWidget(row, 8, self._btn_container(edit_btn))
            else:
                incl_btn = make_icon_btn("include", "Include in calculation", icon_color="#2ecc71", hover_color="46, 204, 113")
                incl_btn.clicked.connect(
                    lambda _, ci=chunk_id, cn=comp_name, i=idx: self._toggle_inclusion(ci, cn, i, True)
                )
                freeze_widgets(self._frozen, incl_btn)
                t.setCellWidget(row, 8, self._btn_container(edit_btn, incl_btn))
        t.update_height()
        t.setUpdatesEnabled(True)

    def _update_summary(
        self, total: float, included: int, total_count: int, cat_totals: dict
    ):
        self.total_lbl.setText(f"Total: {fmt_comma(total)} kgCO₂e")
        self.count_lbl.setText(f"Included: {included} of {total_count} items")
        self.foundation_lbl.setText(
            f"Foundation: {fmt_comma(cat_totals.get('Foundation', 0))}"
        )
        self.sub_lbl.setText(
            f"Sub Structure: {fmt_comma(cat_totals.get('Sub Structure', 0))}"
        )
        self.super_lbl.setText(
            f"Super Structure: {fmt_comma(cat_totals.get('Super Structure', 0))}"
        )
        self.misc_lbl.setText(f"Misc: {fmt_comma(cat_totals.get('Misc', 0))}")

    def _toggle_inclusion(
        self, chunk_id: str, comp_name: str, data_index: int, include: bool
    ):
        data = self.controller.engine.fetch_chunk(chunk_id) or {}
        if comp_name in data and data_index < len(data[comp_name]):
            data[comp_name][data_index]["state"][
                "included_in_carbon_emission"
            ] = include
            self.controller.engine.stage_update(chunk_name=chunk_id, data=data)
            self._mark_dirty()
            QTimer.singleShot(0, self.on_refresh)

    def _btn_container(self, *buttons) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(4)
        for btn in buttons:
            h.addWidget(btn)
        return w

    def _open_emission_edit(
        self, chunk_id: str, comp_name: str, data_index: int, item: dict
    ):
        from ...structure.widgets.material_dialog import MaterialDialog
        dialog = MaterialDialog(comp_name, parent=self, data=item, emissions_only=True)
        if dialog.exec():
            vals = dialog.get_values()
            data = self.controller.engine.fetch_chunk(chunk_id) or {}
            if comp_name in data and data_index < len(data[comp_name]):
                target = data[comp_name][data_index]
                target["values"]["carbon_emission"] = vals.get("carbon_emission", 0.0)
                target["values"]["carbon_unit"] = vals.get("carbon_unit", "")
                target["values"]["conversion_factor"] = vals.get("conversion_factor", 1.0)
                target["state"]["included_in_carbon_emission"] = vals.get(
                    "included_in_carbon_emission", True
                )
                target["state"]["carbon_conversion_confirmed"] = True
                target["meta"]["modified_on"] = datetime.datetime.now().isoformat()
                self.controller.engine.stage_update(chunk_name=chunk_id, data=data)
                self._mark_dirty()
                QTimer.singleShot(0, self.on_refresh)

    def _mark_dirty(self):
        if self.controller and self.controller.engine:
            import time

            eng = self.controller.engine
            eng._last_keystroke_time = time.time()
            eng._has_unsaved_changes = True
            try:
                eng.on_dirty(True)
            except:
                pass

    def _compute(self) -> dict:
        """
        Core calculation logic shared by on_refresh(), validate(), and get_data().
        Returns raw computed data without touching any UI.
        """
        cat_totals = {label: 0.0 for _, label in CHUNKS}
        included_items = []
        excluded_items = []
        total_carbon = 0.0
        total_count = 0
        included_count = 0

        if not self.controller or not getattr(self.controller, "engine", None):
            return {
                "total_carbon": 0.0,
                "cat_totals": cat_totals,
                "included_count": 0,
                "total_count": 0,
                "included_items": [],
                "excluded_items": [],
            }

        for chunk_id, category in CHUNKS:
            data = self.controller.engine.fetch_chunk(chunk_id) or {}
            for comp_name, items in data.items():
                for idx, item in enumerate(items):
                    if item.get("state", {}).get("in_trash", False):
                        continue
                    total_count += 1
                    v = item.get("values", {})
                    state = item.get("state", {})
                    carbon_unit = v.get("carbon_unit", "")
                    carbon_denom = carbon_unit.split("/")[-1] if "/" in carbon_unit else ""
                    analysis = _cached_analysis(
                        v.get("unit", ""), carbon_denom, _cf_value(v)
                    )
                    valid = is_carbon_valid(item)
                    is_included_flag = state.get("included_in_carbon_emission", True)
                    is_confirmed = state.get("carbon_conversion_confirmed", False)
                    suspicious = analysis["is_suspicious"] and not is_confirmed

                    if valid and is_included_flag and not suspicious:
                        included_count += 1
                        carbon = calc_carbon(item)
                        total_carbon += carbon
                        cat_totals[category] += carbon
                        included_items.append(
                            (category, chunk_id, comp_name, idx, item, carbon, analysis)
                        )
                    else:
                        reason = (
                            "Missing Data"
                            if not valid
                            else ("Suspicious Data" if suspicious else "User Excluded")
                        )
                        excluded_items.append(
                            (category, chunk_id, comp_name, idx, item, reason, analysis)
                        )

        return {
            "total_carbon": total_carbon,
            "cat_totals": cat_totals,
            "included_count": included_count,
            "total_count": total_count,
            "included_items": included_items,
            "excluded_items": excluded_items,
        }

    def validate(self) -> dict:
        result = self._compute()
        warnings = []

        if result["total_count"] == 0:
            warnings.append(
                "No materials found — add items in the Construction Work Data section."
            )
        elif result["total_carbon"] == 0.0:
            warnings.append(
                f"Total material carbon is 0 kgCO₂e — "
                f"{result['included_count']} of {result['total_count']} items are included."
            )

        missing = sum(
            1 for *_, reason, _ in result["excluded_items"] if reason == "Missing Data"
        )
        suspicious = sum(
            1 for *_, reason, _ in result["excluded_items"] if reason == "Suspicious Data"
        )
        if missing:
            warnings.append(
                f"{missing} item{'s' if missing != 1 else ''} excluded — missing emission factor data."
            )
        if suspicious:
            warnings.append(
                f"{suspicious} item{'s' if suspicious != 1 else ''} excluded — "
                f"suspicious conversion factor (not confirmed)."
            )

        return {"errors": [], "warnings": warnings}

    def get_data(self) -> dict:
        result = self._compute()
        included = [
            {
                "category": cat,
                "component": comp,
                "material": item.get("values", {}).get("material_name", ""),
                "quantity": float(item.get("values", {}).get("quantity", 0) or 0),
                "unit": item.get("values", {}).get("unit", ""),
                "conversion_factor": float(
                    item.get("values", {}).get("conversion_factor", 1) or 1
                ),
                "carbon_emission": float(
                    item.get("values", {}).get("carbon_emission", 0) or 0
                ),
                "carbon_unit": item.get("values", {}).get("carbon_unit", ""),
                "total_kgCO2e": carbon,
            }
            for cat, chunk_id, comp, idx, item, carbon, analysis in result["included_items"]
        ]
        return {
            "chunk": "material_emissions_data",
            "data": {
                "included_items": included,
                "cat_totals": result["cat_totals"],
                "total_kgCO2e": result["total_carbon"],
                "included_count": result["included_count"],
                "total_count": result["total_count"],
            },
        }

    def freeze(self, frozen: bool = True):
        self._frozen = frozen
        self.on_refresh()  # repopulate so button states reflect new frozen state

    def showEvent(self, event):
        super().showEvent(event)
        self.on_refresh()
