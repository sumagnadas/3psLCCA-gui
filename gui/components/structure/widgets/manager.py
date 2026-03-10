from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QGroupBox,
    QInputDialog,
)
from PySide6.QtCore import Qt, QTimer
import time
import uuid
import datetime

from .base_table import StructureTableWidget
from .material_dialog import MaterialDialog


# ---------------------------------------------------------------------------
# StructureManagerWidget
# ---------------------------------------------------------------------------


class StructureManagerWidget(QWidget):
    def __init__(self, controller, chunk_name, default_components):
        super().__init__()
        self.controller = controller
        self.chunk_name = chunk_name
        self.default_components = default_components
        self.sections = {}
        self.data = {}

        self._frozen = False
        self._add_material_btns = []

        self.main_layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        btn_layout = QHBoxLayout()
        self.add_comp_btn = QPushButton("+ Add Component Section")
        self.add_comp_btn.clicked.connect(self.add_new_component)
        btn_layout.addWidget(self.add_comp_btn)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)

    def on_refresh(self):
        try:
            if not self.controller or not getattr(self.controller, "engine", None):
                return

            data = self.controller.engine.fetch_chunk(self.chunk_name) or {}

            if not data and self.default_components:
                for comp in self.default_components:
                    data[comp] = []
                self.controller.engine.stage_update(
                    chunk_name=self.chunk_name, data=data
                )

            self.data = data
            self.refresh_ui()
        except Exception as e:
            import traceback

            print(f"[ERROR] on_refresh crashed: {e}")
            traceback.print_exc()

    def refresh_ui(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.sections = {}
        self._add_material_btns = []

        for comp_name, items in self.data.items():
            self.create_section(comp_name)
            table = self.sections.get(comp_name)
            if table:
                for original_index, item in enumerate(items):
                    if not item.get("state", {}).get("in_trash", False):
                        table.add_row(item, original_index)

        self.container_layout.addStretch()
        self.container.adjustSize()

    def create_section(self, name):
        group = QGroupBox(name)
        g_layout = QVBoxLayout(group)

        table = StructureTableWidget(self, name)
        self.sections[name] = table

        add_row_btn = QPushButton(f"Add Material to {name}")
        add_row_btn.clicked.connect(lambda checked=False, n=name: self.open_dialog(n))
        add_row_btn.setEnabled(not self._frozen)
        self._add_material_btns.append(add_row_btn)

        g_layout.addWidget(table)
        g_layout.addWidget(add_row_btn)
        self.container_layout.addWidget(group)

    def add_material(self, comp_name, values_dict, is_trash=False):
        now = datetime.datetime.now().isoformat()

        included_carbon = values_dict.pop("_included_in_carbon_emission", True)
        included_recycling = values_dict.pop("_included_in_recyclability", True)
        is_modified_by_user = values_dict.pop("_is_modified_by_user", False)

        new_entry = {
            "id": str(uuid.uuid4()),
            "values": values_dict,
            "meta": {
                "created_on": now,
                "modified_on": now,
                "is_user_defined": True,
                "is_from_db": False,
                "source_version": "1.0",
                "is_modified_by_user": is_modified_by_user,
            },
            "state": {
                "in_trash": is_trash,
                "included_in_carbon_emission": included_carbon,
                "included_in_recyclability": included_recycling,
            },
        }

        current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        if comp_name not in current_data:
            current_data[comp_name] = []

        current_data[comp_name].append(new_entry)
        self.controller.engine.stage_update(
            chunk_name=self.chunk_name, data=current_data
        )
        self.save_current_state()
        self.on_refresh()

    def _get_project_country(self) -> str:
        try:
            return self.controller.get_chunk("general_info").get("project_country", "") or ""
        except Exception:
            return ""

    def open_dialog(self, comp_name):
        dialog = MaterialDialog(comp_name, self, country=self._get_project_country())
        if dialog.exec():
            self.add_material(comp_name, dialog.get_values())

    def open_edit_dialog(self, comp_name, table_row_index):
        try:
            current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
            items = current_data.get(comp_name, [])

            active_indices = [
                i
                for i, item in enumerate(items)
                if not item.get("state", {}).get("in_trash", False)
            ]

            if table_row_index < len(active_indices):
                original_idx = active_indices[table_row_index]
                item_to_edit = items[original_idx]

                dialog = MaterialDialog(comp_name, self, data=item_to_edit,
                                        country=self._get_project_country())
                if dialog.exec():
                    new_values = dialog.get_values()

                    included_carbon = new_values.pop("_included_in_carbon_emission", True)
                    included_recycling = new_values.pop("_included_in_recyclability", True)
                    new_is_modified = new_values.pop("_is_modified_by_user", False)

                    item_to_edit["values"] = new_values
                    item_to_edit["meta"]["modified_on"] = datetime.datetime.now().isoformat()
                    item_to_edit["meta"]["is_modified_by_user"] = (
                        item_to_edit["meta"].get("is_modified_by_user", False)
                        or new_is_modified
                    )
                    item_to_edit["state"]["included_in_carbon_emission"] = included_carbon
                    item_to_edit["state"]["included_in_recyclability"] = included_recycling

                    self.controller.engine.stage_update(
                        chunk_name=self.chunk_name, data=current_data
                    )
                    self.save_current_state()
                    QTimer.singleShot(0, self.on_refresh)
        except Exception as e:
            import traceback

            print(f"[ERROR] open_edit_dialog crashed: {e}")
            traceback.print_exc()

    def toggle_trash_status(self, comp_name, data_index, should_trash):
        data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
        if comp_name in data and len(data[comp_name]) > data_index:
            if "state" not in data[comp_name][data_index]:
                data[comp_name][data_index]["state"] = {}
            data[comp_name][data_index]["state"]["in_trash"] = should_trash

            self.controller.engine.stage_update(chunk_name=self.chunk_name, data=data)
            self.save_current_state()
            self.on_refresh()

            main_view = self.window().findChild(QWidget, "StructureTabView")
            if main_view and hasattr(main_view, "on_refresh"):
                main_view.on_refresh()

    def add_new_component(self):
        name, ok = QInputDialog.getText(self, "New Component", "Enter Component Name:")
        if ok and name.strip():
            clean_name = name.strip()
            self.create_section(clean_name)
            current_data = self.controller.engine.fetch_chunk(self.chunk_name) or {}
            if clean_name not in current_data:
                current_data[clean_name] = []
                self.controller.engine.stage_update(
                    chunk_name=self.chunk_name, data=current_data
                )
                self.save_current_state()

    def freeze(self, frozen: bool = True):
        self._frozen = frozen
        self.add_comp_btn.setEnabled(not frozen)
        for btn in self._add_material_btns:
            btn.setEnabled(not frozen)
        for table in self.sections.values():
            table.freeze(frozen)

    def save_current_state(self):
        if self.controller and self.controller.engine:
            eng = self.controller.engine
            eng._last_keystroke_time = time.time()
            eng._has_unsaved_changes = True
            try:
                eng.on_dirty(True)
            except Exception:
                pass
