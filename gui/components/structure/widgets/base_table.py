from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QSize


class StructureTableWidget(QTableWidget):
    def __init__(self, parent_manager, component_name, is_trash_view=False):
        super().__init__()
        self.manager = parent_manager
        self.component_name = component_name
        self.is_trash_view = is_trash_view

        # Setup 6 columns: Work Name, Rate, Qty, Source, Total, Action
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(
            ["Work Name", "Rate", "Qty", "Source", "Total", "Action"]
        )
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setMinimumSectionSize(100)

        # Set proportional default widths
        self.setColumnWidth(0, 220)  # Work Name
        self.setColumnWidth(1, 80)  # Rate
        self.setColumnWidth(2, 65)  # Qty
        self.setColumnWidth(3, 110)  # Source
        self.setColumnWidth(4, 90)  # Total
        self.setColumnWidth(5, 70)  # Action
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Disable direct typing in cells (Double-click logic handles editing)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        self.verticalHeader().setDefaultSectionSize(35)

        # Connect Double Click for Editing (only if not in trash)
        if not self.is_trash_view:
            self.cellDoubleClicked.connect(self._on_cell_double_clicked)

        self.update_height()

    def _on_cell_double_clicked(self, row, column):
        """Pass the visual row index to the manager to find the data and open the edit dialog."""
        self.manager.open_edit_dialog(self.component_name, row)

    def sizeHint(self):
        header_h = self.horizontalHeader().height() or 35
        rows_h = self.rowCount() * self.verticalHeader().defaultSectionSize()
        return QSize(super().sizeHint().width(), max(150, header_h + rows_h + 15))

    def minimumSizeHint(self):
        return self.sizeHint()

    def update_height(self):
        """Notifies the layout that the size hint changed — no fixed height needed."""
        self.updateGeometry()

    def add_row(self, item_data, original_index):
        """
        Adds a row to the table reading from the 'values' nested block.
        original_index links the visual row back to the full list in the JSON engine.
        """
        self.blockSignals(True)
        row = self.rowCount()
        self.insertRow(row)

        # Access the nested 'values' block from your new schema
        v = item_data.get("values", {})

        # 0. Work Name (Mapped to material_name)
        self.setItem(row, 0, QTableWidgetItem(v.get("material_name", "New Item")))

        # 1. Rate
        rate_item = QTableWidgetItem(str(v.get("rate", 0)))
        rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 1, rate_item)

        # 2. Qty
        unit = v.get("unit", "")
        _UNIT_DISPLAY = {"m2": "m²", "m3": "m³", "sqm": "m²", "cum": "m³", "sqft": "sq.ft", "sqyd": "sq.yd"}
        unit = _UNIT_DISPLAY.get(unit.lower(), unit) if unit else unit
        qty_text = f"{v.get('quantity', 0)} {unit}".strip()
        qty_item = QTableWidgetItem(qty_text)
        qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 2, qty_item)

        # 3. Source (Mapped to rate_source)
        self.setItem(row, 3, QTableWidgetItem(v.get("rate_source", "Manual")))

        # 4. Total Calculation
        try:
            rate = float(v.get("rate", 0) or 0)
            qty = float(v.get("quantity", 0) or 0)
            total = rate * qty
        except (ValueError, TypeError):
            total = 0.0

        total_item = QTableWidgetItem(f"{total:.2f}")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)  # Read-only
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 4, total_item)

        # 5. Action Button (Trash or Restore)
        btn_text = "Restore" if self.is_trash_view else "Trash"
        action_btn = QPushButton(btn_text)
        action_btn.setFocusPolicy(Qt.NoFocus)

        # Logic: toggle the state['in_trash'] flag via the manager
        action_btn.clicked.connect(
            lambda checked=False, idx=original_index: self.manager.toggle_trash_status(
                self.component_name, idx, not self.is_trash_view
            )
        )
        self.setCellWidget(row, 5, action_btn)

        self.blockSignals(False)
        self.update_height()

    def freeze(self, frozen: bool = True):
        """Disable/enable the Trash button in every row."""
        for row in range(self.rowCount()):
            btn = self.cellWidget(row, 5)
            if btn:
                btn.setEnabled(not frozen)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total = self.viewport().width()
        min_w = 100

        # Proportional widths (must all be >= min_w)
        widths = {
            0: max(min_w, int(total * 0.32)),  # Work Name
            1: max(min_w, int(total * 0.12)),  # Rate
            2: max(min_w, int(total * 0.10)),  # Qty
            3: max(min_w, int(total * 0.16)),  # Source
            4: max(min_w, int(total * 0.14)),  # Total
            5: max(min_w, int(total * 0.10)),  # Action
        }

        for col, width in widths.items():
            self.setColumnWidth(col, width)
