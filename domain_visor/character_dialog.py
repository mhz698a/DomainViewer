# domain_visor/character_dialog.py

import os
import json
import traceback
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFileDialog, QScrollArea, QWidget,
    QListWidget, QListWidgetItem, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from domain_visor.theme import Theme
from domain_visor.type_underwear_editor import load_global_type_underwear, TypeUnderwearEditorDialog

class CharacterEditDialog(QDialog):
    """
    Diálogo modal para editar los datos de un personaje en su archivo JSON.
    """
    def __init__(self, char_data, parent=None):
        super().__init__(parent)
        self.char_data = char_data.copy()  # Trabajar con una copia
        self.original_char_data = char_data
        self.saved = False

        self.setWindowTitle("Modificar Personaje")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.resize(650, 600)

        # Quitar botón de ayuda
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Aplicar estilos acordes con Theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.APP_BACKGROUND};
                color: {Theme.TEXT_WHITE};
            }}
            QWidget {{
                background-color: {Theme.APP_BACKGROUND};
                color: {Theme.TEXT_WHITE};
                font-family: Arial;
                font-size: 11px;
            }}
            QLabel {{
                color: {Theme.TEXT_WHITE};
                font-weight: bold;
            }}
            QLineEdit, QDateEdit {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                color: {Theme.TEXT_WHITE};
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border-color: #85c1e9;
            }}
            QLineEdit[readOnly="true"] {{
                background-color: #1e1e1e;
                color: #888888;
                border-color: #333333;
            }}
            QComboBox {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                color: {Theme.TEXT_WHITE};
            }}
            QComboBox:focus {{
                border-color: #85c1e9;
            }}
            QPushButton {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                color: {Theme.TEXT_WHITE};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3e3e42;
                border-color: #85c1e9;
            }}
            QPushButton:pressed {{
                background-color: #1e1e1e;
            }}
        """)

        # La ubicación de la credencial determina la carpeta del personaje.
        json_path_str = self.char_data.get("character_json_path", "")
        if json_path_str:
            self.initial_character_json_path = Path(json_path_str)
        else:
            # Compatibilidad con JSON/cachés anteriores que aún contienen character_path.
            legacy_dir = Path(self.char_data.get("character_path", ""))
            expected_json = legacy_dir / f"__{self.char_data.get('name', '')}__.json"
            if expected_json.is_file():
                self.initial_character_json_path = expected_json
            else:
                legacy_jsons = sorted(legacy_dir.glob("__*.json")) if legacy_dir.is_dir() else []
                self.initial_character_json_path = legacy_jsons[0] if legacy_jsons else expected_json

        self.initial_character_path = self.initial_character_json_path.parent
        self.parent_dir = self.initial_character_path.parent
        self.current_character_path = self.initial_character_path
        self.album_prefix = f"{max(0, self.char_data.get('year', 2004) - 2003):02d}"

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Scroll area para los campos por si la ventana se hace pequeña
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(10)

        # 1. Year (Readonly)
        scroll_layout.addWidget(QLabel("Año (Year):"), 0, 0)
        self.txt_year = QLineEdit(str(self.char_data.get("year", "")))
        self.txt_year.setReadOnly(True)
        scroll_layout.addWidget(self.txt_year, 0, 1, 1, 2)

        # 2. Position
        scroll_layout.addWidget(QLabel("Posición (Position):"), 1, 0)
        self.txt_position = QLineEdit(str(self.char_data.get("position", "")))
        scroll_layout.addWidget(self.txt_position, 1, 1, 1, 2)

        # 3. Name
        scroll_layout.addWidget(QLabel("Nombre (Name):"), 2, 0)
        self.txt_name = QLineEdit(self.char_data.get("name", ""))
        scroll_layout.addWidget(self.txt_name, 2, 1, 1, 2)

        # 4. Alterego
        scroll_layout.addWidget(QLabel("Alterego:"), 3, 0)
        self.txt_alterego = QLineEdit(self.char_data.get("alterego", ""))
        scroll_layout.addWidget(self.txt_alterego, 3, 1, 1, 2)

        # 5. Birthday (QDateEdit with Calendar Popup)
        scroll_layout.addWidget(QLabel("Cumpleaños (Birthday):"), 4, 0)
        self.txt_birthday = QDateEdit()
        self.txt_birthday.setCalendarPopup(True)
        self.txt_birthday.setDisplayFormat("yyyy-MM-dd")

        bday_str = self.char_data.get("birthday", "")
        bday_date = QDate.fromString(bday_str, "yyyy-MM-dd")
        if bday_date.isValid():
            self.txt_birthday.setDate(bday_date)
        else:
            self.txt_birthday.setDate(QDate.currentDate())
        scroll_layout.addWidget(self.txt_birthday, 4, 1, 1, 2)

        # 6. Age
        scroll_layout.addWidget(QLabel("Edad (Age):"), 5, 0)
        self.txt_age = QLineEdit(str(self.char_data.get("age", "")))
        scroll_layout.addWidget(self.txt_age, 5, 1, 1, 2)

        # 7. Icon Path (QLineEdit + Establecer + Abrir)
        scroll_layout.addWidget(QLabel("Ruta Icono (Icon Path):"), 6, 0)
        self.txt_icon_path = QLineEdit(self.char_data.get("icon_path", ""))
        scroll_layout.addWidget(self.txt_icon_path, 6, 1)

        btn_icon_layout = QHBoxLayout()
        self.btn_set_icon = QPushButton("Establecer")
        self.btn_set_icon.clicked.connect(self.set_icon_file)
        self.btn_open_icon = QPushButton("Abrir")
        self.btn_open_icon.clicked.connect(self.open_icon_file)
        btn_icon_layout.addWidget(self.btn_set_icon)
        btn_icon_layout.addWidget(self.btn_open_icon)
        scroll_layout.addLayout(btn_icon_layout, 6, 2)

        # 8. Background Path (QLineEdit + Establecer + Abrir)
        scroll_layout.addWidget(QLabel("Ruta Fondo (Background Path):"), 7, 0)
        self.txt_bg_path = QLineEdit(self.char_data.get("background_path", ""))
        scroll_layout.addWidget(self.txt_bg_path, 7, 1)

        btn_bg_layout = QHBoxLayout()
        self.btn_set_bg = QPushButton("Establecer")
        self.btn_set_bg.clicked.connect(self.set_bg_file)
        self.btn_open_bg = QPushButton("Abrir")
        self.btn_open_bg.clicked.connect(self.open_bg_file)
        btn_bg_layout.addWidget(self.btn_set_bg)
        btn_bg_layout.addWidget(self.btn_open_bg)
        scroll_layout.addLayout(btn_bg_layout, 7, 2)

        # 9. Type Underwear (QListWidget with checkboxes & Editar lista button)
        scroll_layout.addWidget(QLabel("Ropa Interior (Type Underwear):"), 8, 0)

        underwear_container = QWidget()
        underwear_layout = QVBoxLayout(underwear_container)
        underwear_layout.setContentsMargins(0, 0, 0, 0)
        underwear_layout.setSpacing(5)

        self.list_underwear = QListWidget()
        self.list_underwear.setMaximumHeight(120)
        self.list_underwear.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 4px;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #2d2d2d;
                color: #ffffff;
            }
        """)

        self.btn_edit_underwear_list = QPushButton("Editar lista")
        self.btn_edit_underwear_list.clicked.connect(self.open_underwear_list_editor)

        underwear_layout.addWidget(self.list_underwear)
        underwear_layout.addWidget(self.btn_edit_underwear_list, 0, Qt.AlignmentFlag.AlignLeft)

        scroll_layout.addWidget(underwear_container, 8, 1, 1, 2)

        # Parse current_underwear backward-compatibly
        current_underwear = self.char_data.get("type_underwear", [])
        if isinstance(current_underwear, str):
            self.selected_underwear = [current_underwear] if current_underwear else []
        elif isinstance(current_underwear, list):
            self.selected_underwear = list(current_underwear)
        else:
            self.selected_underwear = []

        self.populate_underwear_list()
        self.list_underwear.itemChanged.connect(self.on_underwear_item_changed)

        # 10. Short Masked Alterego
        scroll_layout.addWidget(QLabel("Short Masked Alterego:"), 9, 0)
        self.txt_short_masked = QLineEdit(self.char_data.get("short_masked_alterego", ""))
        scroll_layout.addWidget(self.txt_short_masked, 9, 1, 1, 2)

        # La ruta de la carpeta se deriva internamente de character_json_path y no se muestra.

        # 12. Color Group (Combobox)
        scroll_layout.addWidget(QLabel("Grupo Color (Color Group):"), 10, 0)
        self.cb_color_group = QComboBox()
        color_options = [
            "", "rojo", "azul", "verde", "amarillo", "naranja", "morado",
            "rosa", "blanco", "negro", "gris", "marrón", "turquesa", "cian",
            "magenta", "arcoiris"
        ]
        self.cb_color_group.addItems(color_options)
        current_color = self.char_data.get("color_group", "")
        if current_color in color_options:
            self.cb_color_group.setCurrentText(current_color)
        else:
            self.cb_color_group.setCurrentIndex(0)
        scroll_layout.addWidget(self.cb_color_group, 10, 1, 1, 2)

        # 13. Profession Group
        scroll_layout.addWidget(QLabel("Grupo Profesión (Profession):"), 11, 0)
        self.txt_profession = QLineEdit(self.char_data.get("profession_group", ""))
        scroll_layout.addWidget(self.txt_profession, 11, 1, 1, 2)

        # 14. Time of Year (Combobox)
        scroll_layout.addWidget(QLabel("Tiempo de Año (Time of Year):"), 12, 0)
        self.cb_time_of_year = QComboBox()
        time_options = ["", "invierno", "primavera", "verano", "otoño"]
        self.cb_time_of_year.addItems(time_options)
        current_time = self.char_data.get("time_of_year", "")
        if current_time in time_options:
            self.cb_time_of_year.setCurrentText(current_time)
        else:
            self.cb_time_of_year.setCurrentIndex(0)
        scroll_layout.addWidget(self.cb_time_of_year, 12, 1, 1, 2)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Forzar reemplazo inicial de espacios si los hubiera antes de conectar señales
        self._replace_spaces_real_time(self.txt_name)
        self._replace_spaces_real_time(self.txt_alterego)

        # Conectar señales en tiempo real para reemplazar espacios por guiones bajos
        self.txt_name.textChanged.connect(lambda: self._replace_spaces_real_time(self.txt_name))
        self.txt_alterego.textChanged.connect(lambda: self._replace_spaces_real_time(self.txt_alterego))

        # Conectar señales para actualización automática de ruta
        self.txt_position.textChanged.connect(self._update_character_path)
        self.txt_name.textChanged.connect(self._update_character_path)
        self.txt_alterego.textChanged.connect(self._update_character_path)
        self.txt_birthday.dateChanged.connect(self._update_character_path)
        self.txt_age.textChanged.connect(self._update_character_path)

        # Forzar cálculo inicial de ruta si es posible
        self._update_character_path()

        # Footer Buttons
        footer_layout = QHBoxLayout()

        self.btn_open_credential_location = QPushButton("Abrir ubicacion de credencial")
        self.btn_open_credential_location.clicked.connect(self.open_credential_location)
        footer_layout.addWidget(self.btn_open_credential_location)

        footer_layout.addStretch()

        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_discard = QPushButton("Descartar")
        self.btn_discard.clicked.connect(self.reject)

        footer_layout.addWidget(self.btn_save)
        footer_layout.addWidget(self.btn_discard)
        main_layout.addLayout(footer_layout)

    def populate_underwear_list(self):
        self.list_underwear.blockSignals(True)
        self.list_underwear.clear()

        global_options = load_global_type_underwear()

        # 1. Agregar elementos de la lista global
        for option in global_options:
            item = QListWidgetItem(option)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if option in self.selected_underwear:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, False)  # No es descontinuado
            item.setData(Qt.ItemDataRole.UserRole + 1, option)  # Nombre real
            self.list_underwear.addItem(item)

        # 2. Agregar elementos del personaje que fueron descontinuados (ya no están en la lista global)
        for option in self.selected_underwear:
            if option not in global_options:
                disp_text = f"{option} (Descontinuado)"
                item = QListWidgetItem(disp_text)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, True)  # Es descontinuado
                item.setData(Qt.ItemDataRole.UserRole + 1, option)  # Nombre real
                self.list_underwear.addItem(item)

        self.list_underwear.blockSignals(False)

    def open_underwear_list_editor(self):
        # Actualizar self.selected_underwear con las selecciones actuales
        self._update_currently_selected_underwear()
        dlg = TypeUnderwearEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.populate_underwear_list()

    def _update_currently_selected_underwear(self):
        selected = []
        for i in range(self.list_underwear.count()):
            item = self.list_underwear.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                real_name = item.data(Qt.ItemDataRole.UserRole + 1)
                if real_name:
                    selected.append(real_name)
        self.selected_underwear = selected

    def on_underwear_item_changed(self, item):
        is_discontinued = item.data(Qt.ItemDataRole.UserRole)
        if is_discontinued and item.checkState() == Qt.CheckState.Unchecked:
            real_name = item.data(Qt.ItemDataRole.UserRole + 1)
            reply = QMessageBox.question(
                self,
                "Elemento descontinuado",
                f"El elemento '{real_name}' fue descontinuado. Si continúa, se eliminará del personaje.\n¿Desea eliminarlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Se elimina del personaje
                self.list_underwear.blockSignals(True)
                row = self.list_underwear.row(item)
                self.list_underwear.takeItem(row)
                self.list_underwear.blockSignals(False)
            else:
                # Se conserva el valor
                self.list_underwear.blockSignals(True)
                item.setCheckState(Qt.CheckState.Checked)
                self.list_underwear.blockSignals(False)

        self._update_currently_selected_underwear()

    def _replace_spaces_real_time(self, line_edit):
        text = line_edit.text()
        if " " in text:
            cursor_pos = line_edit.cursorPosition()
            new_text = text.replace(" ", "_")
            line_edit.blockSignals(True)
            line_edit.setText(new_text)
            line_edit.setCursorPosition(cursor_pos)
            line_edit.blockSignals(False)

    def _update_character_path(self):
        # 1. Obtener valores actuales o usar fallbacks seguros si están vacíos
        pos_raw = self.txt_position.text().strip()
        try:
            pos_val = int(pos_raw)
            pos_str = f"{pos_val:02d}"
        except ValueError:
            pos_str = pos_raw if pos_raw else "00"

        name_str = self.txt_name.text().strip()
        alterego_str = self.txt_alterego.text().strip()
        birthday_str = self.txt_birthday.date().toString("yyyy-MM-dd")

        age_raw = self.txt_age.text().strip()
        try:
            age_val = int(age_raw)
            age_str = f"{age_val:02d}"
        except ValueError:
            age_str = age_raw if age_raw else "00"

        # Formato de carpeta: {album_prefix}. {position_padded};{alterego};{name};{birthday};{age_padded}
        folder_name = f"{self.album_prefix}. {pos_str};{alterego_str};{name_str};{birthday_str};{age_str}"
        new_path = self.parent_dir / folder_name

        self.current_character_path = new_path.resolve()

    # Métodos de ayuda para los selectores y apertura de archivos

    def get_start_directory(self) -> str:
        for char_path in (Path(self.current_character_path), self.initial_character_path):
            if char_path.is_dir():
                return str(char_path)
        return str(Path.cwd())

    def set_icon_file(self):
        start_dir = self.get_start_directory()
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Elegir Icono", start_dir,
            "Imágenes (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;Todos los archivos (*)"
        )
        if filepath:
            selected_path = Path(filepath).resolve()
            relative_path = None
            for char_path in (self.initial_character_path, Path(self.current_character_path)):
                try:
                    relative_path = selected_path.relative_to(char_path.resolve())
                    break
                except ValueError:
                    continue

            if relative_path is not None:
                self.txt_icon_path.setText(relative_path.as_posix())
            else:
                # Los recursos externos se guardan como rutas absolutas.
                self.txt_icon_path.setText(str(selected_path))

    def _open_file_cross_platform(self, path):
        import sys
        import subprocess
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir:\n{e}")

    def open_credential_location(self):
        """Abre la carpeta que contiene el JSON del personaje detectado."""
        credential_dir = self.initial_character_json_path.parent
        if credential_dir.is_dir():
            self._open_file_cross_platform(str(credential_dir.resolve()))
        else:
            QMessageBox.warning(
                self,
                "Advertencia",
                f"No se encontró la ubicación de la credencial:\n{credential_dir}"
            )

    def _resolve_asset_path(self, raw_path):
        asset_path = Path(raw_path).expanduser()
        if asset_path.is_absolute():
            return asset_path

        current_candidate = Path(self.current_character_path) / asset_path
        if current_candidate.exists():
            return current_candidate

        # Antes de guardar, los recursos relativos siguen físicamente en la
        # carpeta original, incluso cuando el nombre nuevo aún no existe.
        return self.initial_character_path / asset_path

    def open_icon_file(self):
        icon_path = self.txt_icon_path.text().strip()
        full_path = self._resolve_asset_path(icon_path) if icon_path else Path()
        if full_path.is_file():
            self._open_file_cross_platform(str(full_path.resolve()))
        else:
            QMessageBox.warning(self, "Advertencia", f"El archivo no existe:\n{full_path}")

    def set_bg_file(self):
        start_dir = self.get_start_directory()
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Elegir Fondo", start_dir,
            "Imágenes (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;Todos los archivos (*)"
        )
        if filepath:
            selected_path = Path(filepath).resolve()
            relative_path = None
            for char_path in (self.initial_character_path, Path(self.current_character_path)):
                try:
                    relative_path = selected_path.relative_to(char_path.resolve())
                    break
                except ValueError:
                    continue

            if relative_path is not None:
                self.txt_bg_path.setText(relative_path.as_posix())
            else:
                self.txt_bg_path.setText(str(selected_path))

    def open_bg_file(self):
        bg_path = self.txt_bg_path.text().strip()
        full_path = self._resolve_asset_path(bg_path) if bg_path else Path()
        if full_path.is_file():
            self._open_file_cross_platform(str(full_path.resolve()))
        else:
            QMessageBox.warning(self, "Advertencia", f"El archivo no existe:\n{full_path}")

    def open_char_dir(self):
        char_path = Path(self.current_character_path)
        if char_path.is_dir():
            self._open_file_cross_platform(str(char_path.resolve()))
        else:
            QMessageBox.warning(self, "Advertencia", "La carpeta de personaje no existe o está vacía.")

    def save_data(self):
        try:
            # 1. Validar posición y edad que sean enteros válidos
            try:
                position = int(self.txt_position.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Validación", "La posición debe ser un número entero válido.")
                return

            try:
                age = int(self.txt_age.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Validación", "La edad debe ser un número entero válido.")
                return

            # 2. Recolectar datos editados
            new_name = self.txt_name.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Validación", "El campo Nombre (Name) es obligatorio.")
                return

            original_name = self.original_char_data.get("name", "")
            original_json_path_str = self.original_char_data.get("character_json_path", "")
            original_json_file = (
                Path(original_json_path_str)
                if original_json_path_str
                else self.initial_character_json_path
            )
            original_char_path = original_json_file.parent

            # Recolectar ropa interior seleccionada
            self._update_currently_selected_underwear()
            selected_underwear = self.selected_underwear

            # La nueva ruta de la carpeta que calculamos automáticamente
            new_char_path = Path(self.current_character_path)

            # Preparar la nueva estructura character_data (usará el new_char_path ya resuelto)
            updated_data = {
                "year": int(self.txt_year.text().strip()),
                "position": position,
                "name": new_name,
                "alterego": self.txt_alterego.text().strip(),
                "birthday": self.txt_birthday.date().toString("yyyy-MM-dd"),
                "age": age,
                "icon_path": self.txt_icon_path.text().strip(),
                "background_path": self.txt_bg_path.text().strip(),
                "type_underwear": selected_underwear,
                "short_masked_alterego": self.txt_short_masked.text().strip(),
                # Se calcula con la carpeta destino y el nombre del JSON que se guardará.
                "character_json_path": str((new_char_path / f"__{new_name}__.json").resolve()),
                "color_group": self.cb_color_group.currentText(),
                "profession_group": self.txt_profession.text().strip(),
                "time_of_year": self.cb_time_of_year.currentText()
            }

            # Validar la ubicación real del JSON detectado antes de guardar.
            if not original_char_path.is_dir() or not original_json_file.is_file():
                QMessageBox.warning(
                    self,
                    "Validación",
                    f"No se encontró la credencial original:\n{original_json_file}"
                )
                return

            # Comprobar conflictos antes de escribir o renombrar.
            moving_folder = original_char_path.resolve() != new_char_path.resolve()
            if moving_folder and new_char_path.exists():
                QMessageBox.warning(self, "Validación", f"La carpeta destino ya existe:\n{new_char_path}")
                return

            old_json_file = original_json_file
            new_json_file = original_char_path / f"__{new_name}__.json"
            if new_json_file.exists() and new_json_file.resolve() != old_json_file.resolve():
                QMessageBox.warning(self, "Validación", f"La credencial destino ya existe:\n{new_json_file}")
                return

            # Escribir primero el JSON nuevo dentro de la carpeta actual.
            with open(new_json_file, "w", encoding="utf-8") as jf:
                json.dump({"character_data": updated_data}, jf, indent=4, ensure_ascii=False)

            final_character_dir = original_char_path
            if moving_folder:
                try:
                    original_char_path.rename(new_char_path)
                    final_character_dir = new_char_path
                except Exception as ex:
                    if new_json_file.exists() and new_json_file.resolve() != old_json_file.resolve():
                        try:
                            new_json_file.unlink()
                        except OSError:
                            pass
                    QMessageBox.critical(
                        self,
                        "Error al Guardar",
                        f"No se pudo renombrar la carpeta del personaje:\n{ex}"
                    )
                    return

            # Eliminar el archivo anterior usando su ubicación después del eventual rename.
            final_old_json = final_character_dir / old_json_file.name
            final_new_json = final_character_dir / new_json_file.name
            if final_old_json.exists() and final_old_json.resolve() != final_new_json.resolve():
                try:
                    final_old_json.unlink()
                except OSError as ex:
                    print(f"Advertencia eliminando JSON anterior: {ex}")

            # Guardar el resultado en self.char_data para devolverlo
            self.char_data = updated_data
            self.saved = True
            self.accept()

        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error al Guardar", f"Ocurrió un error guardando el personaje:\n{e}\n\nDetalles:\n{tb}")
