# domain_visor/progress_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt
from domain_visor.theme import Theme

class ScanWorker(QObject):
    """
    Worker que ejecuta el escaneo y verificación de la caché en segundo plano.
    """
    progress = pyqtSignal(int)      # Emite el porcentaje de progreso (0-100)
    status_msg = pyqtSignal(str)   # Emite un mensaje de estado actual
    finished = pyqtSignal()         # Emite al terminar

    def __init__(self, character_manager):
        super().__init__()
        self.character_manager = character_manager

    def run(self):
        # 1. Obtener los años a procesar para poder emitir progreso detallado
        first_year = self.character_manager.get_first_infrastructure_year()
        import datetime
        current_year = datetime.date.today().year
        years = list(range(first_year, current_year + 1))
        total_steps = len(years) + 1  # Años + Paso inicial de verificación de caché anterior

        self.status_msg.emit("Verificando la caché de personajes existente...")
        self.progress.emit(0)

        # Paso de verificación inicial de caché existente
        if not self.character_manager.TRUST_CACHE:
            dirty = False
            years_to_check = list(self.character_manager._cache.keys())
            for idx, year_str in enumerate(years_to_check):
                valid_chars = []
                for char in self.character_manager._cache[year_str]:
                    import pathlib
                    char_path_str = char.get("character_path", "")
                    if char_path_str and pathlib.Path(char_path_str).exists():
                        valid_chars.append(char)
                    else:
                        dirty = True
                if len(valid_chars) != len(self.character_manager._cache[year_str]):
                    self.character_manager._cache[year_str] = valid_chars
                    dirty = True
            if dirty:
                self.character_manager.save_cache_file()

        self.progress.emit(int(1 / total_steps * 100))

        # 2. Escanear cada año de forma individual y reportar progreso
        if not self.character_manager.base_path.exists():
            self.status_msg.emit(f"Advertencia: No existe {self.character_manager.base_path}")
            self.progress.emit(100)
            self.finished.emit()
            return

        updated_cache = {}
        for idx, year in enumerate(years):
            self.status_msg.emit(f"Analizando año {year}...")

            album_prefix = f"{max(0, year - 2003):02d}"
            year_dir = self.character_manager.base_path / str(year) / f"{album_prefix}. album"

            if year_dir.exists():
                characters_list = []
                try:
                    for item in year_dir.iterdir():
                        if item.is_dir():
                            folder_name = item.name
                            prefix_to_check = f"{album_prefix}. "
                            if not folder_name.startswith(prefix_to_check):
                                continue

                            rest = folder_name[len(prefix_to_check):]
                            if rest.count(";") != 4:
                                continue

                            parts = rest.split(";")
                            raw_pos, alterego, name, birthday, raw_age = parts

                            try:
                                position = int(raw_pos)
                                age = int(raw_age)
                                datetime.datetime.strptime(birthday, "%Y-%m-%d")
                            except ValueError:
                                continue

                            json_file = item / f"__{name}__.json"
                            char_data = {}

                            if json_file.exists():
                                try:
                                    with open(json_file, "r", encoding="utf-8") as jf:
                                        loaded_data = json.load(jf)
                                        char_data = loaded_data.get("character_data", {})
                                except Exception:
                                    pass

                            if not char_data:
                                icon_path = ""
                                img_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
                                for sub_item in sorted(item.iterdir()):
                                    if sub_item.is_file() and sub_item.suffix.lower() in img_extensions:
                                        icon_path = sub_item.name
                                        break

                                char_data = {
                                    "year": year,
                                    "position": position,
                                    "name": name,
                                    "alterego": alterego,
                                    "birthday": birthday,
                                    "age": age,
                                    "icon_path": icon_path,
                                    "background_path": "",
                                    "type_underwear": "",
                                    "short_masked_alterego": "",
                                    "character_path": str(item.resolve()),
                                    "color_group": "",
                                    "profession_group": ""
                                }

                                try:
                                    with open(json_file, "w", encoding="utf-8") as jf:
                                        json.dump({"character_data": char_data}, jf, indent=4, ensure_ascii=False)
                                except Exception:
                                    pass

                            characters_list.append(char_data)
                except Exception:
                    pass

                if characters_list:
                    characters_list.sort(key=lambda c: c.get("position", 0))
                    updated_cache[str(year)] = characters_list[:6]

            # Emitir progreso después de procesar este año
            current_progress = int((idx + 2) / total_steps * 100)
            self.progress.emit(min(100, current_progress))

        # Guardar todo al final
        self.character_manager._cache.update(updated_cache)
        self.character_manager.save_cache_file()

        self.status_msg.emit("¡Escaneo e indexación completados!")
        self.progress.emit(100)
        self.finished.emit()


class ProgressDialog(QDialog):
    """
    Ventana de progreso que muestra el estado de escaneo de los personajes en segundo plano.
    Diseñada de forma no modal con estilos adaptados al visor.
    """
    def __init__(self, character_manager, parent=None):
        super().__init__(parent)
        self.character_manager = character_manager
        self.setWindowTitle("Indexando personajes...")
        self.setFixedSize(420, 150)

        # Eliminar botón de ayuda del encabezado de la ventana
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Aplicar colores del tema
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.APP_BACKGROUND};
                color: {Theme.TEXT_WHITE};
                border: 1px solid {Theme.SUPERDOMAIN_BORDER};
            }}
            QLabel {{
                color: {Theme.TEXT_WHITE};
                font-family: Arial;
                font-size: 11px;
            }}
            QProgressBar {{
                border: 1px solid {Theme.SUPERDOMAIN_BORDER};
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
                color: {Theme.TEXT_WHITE};
                height: 18px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ROLE_EXODOMAIN_BG};
                width: 10px;
            }}
        """)

        # Configurar UI
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)

        self.info_label = QLabel("Iniciando indexación de personajes...", self)
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # Configurar Hilo de Procesamiento
        self.thread = QThread(self)
        self.worker = ScanWorker(character_manager)
        self.worker.moveToThread(self.thread)

        # Conectar señales del worker
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status_msg.connect(self.info_label.setText)
        self.worker.finished.connect(self.on_scan_finished)

        # Iniciar hilo al abrir la ventana
        self.thread.started.connect(self.worker.run)

    def start_loading(self):
        """Inicia el hilo de escaneo y muestra el diálogo."""
        self.thread.start()
        self.show()

    def on_scan_finished(self):
        """Maneja el fin de la indexación, deteniendo el hilo y cerrando el diálogo."""
        self.thread.quit()
        self.thread.wait()
        self.accept()
