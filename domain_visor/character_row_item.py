# domain_visor/character_row_item.py

import os
from pathlib import Path
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPixmap
from PyQt6.QtWidgets import QGraphicsItem, QToolTip

from domain_visor.theme import Theme

# Caché global en memoria para las imágenes pre-cargadas en el hilo secundario
PIXMAP_CACHE = {}

class CharacterIconItem(QGraphicsItem):
    """
    Representa un cuadrado individual de perfil de personaje de 20x20px.
    """
    def __init__(self, char_data, parent=None):
        super().__init__(parent)
        self.char_data = char_data
        self._size = 20.0

        # Cargar datos del personaje
        self.position = char_data.get("position", 1)
        self.name = char_data.get("name", "")
        self.alterego = char_data.get("alterego", "")
        self.icon_path = char_data.get("icon_path", "")
        self.character_path = char_data.get("character_path", "")

        # Formatear el Tooltip (requisito 5): "{name} - {alterego}"
        # Transformación nombre propio (Title Case) y sin guiones bajos
        formatted_name = self.name.replace("_", " ").strip().title()
        formatted_alterego = self.alterego.replace("_", " ").strip().title()

        if not formatted_name:
            formatted_name = "?"
        if not formatted_alterego:
            formatted_alterego = "?"

        tooltip_text = f"{formatted_name} - {formatted_alterego}"
        self.setToolTip(tooltip_text)

        # Cargar pixmap de forma segura usando la caché global pre-cargada
        self.pixmap = None
        if self.icon_path and self.character_path:
            full_img_path = str(Path(self.character_path) / self.icon_path)
            if full_img_path in PIXMAP_CACHE:
                self.pixmap = PIXMAP_CACHE[full_img_path]
            else:
                if Path(full_img_path).exists():
                    self.pixmap = QPixmap(full_img_path)
                    PIXMAP_CACHE[full_img_path] = self.pixmap

        # Configurar cursor apuntador para interacción (requisito clásico)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = QRectF(0, 0, self._size, self._size)

        # 1. Dibujar Imagen o "?" (requisito 4)
        if self.pixmap and not self.pixmap.isNull():
            # Dibujar la imagen escalada para que quepa en el cuadrado de 20x20
            painter.drawPixmap(rect.toRect(), self.pixmap)
        else:
            # Mostrar icono de "?" con texto "{position}?"
            painter.setBrush(QBrush(QColor("#2d2d2d")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)

            font = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(Theme.TEXT_WHITE))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.position}?")

        # 2. El cuadrado tendrá un contorno delgado pero visible (requisito 6)
        border_pen = QPen(QColor(Theme.TEXT_WHITE))
        border_pen.setWidthF(1.0)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawRect(rect)

        painter.restore()


class CharacterRowItem(QGraphicsItem):
    """
    Contenedor de perfiles/personajes distribuidos en el centro de la fila.
    """
    def __init__(self, characters_data, width, parent=None):
        super().__init__(parent)
        self.characters_data = characters_data
        self._width = float(width)
        self._height = 20.0
        self.icons = []

        # Instanciar hasta 6 perfiles
        count = len(characters_data)
        if count > 0:
            total_icons_width = count * 20.0 + (count - 1) * 5.0
            # Distribuir centrado dentro del ancho total
            start_x = (self._width - total_icons_width) / 2.0

            for idx, char_data in enumerate(characters_data):
                icon_item = CharacterIconItem(char_data, parent=self)
                icon_x = start_x + idx * (20.0 + 5.0)
                icon_item.setPos(icon_x, 0)
                self.icons.append(icon_item)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    def paint(self, painter, option, widget=None):
        # El contenedor en sí es invisible, solo dibuja sus hijos
        pass
