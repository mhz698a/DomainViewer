# domain_visor/character_manager.py

import os
import json
import datetime
from pathlib import Path

class CharacterManager:
    """
    Gestiona la carga dinámica y cacheada de perfiles/personajes.
    - Escanea directorios de años desde el primer año de la infraestructura hasta el año actual.
    - Valida carpetas de personajes que tengan exactamente 4 puntos y comas (';').
    - Crea y lee archivos JSON de personaje con el nombre __{name}__.json.
    - Guarda y consulta un archivo cache global en __structure__/characters_cache.json.
    """
    TRUST_CACHE = False  # Bandera constante en el código

    def __init__(self, base_path=None, cache_path=None, infrastructure_path=None):
        # Permitir sobreescribir rutas para testing
        self.base_path = Path(base_path) if base_path else Path("E:/_Internal")
        self.cache_path = Path(cache_path) if cache_path else Path("__structure__/characters_cache.json")
        self.infrastructure_path = Path(infrastructure_path) if infrastructure_path else Path("__structure__/infrastructure.json")
        self._cache = {}
        self.load_cache_file()

    def get_first_infrastructure_year(self) -> int:
        """
        Lee infrastructure.json y retorna el año mínimo de inicio de los dominios.
        Si no se puede leer, retorna 1999 por defecto.
        """
        if not self.infrastructure_path.exists():
            return 1999
        try:
            with open(self.infrastructure_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            min_year = None
            for sd in data:
                for domain in sd.get("domains", []):
                    range_text = domain.get("range", "")
                    if "-" in range_text:
                        try:
                            start_year = int(range_text.split("-")[0])
                            if min_year is None or start_year < min_year:
                                min_year = start_year
                        except ValueError:
                            pass
            return min_year if min_year is not None else 1999
        except Exception:
            return 1999

    def load_cache_file(self):
        """Carga el archivo de caché si existe."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
        else:
            self._cache = {}

    def save_cache_file(self):
        """Guarda la caché actual al archivo JSON."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando caché de personajes: {e}")

    def verify_cache_at_startup(self):
        """
        Se asegura de que los personajes guardados en caché sigan existiendo en disco.
        Si TRUST_CACHE es False, verifica la existencia de las carpetas de los personajes en la caché.
        Si no existen, los elimina de la caché. Luego realiza un escaneo para actualizar.
        """
        if not self.TRUST_CACHE:
            dirty = False
            # Crear una lista de claves a verificar
            years_to_check = list(self._cache.keys())
            for year_str in years_to_check:
                valid_chars = []
                for char in self._cache[year_str]:
                    char_path_str = char.get("character_path", "")
                    if char_path_str and Path(char_path_str).exists():
                        valid_chars.append(char)
                    else:
                        dirty = True
                if len(valid_chars) != len(self._cache[year_str]):
                    self._cache[year_str] = valid_chars
                    dirty = True
            if dirty:
                self.save_cache_file()

        # Independientemente de TRUST_CACHE, realizamos un escaneo para asegurar que todo esté al día
        self.scan_all_years()

    def scan_all_years(self):
        """
        Escanea las carpetas de años desde el primer año hasta el año actual.
        Filtra años futuros. Actualiza la caché con los personajes encontrados.
        """
        # 1. Comprobar si la ruta base existe. Si no, mostramos un mensaje por consola
        # pero permitimos que el resto siga funcionando (requisito 1).
        if not self.base_path.exists():
            print(f"Advertencia: La ruta base {self.base_path} no existe. No se cargarán nuevos personajes de disco.")
            return

        first_year = self.get_first_infrastructure_year()
        current_year = datetime.date.today().year

        updated_cache = {}

        for year in range(first_year, current_year + 1):
            album_prefix = f"{max(0, year - 2003):02d}"
            year_dir = self.base_path / str(year) / f"{album_prefix}. album"

            if not year_dir.exists():
                continue

            characters_list = []
            try:
                # Listar subcarpetas dentro de year_dir
                for item in year_dir.iterdir():
                    if item.is_dir():
                        folder_name = item.name
                        # Debe cumplir con tener el prefijo y contener exactamente 4 ';'
                        prefix_to_check = f"{album_prefix}. "
                        if not folder_name.startswith(prefix_to_check):
                            continue

                        rest = folder_name[len(prefix_to_check):]
                        if rest.count(";") != 4:
                            continue

                        # Separar los 5 componentes
                        parts = rest.split(";")
                        raw_pos, alterego, name, birthday, raw_age = parts

                        try:
                            position = int(raw_pos)
                            age = int(raw_age)
                            # Validar formato de birthday yyyy-mm-dd de forma básica
                            datetime.datetime.strptime(birthday, "%Y-%m-%d")
                        except ValueError:
                            # Si la posición, edad o la fecha no son válidas, descartamos
                            continue

                        # Nombre del JSON: __{name}__.json
                        json_file = item / f"__{name}__.json"
                        char_data = {}

                        if json_file.exists():
                            # Requisito 2.2: si el archivo ya existe, leemos de una vez el contenido
                            try:
                                with open(json_file, "r", encoding="utf-8") as jf:
                                    loaded_data = json.load(jf)
                                    char_data = loaded_data.get("character_data", {})
                            except Exception:
                                pass

                        # Requisito 2.3: rellenar con los datos recolectados y lo demás en blanco
                        # Si no existe o le faltaban campos obligatorios, inicializar
                        if not char_data:
                            # Buscar primer imagen de la carpeta del personaje
                            icon_path = ""
                            img_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
                            for sub_item in sorted(item.iterdir()):
                                if sub_item.is_file() and sub_item.suffix.lower() in img_extensions:
                                    icon_path = sub_item.name  # ruta relativa a la carpeta de personaje
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
                                "type_underwear": [],
                                "short_masked_alterego": "",
                                "character_path": str(item.resolve()),
                                "color_group": "",
                                "profession_group": ""
                            }

                            # Guardar el JSON en la carpeta
                            try:
                                with open(json_file, "w", encoding="utf-8") as jf:
                                    json.dump({"character_data": char_data}, jf, indent=4, ensure_ascii=False)
                            except Exception as e:
                                print(f"Error guardando JSON en personaje: {e}")

                        # Agregar a la lista para guardar en caché
                        characters_list.append(char_data)
            except Exception as e:
                print(f"Error procesando el año {year}: {e}")

            if characters_list:
                # Almacenar en caché ordenados por posición
                characters_list.sort(key=lambda c: c.get("position", 0))
                # Limitar a un máximo de 6 perfiles por año (requisito profiles_row_item tiene capacidad de mostrar 6 perfiles)
                updated_cache[str(year)] = characters_list[:6]

        # Actualizar la caché en memoria y guardarla en el archivo
        self._cache.update(updated_cache)
        self.save_cache_file()

    def get_characters_for_year(self, year: int) -> list:
        """
        Retorna la lista de personajes (hasta 6) para un año determinado usando la caché.
        """
        return self._cache.get(str(year), [])
