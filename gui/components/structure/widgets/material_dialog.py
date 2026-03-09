"""
gui/components/structure/widgets/material_dialog.py
====================================================
MaterialDialog and its helper classes / functions.
Extracted from manager.py so it can be imported by other modules
(carbon_emission, recycling, etc.) without pulling in StructureManagerWidget.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLineEdit,
    QFrame,
    QLabel,
    QMessageBox,
    QCheckBox,
    QComboBox,
    QCompleter,
    QScrollArea,
)
from PySide6.QtCore import Qt, QUrl, QStringListModel
from PySide6.QtGui import (
    QDoubleValidator,
    QDesktopServices,
    QStandardItemModel,
    QStandardItem,
)

from ...utils.definitions import (
    _CONSTRUCTION_UNITS,
    UNIT_TO_SI,
    UNIT_DIMENSION,
    SI_BASE_UNITS,
)
from ...utils.input_fields.add_material import FIELD_DEFINITIONS, BASE_DOCS_URL


# ---------------------------------------------------------------------------
# Info Popup
# ---------------------------------------------------------------------------


class InfoPopup(QDialog):
    def __init__(self, field_key: str, parent=None):
        super().__init__(parent)
        defn = FIELD_DEFINITIONS.get(field_key, {})

        self.setWindowTitle(defn.get("label", field_key))
        self.setMinimumWidth(360)
        self.setMaximumWidth(460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(420, 260)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title_lbl = QLabel(f"<b>{defn.get('label', field_key)}</b>")
        title_lbl.setStyleSheet("font-size: 13px;")
        layout.addWidget(title_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        expl_lbl = QLabel(defn.get("explanation", "No description available."))
        expl_lbl.setWordWrap(True)
        expl_lbl.setStyleSheet("font-size: 12px;")
        layout.addWidget(expl_lbl)

        btn_row = QHBoxLayout()
        doc_slug = defn.get("doc_slug", "")
        if doc_slug:
            read_more = QPushButton("Read More →")
            read_more.setStyleSheet("font-weight: 600; border: none;")
            read_more.setCursor(Qt.PointingHandCursor)
            read_more.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(f"{BASE_DOCS_URL}{doc_slug}"))
            )
            btn_row.addWidget(read_more)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)


# ---------------------------------------------------------------------------
# Shared UI helpers
# ---------------------------------------------------------------------------


def _field_block(key: str, input_widget: QWidget, parent_dialog: QDialog) -> QWidget:
    defn = FIELD_DEFINITIONS.get(key, {})
    label = defn.get("label", key)
    expl = defn.get("explanation", "")
    required = defn.get("required", False)

    block = QWidget()
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 4, 0, 4)
    layout.setSpacing(3)

    title_lbl = QLabel(f"{label} *" if required else label)
    title_lbl.setStyleSheet("font-weight: 600; font-size: 12px;")
    layout.addWidget(title_lbl)

    expl_row = QHBoxLayout()
    expl_row.setContentsMargins(0, 0, 0, 0)
    expl_row.setSpacing(6)

    expl_lbl = QLabel(expl)
    expl_lbl.setWordWrap(True)
    expl_lbl.setStyleSheet("font-size: 11px;")
    expl_row.addWidget(expl_lbl, stretch=1)

    info_btn = QPushButton("ⓘ")
    info_btn.setFixedSize(22, 22)
    info_btn.setFlat(True)
    info_btn.setStyleSheet(
        "QPushButton {font-weight: bold; font-size: 13px; border: none; }"
    )
    info_btn.setFocusPolicy(Qt.NoFocus)
    info_btn.setCursor(Qt.PointingHandCursor)
    info_btn.clicked.connect(lambda: InfoPopup(key, parent_dialog).exec())
    expl_row.addWidget(info_btn, alignment=Qt.AlignTop)

    layout.addLayout(expl_row)

    input_widget.setMinimumHeight(30)
    layout.addWidget(input_widget)

    return block


def _section_header(title: str) -> QLabel:
    lbl = QLabel(f"<b>{title}</b>")
    lbl.setStyleSheet("font-size: 13px; margin-top: 4px;")
    return lbl


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("font-weight: 600; font-size: 11px;")
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


# ---------------------------------------------------------------------------
# CustomUnitDialog
# ---------------------------------------------------------------------------


class CustomUnitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Unit")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)

        dbl = QDoubleValidator()
        dbl.setNotation(QDoubleValidator.StandardNotation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        desc = QLabel("Define a custom unit and its equivalent in the SI base unit for its dimension.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(desc)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        sym_col = QVBoxLayout()
        sym_col.setSpacing(3)
        sym_col.addWidget(_lbl("Symbol *"))
        self.symbol_in = QLineEdit()
        self.symbol_in.setPlaceholderText("e.g. bag, rft, point")
        self.symbol_in.setMinimumHeight(32)
        sym_col.addWidget(self.symbol_in)
        row1.addLayout(sym_col, stretch=1)

        name_col = QVBoxLayout()
        name_col.setSpacing(3)
        name_col.addWidget(_lbl("Name (optional)"))
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("e.g. Cement Bag")
        self.name_in.setMinimumHeight(32)
        name_col.addWidget(self.name_in)
        row1.addLayout(name_col, stretch=2)

        layout.addLayout(row1)

        layout.addWidget(_lbl("Weight Equivalent"))
        conv_row = QHBoxLayout()
        conv_row.setSpacing(8)
        conv_row.addWidget(QLabel("1 [symbol]  ="))
        self.conv_in = QLineEdit()
        self.conv_in.setPlaceholderText("e.g. 50")
        self.conv_in.setMinimumHeight(32)
        self.conv_in.setValidator(dbl)
        conv_row.addWidget(self.conv_in, stretch=1)
        self.si_unit_in = QLineEdit("kg")
        self.si_unit_in.setReadOnly(True)
        self.si_unit_in.setMinimumHeight(32)
        self.si_unit_in.setMaximumWidth(70)
        self.si_unit_in.setStyleSheet("background: #f5f5f5; color: #595959;")
        conv_row.addWidget(self.si_unit_in)
        conv_row.addStretch()
        layout.addLayout(conv_row)

        note = QLabel("Weight equivalent in kg — used for transport trip calculations.")
        note.setStyleSheet("font-size: 10px; color: #888;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Unit")
        add_btn.setStyleSheet("font-weight: bold; padding: 6px 20px;")
        add_btn.setMinimumHeight(32)
        add_btn.clicked.connect(self._validate_and_accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        if not self.symbol_in.text().strip():
            QMessageBox.critical(self, "Error", "Symbol is required.")
            return
        self.accept()

    def get_unit(self) -> dict:
        si_unit = self.si_unit_in.text().strip() or "kg"
        dimension = {
            "kg": "Mass", "g": "Mass",
            "m": "Length",
            "m²": "Area", "m2": "Area",
            "m³": "Volume", "m3": "Volume",
            "nos": "Count",
        }.get(si_unit)
        return {
            "symbol": self.symbol_in.text().strip(),
            "name": self.name_in.text().strip(),
            "dimension": dimension,
            "to_si": float(self.conv_in.text() or 1),
            "si_unit": si_unit,
        }


# ---------------------------------------------------------------------------
# SOR / registry helpers
# ---------------------------------------------------------------------------

_SOR_UNIT_ALIASES: dict[str, str] = {
    "rmt": "rm",
    "lmt": "rm",
    "sqmt": "sqm",
    "t":   "tonne",
}


def _resolve_unit_code(sor_unit: str, combo: "QComboBox") -> int:
    idx = combo.findData(sor_unit)
    if idx >= 0:
        return idx
    lower = sor_unit.lower()
    idx = combo.findData(lower)
    if idx >= 0:
        return idx
    alias = _SOR_UNIT_ALIASES.get(lower)
    if alias:
        idx = combo.findData(alias)
        if idx >= 0:
            return idx
    return -1


def _registry_dir() -> str:
    import os
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'registry')
    )


def _ensure_registry_on_path():
    import sys
    d = _registry_dir()
    if d not in sys.path:
        sys.path.insert(0, d)


def _list_sor_options(country: str = None) -> list[dict]:
    _ensure_registry_on_path()
    result = []
    try:
        from db_registry import list_databases
        raw = list_databases(country=country.strip() if country else None)
        for e in raw:
            if e.get("status") != "OK":
                continue
            region = e.get("region", "")
            label = f"{e['db_key']}  ({region})" if region else e["db_key"]
            result.append({"db_key": e["db_key"], "region": region, "label": label})
    except Exception as ex:
        print(f"[MaterialDialog] Could not list SOR options: {ex}")

    try:
        from ..registry.custom_material_db import CustomMaterialDB, CUSTOM_PREFIX
        cdb = CustomMaterialDB()
        for db_name in cdb.list_db_names():
            result.append({
                "db_key": f"{CUSTOM_PREFIX}{db_name}",
                "region": "Custom",
                "label": f"{db_name}  (Custom)",
            })
    except Exception as ex:
        print(f"[MaterialDialog] Could not list custom databases: {ex}")

    return result


def _list_sor_types(db_keys: list = None) -> list[str]:
    _ensure_registry_on_path()
    try:
        from db_registry import list_databases as _list_dbs
        available = [
            e["db_key"] for e in _list_dbs()
            if e.get("status") == "OK"
            and (db_keys is None or e["db_key"] in db_keys)
        ]
        if not available:
            return []
        from search_engine import MaterialSearchEngine
        engine = MaterialSearchEngine(db_keys=db_keys)
        return sorted({
            item.get("type", "").strip()
            for item in engine._iter_items()
            if item.get("type", "").strip()
        })
    except Exception:
        return []


def _load_material_suggestions(db_keys: list = None, comp_name: str = None) -> dict:
    _ensure_registry_on_path()

    if db_keys is not None:
        regular_keys = [k for k in db_keys if not k.startswith("custom::")]
        custom_names = [k[len("custom::"):] for k in db_keys if k.startswith("custom::")]
        load_all_custom = False
    else:
        regular_keys = None
        custom_names = []
        load_all_custom = True

    result = {}
    comp_lower = comp_name.strip().lower() if comp_name else None

    skip_regular = (db_keys is not None and not regular_keys)
    if not skip_regular:
        try:
            from db_registry import list_databases as _list_dbs
            _available = [
                e["db_key"] for e in _list_dbs()
                if e.get("status") == "OK"
                and (regular_keys is None or e["db_key"] in regular_keys)
            ]
            if not _available:
                skip_regular = True
        except Exception:
            skip_regular = True

    if not skip_regular:
        try:
            from search_engine import MaterialSearchEngine
            engine = MaterialSearchEngine(db_keys=regular_keys)

            if comp_lower:
                for item in engine._iter_items():
                    t = item.get('type', '').lower()
                    if t == comp_lower or comp_lower in t or t in comp_lower:
                        name = item.get('name', '').strip()
                        if name:
                            result[name] = item
                if not result:
                    for item in engine._iter_items():
                        name = item.get('name', '').strip()
                        if name:
                            result[name] = item
            else:
                for item in engine._iter_items():
                    name = item.get('name', '').strip()
                    if name:
                        result[name] = item
        except Exception as e:
            print(f"[MaterialDialog] Could not load material suggestions: {e}")

    if load_all_custom or custom_names:
        try:
            from ..registry.custom_material_db import CustomMaterialDB
            cdb = CustomMaterialDB()
            names_to_load = cdb.list_db_names() if load_all_custom else custom_names
            for db_name in names_to_load:
                for item in cdb.get_items(db_name):
                    name = item.get("name", "").strip()
                    if not name:
                        continue
                    if comp_lower:
                        t = item.get("type", "").lower()
                        if not (t == comp_lower or comp_lower in t or t in comp_lower):
                            continue
                    result[name] = item
        except Exception as e:
            print(f"[MaterialDialog] Could not load custom material suggestions: {e}")

    return result


# ---------------------------------------------------------------------------
# _SaveToCustomDBDialog
# ---------------------------------------------------------------------------


class _SaveToCustomDBDialog(QDialog):
    def __init__(self, existing_db_names: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save to Custom Database")
        self.setMinimumWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        layout.addWidget(QLabel(
            "Select an existing database or type a new name\n"
            "(e.g. biharSOR-2026, MyMaterials):"
        ))

        self.db_combo = QComboBox()
        self.db_combo.setEditable(True)
        self.db_combo.setMinimumHeight(32)
        self.db_combo.addItems(existing_db_names)
        self.db_combo.setCurrentIndex(-1)
        if self.db_combo.lineEdit():
            self.db_combo.lineEdit().setPlaceholderText("e.g. biharSOR-2026")
        layout.addWidget(self.db_combo)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.setMinimumHeight(32)
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_save(self):
        if not self.selected_name():
            QMessageBox.warning(self, "Missing Name", "Please enter a database name.")
            return
        self.accept()

    def selected_name(self) -> str:
        return self.db_combo.currentText().strip()


# ---------------------------------------------------------------------------
# MaterialDialog
# ---------------------------------------------------------------------------


class MaterialDialog(QDialog):
    _CUSTOM_CODE = "__custom__"

    def __init__(self, comp_name: str, parent=None, data: dict = None,
                 emissions_only: bool = False, recyclability_only: bool = False,
                 country: str = None):
        super().__init__(parent)
        self.is_edit = data is not None
        self.emissions_only = emissions_only
        self.recyclability_only = recyclability_only
        self._comp_name = comp_name
        self._sor_item = None
        self._is_customized = False
        self._sor_filling = False
        self._is_modified_by_user = False
        self._pre_allow_edit_source = None   # saved when "Allow editing" is checked

        mat_name = (data.get("values", {}).get("material_name", "") if data else "") or comp_name
        if recyclability_only:
            self.setWindowTitle(f"Edit Recyclability — {mat_name}")
        elif emissions_only:
            self.setWindowTitle(f"Edit Emission Data — {mat_name}")
        elif self.is_edit:
            self.setWindowTitle(f"Edit Material — {comp_name}")
        else:
            self.setWindowTitle(f"Add Material — {comp_name}")
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        v = data.get("values", {}) if self.is_edit else {}
        s = data.get("state", {}) if self.is_edit else {}

        saved_cu = v.get("_custom_units", v.get("_custom_unit"))
        if saved_cu is None:
            self._custom_units = []
        elif isinstance(saved_cu, dict):
            self._custom_units = [saved_cu]
        else:
            self._custom_units = list(saved_cu)

        dbl = QDoubleValidator()
        dbl.setNotation(QDoubleValidator.StandardNotation)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(10)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # ── SOR selector ──────────────────────────────────────────────────
        self._sor_options = (
            _list_sor_options(country)
            if not (emissions_only or recyclability_only)
            else []
        )
        self.sor_cb = None
        if self._sor_options:
            sor_row = QHBoxLayout()
            sor_row.setContentsMargins(0, 0, 0, 0)
            sor_row.setSpacing(8)
            sor_lbl = QLabel("Suggestions from:")
            sor_lbl.setStyleSheet("font-size: 11px; color: #555;")
            sor_row.addWidget(sor_lbl)
            self.sor_cb = QComboBox()
            self.sor_cb.setMinimumHeight(26)
            self.sor_cb.wheelEvent = lambda event: event.ignore()
            if len(self._sor_options) > 1:
                self.sor_cb.addItem("All databases", None)
            for opt in self._sor_options:
                self.sor_cb.addItem(opt["label"], opt["db_key"])
            sor_row.addWidget(self.sor_cb, stretch=1)
            root.addLayout(sor_row)

        # ── Sub-category filter ───────────────────────────────────────────
        self.type_filter_cb = None
        if self._sor_options:
            sub_row = QHBoxLayout()
            sub_row.setContentsMargins(0, 0, 0, 0)
            sub_row.setSpacing(8)
            sub_lbl = QLabel("Sub-category:")
            sub_lbl.setStyleSheet("font-size: 11px; color: #555;")
            sub_row.addWidget(sub_lbl)
            self.type_filter_cb = QComboBox()
            self.type_filter_cb.setMinimumHeight(26)
            self.type_filter_cb.wheelEvent = lambda event: event.ignore()
            sub_row.addWidget(self.type_filter_cb, stretch=1)
            root.addLayout(sub_row)
            self._populate_type_filter(preselect=comp_name)
            self.type_filter_cb.currentIndexChanged.connect(self._on_type_filter_changed)

        # ── Material Name ─────────────────────────────────────────────────
        root.addWidget(_lbl("Material Name *"))
        self.name_in = QLineEdit(v.get("material_name", ""))
        self.name_in.setPlaceholderText("e.g. Ready-mix Concrete M25")
        self.name_in.setMinimumHeight(32)
        root.addWidget(self.name_in)

        # ── Completer ─────────────────────────────────────────────────────
        self._suggestions = {}
        self._active_completer = None
        self._reload_suggestions()
        if self.sor_cb:
            self.sor_cb.currentIndexChanged.connect(self._on_sor_changed)

        # ── Allow-edit checkbox ───────────────────────────────────────────
        self._allow_edit_chk = QCheckBox("Allow editing DB-filled values")
        self._allow_edit_chk.setEnabled(False)
        self._allow_edit_chk.toggled.connect(self._on_allow_edit_toggled)
        root.addWidget(self._allow_edit_chk)

        # ── Quantity + Unit ───────────────────────────────────────────────
        qty_unit_row = QHBoxLayout()
        qty_unit_row.setSpacing(12)

        qty_col = QVBoxLayout()
        qty_col.setSpacing(3)
        qty_col.addWidget(_lbl("Quantity *"))
        qty_val = v.get("quantity", "")
        self.qty_in = QLineEdit("" if not qty_val else str(qty_val))
        self.qty_in.setPlaceholderText("e.g. 100")
        self.qty_in.setMinimumHeight(32)
        self.qty_in.setValidator(dbl)
        qty_col.addWidget(self.qty_in)
        qty_unit_row.addLayout(qty_col, stretch=1)

        unit_col = QVBoxLayout()
        unit_col.setSpacing(3)
        unit_col.addWidget(_lbl("Unit *"))
        current_unit = v.get("unit", "m3")
        self.unit_in = self._build_unit_dropdown(current_unit, None)
        self.unit_in.wheelEvent = lambda event: event.ignore()
        self.unit_in.currentIndexChanged.connect(self._on_unit_combobox_changed)
        unit_col.addWidget(self.unit_in)
        qty_unit_row.addLayout(unit_col, stretch=2)

        root.addLayout(qty_unit_row)

        # ── Rate + Rate Source ────────────────────────────────────────────
        rate_row = QHBoxLayout()
        rate_row.setSpacing(12)

        rate_col = QVBoxLayout()
        rate_col.setSpacing(3)
        rate_col.addWidget(_lbl("Rate (Cost)"))
        rate_val = v.get("rate", "")
        self.rate_in = QLineEdit("" if not rate_val else str(rate_val))
        self.rate_in.setPlaceholderText("e.g. 4500")
        self.rate_in.setMinimumHeight(32)
        self.rate_in.setValidator(dbl)
        rate_col.addWidget(self.rate_in)
        rate_row.addLayout(rate_col, stretch=1)

        src_col = QVBoxLayout()
        src_col.setSpacing(3)
        src_col.addWidget(_lbl("Rate Source"))
        # Store original source so it can be restored when "Allow editing" is unchecked
        self._original_source = v.get("rate_source", "")
        self.src_in = QLineEdit(self._original_source)
        self.src_in.setPlaceholderText("e.g. DSR 2023, Market Rate")
        self.src_in.setMinimumHeight(32)
        # Clear the source field when editing an existing material;
        # it is restored when the user unchecks "Allow editing DB-filled values"
        # or selects a new DB suggestion.
        if self.is_edit:
            self.src_in.clear()
        src_col.addWidget(self.src_in)
        rate_row.addLayout(src_col, stretch=2)

        root.addLayout(rate_row)

        # ── Carbon Emission ───────────────────────────────────────────────
        root.addWidget(_divider())

        carbon_hdr = QHBoxLayout()
        carbon_title = QLabel("Carbon Emission")
        carbon_title.setStyleSheet("font-weight: 600; font-size: 12px;")
        carbon_hdr.addWidget(carbon_title)
        carbon_hdr.addStretch()
        self.carbon_chk = QCheckBox("Include")
        self.carbon_chk.setChecked(s.get("included_in_carbon_emission", True))
        carbon_hdr.addWidget(self.carbon_chk)
        root.addLayout(carbon_hdr)

        self.carbon_container = QWidget()
        cl = QVBoxLayout(self.carbon_container)
        cl.setContentsMargins(0, 4, 0, 0)
        cl.setSpacing(8)

        ef_row = QHBoxLayout()
        ef_row.setSpacing(12)

        ef_col = QVBoxLayout()
        ef_col.setSpacing(3)
        ef_col.addWidget(_lbl("Emission Factor"))
        ef_val = v.get("carbon_emission", "")
        self.carbon_em_in = QLineEdit("" if not ef_val else str(ef_val))
        self.carbon_em_in.setPlaceholderText("e.g. 0.179")
        self.carbon_em_in.setMinimumHeight(32)
        self.carbon_em_in.setValidator(dbl)
        ef_col.addWidget(self.carbon_em_in)
        ef_row.addLayout(ef_col, stretch=1)

        denom_col = QVBoxLayout()
        denom_col.setSpacing(3)
        denom_col.addWidget(_lbl("Per Unit  (kgCO₂e / ...)"))
        self.carbon_denom_cb = QComboBox()
        self.carbon_denom_cb.setMinimumHeight(32)
        self.carbon_denom_cb.wheelEvent = lambda event: event.ignore()
        self.carbon_denom_cb.setModel(self._build_full_unit_model())

        existing_carbon_unit = v.get("carbon_unit", "")
        if existing_carbon_unit and "/" in existing_carbon_unit:
            saved_denom = existing_carbon_unit.split("/")[-1].strip()
            didx = self.carbon_denom_cb.findData(saved_denom)
            if didx >= 0:
                self.carbon_denom_cb.setCurrentIndex(didx)
        else:
            didx = self.carbon_denom_cb.findData(current_unit)
            if didx >= 0:
                self.carbon_denom_cb.setCurrentIndex(didx)

        denom_col.addWidget(self.carbon_denom_cb)
        ef_row.addLayout(denom_col, stretch=1)

        cl.addLayout(ef_row)

        self.cf_row_widget = QWidget()
        cf_inner = QVBoxLayout(self.cf_row_widget)
        cf_inner.setContentsMargins(0, 0, 0, 0)
        cf_inner.setSpacing(3)

        self.cf_row_lbl = _lbl("Conversion Factor")
        cf_inner.addWidget(self.cf_row_lbl)

        cf_input_row = QHBoxLayout()
        cf_input_row.setSpacing(6)
        self.cf_prefix_lbl = QLabel("1 unit =")
        self.cf_prefix_lbl.setStyleSheet("color: #555; font-size: 12px;")
        cf_input_row.addWidget(self.cf_prefix_lbl)

        cf_val = v.get("conversion_factor", "")
        self.conv_factor_in = QLineEdit("" if not cf_val else str(cf_val))
        self.conv_factor_in.setPlaceholderText("e.g. 2400")
        self.conv_factor_in.setMinimumHeight(32)
        self.conv_factor_in.setMaximumWidth(120)
        self.conv_factor_in.setValidator(dbl)
        cf_input_row.addWidget(self.conv_factor_in)

        self.cf_suffix_lbl = QLabel("unit")
        self.cf_suffix_lbl.setStyleSheet("color: #555; font-size: 12px;")
        cf_input_row.addWidget(self.cf_suffix_lbl)

        self.cf_status_lbl = QLabel("")
        self.cf_status_lbl.setStyleSheet("font-size: 11px; color: #888;")
        cf_input_row.addWidget(self.cf_status_lbl)
        cf_input_row.addStretch()
        cf_inner.addLayout(cf_input_row)

        cl.addWidget(self.cf_row_widget)

        self.formula_lbl = QLabel("")
        self.formula_lbl.setWordWrap(True)
        self.formula_lbl.setStyleSheet("font-size: 11px; color: #555;")
        self.formula_lbl.setVisible(False)
        cl.addWidget(self.formula_lbl)

        root.addWidget(self.carbon_container)

        # ── Recyclability ─────────────────────────────────────────────────
        root.addWidget(_divider())

        recycle_hdr = QHBoxLayout()
        recycle_title = QLabel("Recyclability")
        recycle_title.setStyleSheet("font-weight: 600; font-size: 12px;")
        recycle_hdr.addWidget(recycle_title)
        recycle_hdr.addStretch()
        self.recycle_chk = QCheckBox("Include")
        self.recycle_chk.setChecked(s.get("included_in_recyclability", True))
        recycle_hdr.addWidget(self.recycle_chk)
        root.addLayout(recycle_hdr)

        self.recycle_container = QWidget()
        rl = QHBoxLayout(self.recycle_container)
        rl.setContentsMargins(0, 4, 0, 0)
        rl.setSpacing(12)

        scrap_col = QVBoxLayout()
        scrap_col.setSpacing(3)
        scrap_col.addWidget(_lbl("Scrap Rate (per unit)"))
        scrap_val = v.get("scrap_rate", "")
        self.scrap_in = QLineEdit("" if not scrap_val else str(scrap_val))
        self.scrap_in.setPlaceholderText("e.g. 50")
        self.scrap_in.setMinimumHeight(32)
        self.scrap_in.setValidator(dbl)
        scrap_col.addWidget(self.scrap_in)
        rl.addLayout(scrap_col, stretch=1)

        recov_col = QVBoxLayout()
        recov_col.setSpacing(3)
        recov_col.addWidget(_lbl("Recovery after Demolition (%)"))
        recov_val = v.get("post_demolition_recovery_percentage", "")
        self.recycling_perc_in = QLineEdit("" if not recov_val else str(recov_val))
        self.recycling_perc_in.setPlaceholderText("e.g. 90")
        self.recycling_perc_in.setMinimumHeight(32)
        self.recycling_perc_in.setValidator(dbl)
        recov_col.addWidget(self.recycling_perc_in)
        rl.addLayout(recov_col, stretch=1)

        root.addWidget(self.recycle_container)

        # ── Categorization ────────────────────────────────────────────────
        root.addWidget(_divider())

        cat_row = QHBoxLayout()
        cat_row.setSpacing(12)

        grade_col = QVBoxLayout()
        grade_col.setSpacing(3)
        grade_col.addWidget(_lbl("Grade"))
        self.grade_in = QLineEdit(v.get("grade", ""))
        self.grade_in.setPlaceholderText("e.g. M25, Fe500")
        self.grade_in.setMinimumHeight(32)
        grade_col.addWidget(self.grade_in)
        cat_row.addLayout(grade_col, stretch=1)

        type_col = QVBoxLayout()
        type_col.setSpacing(3)
        type_col.addWidget(_lbl("Type"))
        self.type_in = QComboBox()
        self.type_in.setEditable(True)
        self.type_in.setMinimumHeight(32)
        self.type_in.wheelEvent = lambda event: event.ignore()
        for t in ["Concrete", "Steel", "Masonry", "Timber", "Finishing",
                  "Insulation", "Glass", "Aluminum", "Other"]:
            self.type_in.addItem(t)
        existing_type = v.get("type", "")
        if existing_type:
            tidx = self.type_in.findText(existing_type)
            if tidx >= 0:
                self.type_in.setCurrentIndex(tidx)
            else:
                self.type_in.setCurrentText(existing_type)
        else:
            self.type_in.setCurrentIndex(-1)
            self.type_in.lineEdit().setPlaceholderText("e.g. Concrete, Steel")
        type_col.addWidget(self.type_in)
        cat_row.addLayout(type_col, stretch=1)

        root.addLayout(cat_row)
        root.addStretch()

        # ── Button bar ────────────────────────────────────────────────────
        btn_bar = QWidget()
        btn_bar.setStyleSheet("border-top: 1px solid #ddd;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(20, 10, 20, 10)

        self.save_btn = QPushButton(
            "Update Changes" if self.is_edit else "Add to Table"
        )
        self.save_btn.setStyleSheet("font-weight: bold; padding: 6px 20px;")
        self.save_btn.setMinimumHeight(34)
        self.save_btn.clicked.connect(self.validate_and_accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(34)
        self.cancel_btn.clicked.connect(self.reject)

        self.custom_db_btn = QPushButton("Save to Custom DB…")
        self.custom_db_btn.setMinimumHeight(34)
        self.custom_db_btn.setToolTip("Save this material to a user-created custom database")
        self.custom_db_btn.clicked.connect(self._on_save_to_custom_db)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.custom_db_btn)
        outer.addWidget(btn_bar)

        # ── Freeze fields for emissions_only / recyclability_only modes ───
        if emissions_only:
            for w in (self.name_in, self.qty_in, self.rate_in, self.src_in,
                      self.scrap_in, self.recycling_perc_in, self.grade_in):
                w.setReadOnly(True)
            self.unit_in.setEnabled(False)
            self.recycle_chk.setEnabled(False)
            self.type_in.setEnabled(False)
            self.save_btn.setText("Save Emission Data")
        elif recyclability_only:
            for w in (self.name_in, self.qty_in, self.rate_in, self.src_in,
                      self.carbon_em_in, self.conv_factor_in, self.grade_in):
                w.setReadOnly(True)
            self.unit_in.setEnabled(False)
            self.carbon_chk.setEnabled(False)
            self.carbon_denom_cb.setEnabled(False)
            self.type_in.setEnabled(False)
            self.save_btn.setText("Save Recyclability Data")

        # ── Wire signals ──────────────────────────────────────────────────
        self.carbon_chk.toggled.connect(self.carbon_container.setVisible)
        self.recycle_chk.toggled.connect(self.recycle_container.setVisible)
        self.carbon_container.setVisible(self.carbon_chk.isChecked())
        self.recycle_container.setVisible(self.recycle_chk.isChecked())

        self.carbon_denom_cb.currentIndexChanged.connect(self._on_denom_combobox_changed)
        self.carbon_em_in.textChanged.connect(self._update_formula_preview)
        self.conv_factor_in.textChanged.connect(self._update_formula_preview)
        self.qty_in.textChanged.connect(self._update_formula_preview)

        for _w in (self.name_in, self.qty_in, self.rate_in, self.src_in,
                   self.carbon_em_in, self.conv_factor_in,
                   self.scrap_in, self.recycling_perc_in, self.grade_in):
            _w.textChanged.connect(self._on_field_manually_changed)
        self.unit_in.currentIndexChanged.connect(self._on_field_manually_changed)
        self.carbon_denom_cb.currentIndexChanged.connect(self._on_field_manually_changed)
        self.type_in.currentIndexChanged.connect(self._on_field_manually_changed)

        self._update_cf()

    # ── SOR / suggestion helpers ──────────────────────────────────────────

    def _reload_suggestions(self):
        db_keys = None
        if self.sor_cb:
            key = self.sor_cb.currentData()
            if key:
                db_keys = [key]

        if self.type_filter_cb is not None:
            type_filter = self.type_filter_cb.currentData()
        else:
            type_filter = self._comp_name

        self._suggestions = _load_material_suggestions(
            db_keys=db_keys, comp_name=type_filter
        )

        if self._suggestions:
            model = QStringListModel(sorted(self._suggestions.keys()), self)
            if self._active_completer is None:
                self._active_completer = QCompleter(model, self)
                self._active_completer.setCaseSensitivity(Qt.CaseInsensitive)
                self._active_completer.setFilterMode(Qt.MatchContains)
                self._active_completer.setMaxVisibleItems(10)
                self._active_completer.activated.connect(self._on_suggestion_selected)
                self.name_in.setCompleter(self._active_completer)
            else:
                self._active_completer.setModel(model)
        else:
            self.name_in.setCompleter(None)
            self._active_completer = None

    def _populate_type_filter(self, preselect: str = None):
        db_keys = None
        if self.sor_cb:
            key = self.sor_cb.currentData()
            if key:
                db_keys = [key]

        types = _list_sor_types(db_keys=db_keys)

        self.type_filter_cb.blockSignals(True)
        self.type_filter_cb.clear()
        self.type_filter_cb.addItem("All types", None)
        for t in types:
            self.type_filter_cb.addItem(t, t)

        best_idx = 0
        if preselect:
            pre_lower = preselect.strip().lower()
            for i in range(1, self.type_filter_cb.count()):
                t = (self.type_filter_cb.itemData(i) or "").lower()
                if t == pre_lower or pre_lower in t or t in pre_lower:
                    best_idx = i
                    break

        self.type_filter_cb.setCurrentIndex(best_idx)
        self.type_filter_cb.blockSignals(False)

    def _on_sor_changed(self):
        if self.type_filter_cb is not None:
            current_type = self.type_filter_cb.currentData()
            self._populate_type_filter(preselect=current_type or self._comp_name)
        self._reload_suggestions()

    def _on_type_filter_changed(self):
        self._reload_suggestions()

    def _lock_autofilled_fields(self, lock: bool):
        self.unit_in.setEnabled(not lock)
        self.rate_in.setReadOnly(lock)
        self.src_in.setReadOnly(lock)
        self.carbon_em_in.setReadOnly(lock)
        self.carbon_denom_cb.setEnabled(not lock)
        self.conv_factor_in.setReadOnly(lock)

    def _on_allow_edit_toggled(self, checked: bool):
        """Unlock autofilled fields when checked; restore values and re-lock when unchecked."""
        if checked:
            # Save current source values then clear them so the user can enter their own
            self._pre_allow_edit_source = self.src_in.text()
            self._sor_filling = True
            self.src_in.clear()
            self._sor_filling = False
            self._is_modified_by_user = True
        else:
            if self._sor_item is not None:
                # Restore all values from the DB suggestion that was selected
                self._sor_filling = True
                try:
                    item = self._sor_item
                    unit = item.get('unit', '')
                    if unit:
                        idx = _resolve_unit_code(unit, self.unit_in)
                        if idx >= 0:
                            self.unit_in.setCurrentIndex(idx)

                    rate = item.get('rate', '')
                    self.rate_in.setText(str(rate) if rate not in ('', 'not_available', None) else '')

                    src = item.get('rate_src', '')
                    self.src_in.setText(str(src) if src not in ('', 'not_available', None) else '')

                    carbon = item.get('carbon_emission', 'not_available')
                    if carbon not in ('not_available', '', None):
                        self.carbon_em_in.setText(str(carbon))
                        self.carbon_chk.setChecked(True)
                    else:
                        self.carbon_em_in.setText('')

                    denom = item.get('carbon_emission_units_den', 'not_available')
                    if denom not in ('not_available', '', None):
                        didx = _resolve_unit_code(denom, self.carbon_denom_cb)
                        if didx >= 0:
                            self.carbon_denom_cb.setCurrentIndex(didx)

                    cf = item.get('conversion_factor', 'not_available')
                    self.conv_factor_in.setText(str(cf) if cf not in ('not_available', '', None) else '')

                    recycleable = item.get('recycleable', '')
                    self.recycle_chk.setChecked(
                        bool(recycleable) and recycleable.lower() != 'non-recyclable'
                    )
                finally:
                    self._sor_filling = False
                self._is_customized = False
                self._is_modified_by_user = False
                self._update_cf()
            else:
                # No DB suggestion — restore the source saved at check time, or the original
                restore_src = getattr(self, '_pre_allow_edit_source', None)
                if restore_src is None:
                    restore_src = self._original_source
                if restore_src:
                    self._sor_filling = True
                    self.src_in.setText(restore_src)
                    self._sor_filling = False

        self._lock_autofilled_fields(not checked)

    def _on_save_to_custom_db(self):
        if not self.name_in.text().strip():
            QMessageBox.warning(
                self, "Missing Name",
                "Please enter a material name before saving to a custom database."
            )
            return

        try:
            from ..registry.custom_material_db import CustomMaterialDB
            cdb = CustomMaterialDB()
            existing = cdb.list_db_names()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open custom database:\n{e}")
            return

        dlg = _SaveToCustomDBDialog(existing, parent=self)
        if not dlg.exec():
            return

        db_name = dlg.selected_name()
        try:
            cdb.save_material(db_name, self.get_values())
            QMessageBox.information(
                self, "Saved",
                f"Material saved to '{db_name}'.\n"
                f"It will appear in suggestions next time you open this dialog."
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))

    def _on_field_manually_changed(self):
        if not self._sor_filling and self._sor_item is not None:
            self._is_customized = True

    # ── Suggestion auto-fill ──────────────────────────────────────────────

    def _on_suggestion_selected(self, name: str):
        item = self._suggestions.get(name)
        if not item:
            return

        self._sor_filling = True
        try:
            unit = item.get('unit', '')
            if unit:
                idx = _resolve_unit_code(unit, self.unit_in)
                if idx >= 0:
                    self.unit_in.setCurrentIndex(idx)

            rate = item.get('rate', '')
            if rate not in ('', 'not_available', None):
                self.rate_in.setText(str(rate))

            src = item.get('rate_src', '')
            if src not in ('', 'not_available', None):
                self.src_in.setText(str(src))

            carbon = item.get('carbon_emission', 'not_available')
            if carbon not in ('not_available', '', None):
                self.carbon_em_in.setText(str(carbon))
                self.carbon_chk.setChecked(True)

            denom = item.get('carbon_emission_units_den', 'not_available')
            if denom not in ('not_available', '', None):
                didx = _resolve_unit_code(denom, self.carbon_denom_cb)
                if didx >= 0:
                    self.carbon_denom_cb.setCurrentIndex(didx)

            cf = item.get('conversion_factor', 'not_available')
            if cf not in ('not_available', '', None):
                self.conv_factor_in.setText(str(cf))

            recycleable = item.get('recycleable', '')
            if recycleable and recycleable.lower() != 'non-recyclable':
                self.recycle_chk.setChecked(True)
            else:
                self.recycle_chk.setChecked(False)

            self._sor_item = item
            self._is_customized = False

        finally:
            self._sor_filling = False

        self._update_cf()

        self._allow_edit_chk.blockSignals(True)
        self._allow_edit_chk.setChecked(False)
        self._allow_edit_chk.blockSignals(False)
        self._allow_edit_chk.setEnabled(True)
        self._lock_autofilled_fields(True)
        self._is_modified_by_user = False

    # ── Unit model helpers ────────────────────────────────────────────────

    def _build_full_unit_model(self) -> QStandardItemModel:
        model = QStandardItemModel()

        _display = {"m2": "m²", "m3": "m³", "sqm": "sqm", "sqft": "sq.ft", "sqyd": "sq.yd", "cum": "cum"}

        for dim, units in _CONSTRUCTION_UNITS.units.items():
            sep = QStandardItem(f"── {dim} ──")
            sep.setFlags(Qt.ItemFlag(0))
            model.appendRow(sep)
            for code, info in units.items():
                si_val = UNIT_TO_SI.get(code)
                si_unit_code = SI_BASE_UNITS.get(dim, "")
                sym = _display.get(code, info["name"].split(",")[0].strip())
                si_sym = _display.get(si_unit_code, si_unit_code)
                short_name = info["name"].split(",")[-1].strip()
                item = QStandardItem(f"{sym} — {short_name}")
                item.setData(code, Qt.UserRole)
                tooltip = (
                    f"1 {sym} = {si_val:g} {si_sym}  |  Example: {info['example']}"
                    if si_val is not None and si_val != 1.0
                    else f"SI base unit  |  Example: {info['example']}"
                )
                item.setData(tooltip, Qt.ToolTipRole)
                model.appendRow(item)

        if self._custom_units:
            sep_c = QStandardItem("── Custom ──")
            sep_c.setFlags(Qt.ItemFlag(0))
            model.appendRow(sep_c)
            for cu in self._custom_units:
                display = f"{cu['symbol']} — {cu['name']}" if cu.get("name") else cu["symbol"]
                item = QStandardItem(display)
                item.setData(cu["symbol"], Qt.UserRole)
                item.setData(
                    f"Custom: 1 {cu['symbol']} = {cu['to_si']:g} {cu.get('si_unit', '')}  |  {cu.get('dimension', '')}",
                    Qt.ToolTipRole,
                )
                model.appendRow(item)

        sep2 = QStandardItem("──────────────")
        sep2.setFlags(Qt.ItemFlag(0))
        model.appendRow(sep2)
        add_item = QStandardItem("+ Add Custom Unit...")
        add_item.setData(self._CUSTOM_CODE, Qt.UserRole)
        model.appendRow(add_item)

        return model

    def _build_unit_dropdown(self, current_unit: str, _=None) -> QComboBox:
        cb = QComboBox()
        cb.setMinimumHeight(30)
        cb.setModel(self._build_full_unit_model())
        idx = cb.findData(current_unit)
        if idx >= 0:
            cb.setCurrentIndex(idx)
        return cb

    def _get_unit_info(self, code: str):
        si_val = UNIT_TO_SI.get(code)
        dim = UNIT_DIMENSION.get(code)
        if si_val is None:
            cu = next((c for c in self._custom_units if c["symbol"] == code), None)
            if cu:
                si_val = cu["to_si"]
                dim = cu["dimension"]
        return si_val, dim

    def _rebuild_unit_models(self, mat_sel: str = None, denom_sel: str = None):
        self.unit_in.blockSignals(True)
        self.carbon_denom_cb.blockSignals(True)

        self.unit_in.setModel(self._build_full_unit_model())
        self.carbon_denom_cb.setModel(self._build_full_unit_model())

        if mat_sel:
            idx = self.unit_in.findData(mat_sel)
            if idx >= 0:
                self.unit_in.setCurrentIndex(idx)
        if denom_sel:
            idx = self.carbon_denom_cb.findData(denom_sel)
            if idx >= 0:
                self.carbon_denom_cb.setCurrentIndex(idx)

        self.unit_in.blockSignals(False)
        self.carbon_denom_cb.blockSignals(False)

    def _add_custom_unit(self, triggering_cb: QComboBox):
        prev_mat = self.unit_in.currentData()
        prev_denom = self.carbon_denom_cb.currentData()

        dialog = CustomUnitDialog(self)
        if dialog.exec():
            cu = dialog.get_unit()
            self._custom_units.append(cu)
            new_sym = cu["symbol"]
            mat_sel = new_sym if triggering_cb is self.unit_in else (prev_mat if prev_mat != self._CUSTOM_CODE else new_sym)
            denom_sel = new_sym if triggering_cb is self.carbon_denom_cb else (prev_denom if prev_denom != self._CUSTOM_CODE else new_sym)
            self._rebuild_unit_models(mat_sel=mat_sel, denom_sel=denom_sel)
        else:
            prev = prev_mat if triggering_cb is self.unit_in else prev_denom
            restore = prev if (prev and prev != self._CUSTOM_CODE) else None
            triggering_cb.blockSignals(True)
            if restore:
                idx = triggering_cb.findData(restore)
                if idx >= 0:
                    triggering_cb.setCurrentIndex(idx)
            triggering_cb.blockSignals(False)

        self._update_cf()

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_unit_combobox_changed(self):
        code = self.unit_in.currentData()
        if code == self._CUSTOM_CODE:
            self._add_custom_unit(self.unit_in)
            return
        if code:
            self.carbon_denom_cb.blockSignals(True)
            didx = self.carbon_denom_cb.findData(code)
            if didx >= 0:
                self.carbon_denom_cb.setCurrentIndex(didx)
            self.carbon_denom_cb.blockSignals(False)
        self._update_cf()

    def _on_denom_combobox_changed(self):
        code = self.carbon_denom_cb.currentData()
        if code == self._CUSTOM_CODE:
            self._add_custom_unit(self.carbon_denom_cb)
            return
        self._update_cf()

    # ── Auto conversion factor ────────────────────────────────────────────

    def _update_cf(self):
        mat_code = self.unit_in.currentData() or ""
        denom_code = self.carbon_denom_cb.currentData() or ""
        mat_sym = mat_code or "unit"

        mat_si, mat_dim = self._get_unit_info(mat_code)
        denom_si, denom_dim = self._get_unit_info(denom_code)

        if mat_code == denom_code:
            self.conv_factor_in.setText("1")
            self.cf_row_widget.setVisible(False)
        elif mat_si is not None and denom_si is not None and mat_dim == denom_dim:
            suggested = mat_si / denom_si
            self.conv_factor_in.setText(f"{suggested:g}")
            self.cf_row_widget.setVisible(True)
            self.cf_prefix_lbl.setText(f"1 {mat_sym} =")
            self.cf_suffix_lbl.setText(denom_code or "unit")
            self.cf_status_lbl.setText("(suggested — you can change this)")
        else:
            self.cf_row_widget.setVisible(True)
            self.cf_prefix_lbl.setText(f"1 {mat_sym} =")
            self.cf_suffix_lbl.setText(denom_code or "unit")
            if mat_dim and denom_dim:
                self.cf_status_lbl.setText(f"e.g. density for {mat_dim} → {denom_dim}")
            else:
                self.cf_status_lbl.setText("")

        self._update_formula_preview()

    # ── Formula preview ───────────────────────────────────────────────────

    def _update_formula_preview(self):
        try:
            qty = float(self.qty_in.text() or 0)
            ef = float(self.carbon_em_in.text() or 0)
            cf = float(self.conv_factor_in.text() or 0)

            mat_code = self.unit_in.currentData()
            mat_sym = mat_code or "unit"
            denom_code = self.carbon_denom_cb.currentData() or ""

            if qty > 0 and ef > 0 and cf > 0:
                total = qty * cf * ef
                if cf == 1.0:
                    self.formula_lbl.setText(
                        f"{qty:g} {mat_sym}  ×  {ef:g} kgCO₂e/{denom_code}"
                        f"  =  {total:,.3f} kgCO₂e"
                    )
                else:
                    self.formula_lbl.setText(
                        f"{qty:g} {mat_sym}  ×  {cf:g}  ×  {ef:g} kgCO₂e/{denom_code}"
                        f"  =  {total:,.3f} kgCO₂e"
                    )
                self.formula_lbl.setVisible(True)
            else:
                self.formula_lbl.setVisible(False)
        except (ValueError, ZeroDivisionError):
            self.formula_lbl.setVisible(False)

    # ── Validation ────────────────────────────────────────────────────────

    def validate_and_accept(self):
        if not self.name_in.text().strip():
            QMessageBox.critical(self, "Validation Error", "Material Name is required.")
            return

        try:
            qty = float(self.qty_in.text() or 0)
        except ValueError:
            qty = 0
        if qty <= 0:
            QMessageBox.critical(
                self, "Validation Error", "Quantity must be greater than zero."
            )
            return

        if self.carbon_chk.isChecked():
            try:
                ef = float(self.carbon_em_in.text() or 0)
                cf = float(self.conv_factor_in.text() or 0)
            except ValueError:
                ef, cf = 0, 0

            if ef <= 0:
                reply = QMessageBox.warning(
                    self, "Emission Factor",
                    "Emission factor is zero or empty — carbon calculation will be excluded.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return
                self.carbon_chk.setChecked(False)
            elif cf <= 0:
                reply = QMessageBox.warning(
                    self, "Conversion Factor",
                    "Conversion factor is zero — carbon calculation will be excluded.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return
                self.carbon_chk.setChecked(False)
            else:
                mat_code = self.unit_in.currentData() or ""
                denom_code = self.carbon_denom_cb.currentData() or ""
                _, mat_dim = self._get_unit_info(mat_code)
                _, denom_dim = self._get_unit_info(denom_code)
                if mat_dim != denom_dim and abs(cf - 1.0) < 1e-6:
                    res = QMessageBox.warning(
                        self, "Check Conversion Factor",
                        f"Material dimension ({mat_dim}) and carbon unit dimension ({denom_dim}) differ.\n"
                        f"Conversion factor is 1.0 — this is likely incorrect.\n\nContinue anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if res == QMessageBox.No:
                        return

        if self.recycle_chk.isChecked():
            try:
                scrap = float(self.scrap_in.text() or 0)
                recycle = float(self.recycling_perc_in.text() or 0)
            except ValueError:
                scrap, recycle = 0, 0
            if scrap <= 0 and recycle <= 0:
                reply = QMessageBox.warning(
                    self, "Recyclability",
                    "Both scrap rate and recovery percentage are zero — recyclability will be excluded.\n\nContinue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return
                self.recycle_chk.setChecked(False)

        self.accept()

    # ── Output ────────────────────────────────────────────────────────────

    def get_values(self) -> dict:
        actual_unit = self.unit_in.currentData() or ""
        unit_to_si, _ = self._get_unit_info(actual_unit)
        if unit_to_si is None:
            unit_to_si = 1.0

        recycle_pct = (
            float(self.recycling_perc_in.text() or 0)
            if self.recycle_chk.isChecked()
            else 0.0
        )
        denom_code = self.carbon_denom_cb.currentData() or ""

        return {
            "material_name": self.name_in.text().strip(),
            "quantity": float(self.qty_in.text() or 0),
            "unit": actual_unit,
            "unit_to_si": unit_to_si,
            "_custom_units": self._custom_units,
            "rate": float(self.rate_in.text() or 0),
            "rate_source": self.src_in.text().strip(),
            "carbon_emission": (
                float(self.carbon_em_in.text() or 0)
                if self.carbon_chk.isChecked()
                else 0.0
            ),
            "carbon_unit": f"kgCO₂e/{denom_code}",
            "conversion_factor": (
                float(self.conv_factor_in.text() or 1)
                if self.carbon_chk.isChecked()
                else 1.0
            ),
            "scrap_rate": (
                float(self.scrap_in.text() or 0)
                if self.recycle_chk.isChecked()
                else 0.0
            ),
            "post_demolition_recovery_percentage": recycle_pct,
            "is_recyclable": recycle_pct > 0,
            "grade": self.grade_in.text().strip(),
            "type": self.type_in.currentText().strip(),
            "_included_in_carbon_emission": self.carbon_chk.isChecked(),
            "_included_in_recyclability": self.recycle_chk.isChecked(),
            "_from_sor": self._sor_item is not None,
            "_sor_db_key": self._sor_item.get("db_key", "") if self._sor_item else "",
            "_is_customized": self._is_customized if self._sor_item is not None else False,
            "_is_modified_by_user": self._is_modified_by_user,
        }
