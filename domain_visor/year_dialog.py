# domain_visor/year_dialog.py

import os
import json
import traceback
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidget, QListWidgetItem, QWidget,
    QTreeView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDir, QModelIndex, QUrl
from PyQt6.QtGui import QFileSystemModel, QDesktopServices
from domain_visor.theme import Theme
from domain_visor.character_manager import CharacterManager

def calculate_id_package_default(year: int, infra_path: Path = None) -> str:
    """
    Calcula el ID de paquete por defecto basado en las reglas:
    - Primeros dos caracteres del último nombre del superdominio en mayúsculas.
    - "-"
    - Número del dominio dentro del superdominio en dos dígitos.
    - "-"
    - prefix en dos dígitos: {max(0, year - 2003):02d}
    - "-"
    - "00A" al ser default variant key (se pone por defecto)
    """
    if infra_path is None:
        infra_path = Path("__structure__/infrastructure.json")
    if not infra_path.exists():
        return ""
    try:
        with open(infra_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return ""

    for sd_data in data:
        sd_name = sd_data.get("superdomain", "").strip()
        for idx, domain_data in enumerate(sd_data.get("domains", [])):
            range_text = domain_data.get("range", "")
            try:
                start_year, end_year = map(int, range_text.split("-"))
            except Exception:
                continue
            if start_year <= year <= end_year:
                # 1. Prefijo del superdominio: primeros dos caracteres del último nombre
                parts = [p for p in sd_name.split("_") if p]
                last_part = parts[-1] if parts else ""
                sd_prefix = last_part[:2].upper()

                # 2. Número del dominio dentro del superdominio (1-based index) en dos dígitos
                domain_index = idx + 1
                dom_index_str = f"{domain_index:02d}"

                # 3. Prefix en dos dígitos
                prefix_str = f"{max(0, year - 2003):02d}"

                # 4. Combinar con default variant key "00A"
                return f"{sd_prefix}-{dom_index_str}-{prefix_str}-00A"
    return ""


def find_season_name(year: int, base_path: Path) -> str:
    """
    Busca dentro del año una carpeta que contenga "___".
    Remueve "___[" y "]" si están presentes para que no salgan visualmente en season_name.
    """
    year_dir = base_path / str(year)
    if not year_dir.exists():
        return ""
    try:
        for item in year_dir.iterdir():
            if item.is_dir() and "___" in item.name:
                name = item.name
                # Limpieza de "___[" y "]" para season_name
                name = name.replace("___[", "").replace("]", "")
                return name
    except Exception:
        pass
    return ""


class YearDialog(QDialog):
    """
    Diálogo de Año ("Year Dialog") para visualizar y editar la estructura de identidad del año.
    """
    def __init__(self, year_value: int, parent=None, base_path=None):
        super().__init__(parent)
        self.year_value = year_value
        self.saved = False

        # Configurar gestor de personajes para obtener la ruta base
        self.char_manager = CharacterManager()
        self.base_path = Path(base_path) if base_path else self.char_manager.base_path

        self.setWindowTitle(f"Year Dialog - {self.year_value}")
        self.setModal(True)
        self.setMinimumWidth(760)
        self.resize(900, 500)

        # Quitar botón de ayuda
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Aplicar estilos oscuros del Theme
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
                padding: 5px;
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
            QListWidget {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                color: #ffffff;
            }}
            QListWidget::item {{
                padding: 4px;
                color: #ffffff;
            }}
            QListWidget::item:hover {{
                background-color: #3e3e42;
            }}
            QListWidget::item:selected {{
                background-color: #3e3e42;
                color: #ffffff;
            }}
        """)

        # Definir rutas del año y del archivo JSON
        self.prefix = f"{max(0, self.year_value - 2003):02d}"
        self.year_dir = self.base_path / str(self.year_value)
        self.identity_dir = self.year_dir / f"{self.prefix}. identity"
        self.json_filename = f"The_ID_Year_{self.year_value}.json"
        self.json_filepath = self.identity_dir / self.json_filename

        # Intentar obtener infra_path del parent si existe
        self.infra_path = None
        if parent and hasattr(parent, "json_path"):
            self.infra_path = Path(parent.json_path)

        # Cargar o inicializar estructura de datos
        self.load_or_create_year_data(self.infra_path)
        self.init_ui()

    def load_or_create_year_data(self, infra_path=None):
        """
        Carga o crea el archivo JSON. Sincroniza campos de sólo lectura.
        """
        # Calcular los campos generados automáticamente
        self.auto_season_name = find_season_name(self.year_value, self.base_path)
        self.auto_id_package_default = calculate_id_package_default(self.year_value, infra_path)

        exists = self.json_filepath.exists()
        loaded_data = {}

        if exists:
            try:
                with open(self.json_filepath, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
            except Exception as e:
                print(f"Error cargando archivo {self.json_filepath}: {e}")

        # Estructura interna
        inner_data = loaded_data.get("year_data", {})

        # Crear o actualizar estructura combinando datos cargados y valores autocalculados
        stored_id = inner_data.get("id_package_default", "")
        final_id = self.auto_id_package_default if self.auto_id_package_default else stored_id

        self.year_data = {
            "year": str(self.year_value),
            "prefix": self.prefix,
            "season_name": self.auto_season_name,
            "season_abreviation": inner_data.get("season_abreviation", ""),
            "esentia_name": inner_data.get("esentia_name", ""),
            "id_package_default": final_id, # Generado automáticamente
            "other_id_package_default": inner_data.get("other_id_package_default", [])
        }

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(15)

        # Grid para campos (usando claves exactas como etiquetas y traduciendo Estación a Temporada)
        grid = QGridLayout()
        grid.setSpacing(10)

        # Row 0: year (Readonly)
        grid.addWidget(QLabel("year:"), 0, 0)
        self.txt_year = QLineEdit(self.year_data["year"])
        self.txt_year.setReadOnly(True)
        grid.addWidget(self.txt_year, 0, 1)

        # Row 1: prefix (Readonly)
        grid.addWidget(QLabel("prefix:"), 1, 0)
        self.txt_prefix = QLineEdit(self.year_data["prefix"])
        self.txt_prefix.setReadOnly(True)
        grid.addWidget(self.txt_prefix, 1, 1)

        # Row 2: season_name (Readonly)
        grid.addWidget(QLabel("season_name:"), 2, 0)
        self.txt_season_name = QLineEdit(self.year_data["season_name"])
        self.txt_season_name.setReadOnly(True)
        grid.addWidget(self.txt_season_name, 2, 1)

        # Row 3: id_package_default (Readonly)
        grid.addWidget(QLabel("id_package_default:"), 3, 0)
        self.txt_id_package_default = QLineEdit(self.year_data["id_package_default"])
        self.txt_id_package_default.setReadOnly(True)
        grid.addWidget(self.txt_id_package_default, 3, 1)

        # Row 4: season_abreviation (Editable)
        grid.addWidget(QLabel("season_abreviation (Abreviación Temporada):"), 4, 0)
        self.txt_season_abreviation = QLineEdit(self.year_data["season_abreviation"])
        grid.addWidget(self.txt_season_abreviation, 4, 1)

        # Row 5: esentia_name (Editable)
        grid.addWidget(QLabel("esentia_name:"), 5, 0)
        self.txt_esentia_name = QLineEdit(self.year_data["esentia_name"])
        grid.addWidget(self.txt_esentia_name, 5, 1)

        fields_layout.addLayout(grid)

        # Otros paquetes ID por defecto
        fields_layout.addWidget(QLabel("other_id_package_default:"))
        
        self.list_other_packages = QListWidget()
        for pkg in self.year_data["other_id_package_default"]:
            self.list_other_packages.addItem(QListWidgetItem(pkg))
        fields_layout.addWidget(self.list_other_packages)

        # Controles para añadir/eliminar paquetes
        add_del_layout = QHBoxLayout()
        self.txt_new_package = QLineEdit()
        self.txt_new_package.setPlaceholderText("Nuevo ID de paquete...")
        self.btn_add_package = QPushButton("Añadir")
        self.btn_add_package.clicked.connect(self.add_package_item)
        self.btn_del_package = QPushButton("Eliminar")
        self.btn_del_package.clicked.connect(self.del_package_item)

        add_del_layout.addWidget(self.txt_new_package)
        add_del_layout.addWidget(self.btn_add_package)
        add_del_layout.addWidget(self.btn_del_package)
        fields_layout.addLayout(add_del_layout)

        content_layout.addLayout(fields_layout, 2)
        content_layout.addWidget(self._create_year_folder_tree(), 1)
        main_layout.addLayout(content_layout)

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


    def _create_year_folder_tree(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel(f"Carpetas del año {self.year_value}:")
        title.setStyleSheet("color: #85c1e9; font-size: 12px;")
        layout.addWidget(title)

        year_root = str(self.year_dir)

        self.year_folder_model = QFileSystemModel(self)

        # Filtro corregido y más permisivo para carpetas (desactivado)
        # self.year_folder_model.setFilter(
        #     QDir.Filter.Dirs | QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Readable
        # )

        self.year_folder_tree = QTreeView()
        self.year_folder_tree.setModel(self.year_folder_model)

        # 1. Primero asignamos la ruta base
        self.year_folder_model.setRootPath(year_root)

        # 2. SOLUCIÓN: Forzamos el índice de inmediato sin esperar la señal asíncrona
        root_index = self.year_folder_model.index(year_root)
        self.year_folder_tree.setRootIndex(root_index)

        # 3. Ocultamos las columnas usando el valor por defecto de QFileSystemModel (suele ser 4)
        for column in range(1, 4):
            self.year_folder_tree.hideColumn(column)

        # Mantenemos la señal solo para refrescos o expansiones automáticas futuras
        self.year_folder_model.directoryLoaded.connect(self._refresh_year_folder_root)

        self.year_folder_tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.year_folder_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.year_folder_tree.setHeaderHidden(True)
        self.year_folder_tree.setMinimumWidth(260)
        self.year_folder_tree.clicked.connect(self.open_folder_from_tree)

        self.year_folder_tree.expanded.connect(self._limit_tree_depth)

        layout.addWidget(self.year_folder_tree)
        return container

    def _limit_tree_depth(self, index: QModelIndex):
        """Evita que el usuario expanda más allá del segundo nivel."""
        if not index.isValid():
            return

        # Calculamos la profundidad subiendo por los padres del índice
        depth = 0
        current_index = index

        # Subimos por el árbol hasta llegar al nodo raíz visible (rootIndex)
        root_index = self.year_folder_tree.rootIndex()
        while current_index.isValid() and current_index != root_index:
            current_index = current_index.parent()
            depth += 1

        # depth == 1: Primer nivel (Carpetas principales dentro del año)
        # depth == 2: Segundo nivel (Subcarpetas)
        # Si depth >= 2, significa que el usuario intentó expandir una subcarpeta del segundo nivel
        if depth >= 2:
            self.year_folder_tree.collapse(index)


    def _refresh_year_folder_root(self, path: str):
        if Path(path) != self.year_dir:
            return

        root_index = self.year_folder_model.index(str(self.year_dir))
        self.year_folder_tree.setRootIndex(root_index)
        self.year_folder_tree.expand(root_index)

        # CORRECCIÓN: Ocultar las columnas excedentes aquí,
        # cuando el modelo ya tiene sus columnas inicializadas.
        for column in range(1, self.year_folder_model.columnCount()):
            self.year_folder_tree.hideColumn(column)

    def open_folder_from_tree(self, index: QModelIndex):
        if not index.isValid() or not self.year_folder_model.isDir(index):
            return

        folder_path = self.year_folder_model.filePath(index)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def add_package_item(self):
        text = self.txt_new_package.text().strip()
        if text:
            # Comprobar si ya existe
            exists = False
            for i in range(self.list_other_packages.count()):
                if self.list_other_packages.item(i).text() == text:
                    exists = True
                    break
            if not exists:
                self.list_other_packages.addItem(QListWidgetItem(text))
                self.txt_new_package.clear()
            else:
                QMessageBox.warning(self, "Advertencia", "El ID de paquete ya existe en la lista.")

    def del_package_item(self):
        current_item = self.list_other_packages.currentItem()
        if current_item:
            self.list_other_packages.takeItem(self.list_other_packages.row(current_item))
        else:
            QMessageBox.warning(self, "Advertencia", "Seleccione un elemento de la lista para eliminar.")

    def save_data(self):
        try:
            # 1. Obtener la lista de otros paquetes
            other_packages = []
            for i in range(self.list_other_packages.count()):
                other_packages.append(self.list_other_packages.item(i).text())

            # 2. Actualizar el diccionario
            self.year_data["season_abreviation"] = self.txt_season_abreviation.text().strip()
            self.year_data["esentia_name"] = self.txt_esentia_name.text().strip()
            self.year_data["other_id_package_default"] = other_packages

            # 3. Asegurar que la carpeta exista
            self.identity_dir.mkdir(parents=True, exist_ok=True)

            # 4. Guardar archivo JSON
            with open(self.json_filepath, "w", encoding="utf-8") as f:
                json.dump({"year_data": self.year_data}, f, indent=4, ensure_ascii=False)

            self.saved = True
            self.accept()
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo JSON:\n{e}\n\nDetalles:\n{tb}")


class ConnectionRenameDialog(QDialog):
    """
    Diálogo para cambiar el nombre de un lazo de conexión con reemplazo de espacios en tiempo real.
    """
    def __init__(self, connection, json_path, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.json_path = json_path
        self.saved = False

        self.setWindowTitle("Cambiar Nombre de Lazo / Conexión")
        self.setModal(True)
        # Tamaño un poco más ancho para ver todo el nombre
        self.setMinimumWidth(550)
        self.resize(600, 180)

        # Quitar botón de ayuda
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Aplicar estilos oscuros del Theme
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
                padding: 6px;
                color: {Theme.TEXT_WHITE};
                font-size: 12px;
            }}
            QLineEdit:focus {{
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        info_label = QLabel(f"Modificando lazo de conexión: {self.connection.from_year} → {self.connection.to_year}")
        info_label.setStyleSheet("color: #85c1e9; font-size: 12px;")
        layout.addWidget(info_label)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Nombre del Lazo:"))
        
        self.txt_name = QLineEdit(self.connection.name)
        form_layout.addWidget(self.txt_name)
        layout.addLayout(form_layout)

        # Reemplazar espacios por guión bajo en tiempo real
        self.txt_name.textChanged.connect(self._replace_spaces)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_discard = QPushButton("Descartar")
        self.btn_discard.clicked.connect(self.reject)

        footer_layout.addWidget(self.btn_save)
        footer_layout.addWidget(self.btn_discard)
        layout.addLayout(footer_layout)

    def _replace_spaces(self):
        text = self.txt_name.text()
        if " " in text:
            cursor_pos = self.txt_name.cursorPosition()
            new_text = text.replace(" ", "_")
            self.txt_name.blockSignals(True)
            self.txt_name.setText(new_text)
            self.txt_name.setCursorPosition(cursor_pos)
            self.txt_name.blockSignals(False)

    def save_data(self):
        new_name = self.txt_name.text().strip()
        
        # 1. Cargar infrastructure.json
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer la infraestructura:\n{e}")
            return

        # 2. Modificar la conexión que corresponde
        found = False
        for sd_data in data:
            for conn_data in sd_data.get("connections", []):
                if conn_data.get("from") == self.connection.from_year and conn_data.get("to") == self.connection.to_year:
                    conn_data["range_name"] = new_name
                    found = True
                    break
            if found:
                break

        if not found:
            QMessageBox.warning(self, "Advertencia", "No se encontró la conexión lógica en el archivo de infraestructura.")
            return

        # 3. Guardar en infrastructure.json
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la infraestructura:\n{e}")
            return

        self.saved = True
        self.accept()
