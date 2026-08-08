# domain_visor/character_dialog.py

import os
import json
import traceback
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFileDialog, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from domain_visor.theme import Theme

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
        self.resize(650, 550)

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
            QLineEdit {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                color: {Theme.TEXT_WHITE};
            }}
            QLineEdit:focus {{
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

        # 5. Birthday
        scroll_layout.addWidget(QLabel("Cumpleaños (Birthday):"), 4, 0)
        self.txt_birthday = QLineEdit(self.char_data.get("birthday", ""))
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

        # 9. Type Underwear (Combobox)
        scroll_layout.addWidget(QLabel("Ropa Interior (Type Underwear):"), 8, 0)
        self.cb_underwear = QComboBox()
        underwear_options = [
            "", "Boybrief", "Girlbrief Clasic Mid Low rise", "boyshort boxer",
            "Thong", "Bikini", "Hipster", "Tanga Brief", "French Cut",
            "Brief Slip", "Brief Mid high rise", "Pantaloons"
        ]
        self.cb_underwear.addItems(underwear_options)
        current_underwear = self.char_data.get("type_underwear", "")
        if current_underwear in underwear_options:
            self.cb_underwear.setCurrentText(current_underwear)
        else:
            self.cb_underwear.setCurrentIndex(0)
        scroll_layout.addWidget(self.cb_underwear, 8, 1, 1, 2)

        # 10. Short Masked Alterego
        scroll_layout.addWidget(QLabel("Short Masked Alterego:"), 9, 0)
        self.txt_short_masked = QLineEdit(self.char_data.get("short_masked_alterego", ""))
        scroll_layout.addWidget(self.txt_short_masked, 9, 1, 1, 2)

        # 11. Character Path (QLineEdit + Elegir + Abrir)
        scroll_layout.addWidget(QLabel("Ruta Personaje (Char Path):"), 10, 0)
        self.txt_char_path = QLineEdit(self.char_data.get("character_path", ""))
        scroll_layout.addWidget(self.txt_char_path, 10, 1)

        btn_char_layout = QHBoxLayout()
        self.btn_choose_char = QPushButton("Elegir")
        self.btn_choose_char.clicked.connect(self.choose_char_dir)
        self.btn_open_char = QPushButton("Abrir")
        self.btn_open_char.clicked.connect(self.open_char_dir)
        btn_char_layout.addWidget(self.btn_choose_char)
        btn_char_layout.addWidget(self.btn_open_char)
        scroll_layout.addLayout(btn_char_layout, 10, 2)

        # 12. Color Group (Combobox)
        scroll_layout.addWidget(QLabel("Grupo Color (Color Group):"), 11, 0)
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
        scroll_layout.addWidget(self.cb_color_group, 11, 1, 1, 2)

        # 13. Profession Group
        scroll_layout.addWidget(QLabel("Grupo Profesión (Profession):"), 12, 0)
        self.txt_profession = QLineEdit(self.char_data.get("profession_group", ""))
        scroll_layout.addWidget(self.txt_profession, 12, 1, 1, 2)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_discard = QPushButton("Descartar")
        self.btn_discard.clicked.connect(self.reject)

        footer_layout.addWidget(self.btn_save)
        footer_layout.addWidget(self.btn_discard)
        main_layout.addLayout(footer_layout)

    # Métodos de ayuda para los selectores y apertura de archivos

    def get_start_directory(self) -> str:
        char_path = self.txt_char_path.text().strip()
        if char_path and Path(char_path).exists():
            return char_path
        return str(Path.cwd())

    def set_icon_file(self):
        start_dir = self.get_start_directory()
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Elegir Icono", start_dir,
            "Imágenes (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;Todos los archivos (*)"
        )
        if filepath:
            # Intentar convertir la ruta a relativa del directorio de personaje
            char_path = self.txt_char_path.text().strip()
            if char_path:
                try:
                    rel_path = Path(filepath).relative_to(Path(char_path))
                    self.txt_icon_path.setText(rel_path.as_posix())
                except ValueError:
                    self.txt_icon_path.setText(Path(filepath).name)
            else:
                self.txt_icon_path.setText(Path(filepath).name)

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

    def open_icon_file(self):
        icon_path = self.txt_icon_path.text().strip()
        char_path = self.txt_char_path.text().strip()
        full_path = Path(char_path) / icon_path if char_path and icon_path else Path(icon_path)
        if full_path.exists():
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
            char_path = self.txt_char_path.text().strip()
            if char_path:
                try:
                    rel_path = Path(filepath).relative_to(Path(char_path))
                    self.txt_bg_path.setText(rel_path.as_posix())
                except ValueError:
                    self.txt_bg_path.setText(Path(filepath).name)
            else:
                self.txt_bg_path.setText(Path(filepath).name)

    def open_bg_file(self):
        bg_path = self.txt_bg_path.text().strip()
        char_path = self.txt_char_path.text().strip()
        full_path = Path(char_path) / bg_path if char_path and bg_path else Path(bg_path)
        if full_path.exists():
            self._open_file_cross_platform(str(full_path.resolve()))
        else:
            QMessageBox.warning(self, "Advertencia", f"El archivo no existe:\n{full_path}")

    def choose_char_dir(self):
        start_dir = self.get_start_directory()
        directory = QFileDialog.getExistingDirectory(self, "Elegir Carpeta de Personaje", start_dir)
        if directory:
            self.txt_char_path.setText(str(Path(directory).resolve()))

    def open_char_dir(self):
        char_path = self.txt_char_path.text().strip()
        if char_path and Path(char_path).exists():
            self._open_file_cross_platform(str(Path(char_path).resolve()))
        else:
            QMessageBox.warning(self, "Advertencia", f"La carpeta de personaje no existe u está vacía.")

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
            original_char_path = self.original_char_data.get("character_path", "")

            # Preparar la nueva estructura character_data
            updated_data = {
                "year": int(self.txt_year.text().strip()),
                "position": position,
                "name": new_name,
                "alterego": self.txt_alterego.text().strip(),
                "birthday": self.txt_birthday.text().strip(),
                "age": age,
                "icon_path": self.txt_icon_path.text().strip(),
                "background_path": self.txt_bg_path.text().strip(),
                "type_underwear": self.cb_underwear.currentText(),
                "short_masked_alterego": self.txt_short_masked.text().strip(),
                "character_path": self.txt_char_path.text().strip(),
                "color_group": self.cb_color_group.currentText(),
                "profession_group": self.txt_profession.text().strip()
            }

            # 3. Guardar archivo físico JSON del personaje
            char_path = Path(updated_data["character_path"])
            if not char_path.exists():
                QMessageBox.warning(self, "Validación", f"La ruta de personaje especificada no existe:\n{char_path}")
                return

            # Nombres de JSON viejo y nuevo
            old_json_file = char_path / f"__{original_name}__.json"
            new_json_file = char_path / f"__{new_name}__.json"

            # Si el nombre cambió, y el archivo JSON viejo existe, lo borraremos después o renombraremos
            # Escribir el nuevo JSON
            with open(new_json_file, "w", encoding="utf-8") as jf:
                json.dump({"character_data": updated_data}, jf, indent=4, ensure_ascii=False)

            # Si el nombre cambió y existía un archivo viejo con el nombre antiguo, lo removemos
            if original_name != new_name and old_json_file.exists() and old_json_file != new_json_file:
                try:
                    old_json_file.unlink()
                except Exception as ex:
                    print(f"Advertencia eliminando archivo JSON anterior: {ex}")

            # Guardar el resultado en self.char_data para devolverlo
            self.char_data = updated_data
            self.saved = True
            self.accept()

        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error al Guardar", f"Ocurrió un error guardando el personaje:\n{e}\n\nDetalles:\n{tb}")
