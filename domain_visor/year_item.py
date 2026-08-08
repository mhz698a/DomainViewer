# domain_visor/year_item.py

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QGraphicsItem

from domain_visor.port_item import PortItem
from domain_visor.theme import Theme
from domain_visor.character_row_item import CharacterRowItem
from domain_visor.character_manager import CharacterManager

class YearItem(QGraphicsItem):
    """
    Representa un año individual dentro de un dominio (Paso de Commit 5, 6 y 11).
    Responsabilidades:
    - Dibujar el número del año centrado en la mitad superior de su rectángulo.
    - Dibujar un borde punteado blanco con esquinas redondeadas y sin fondo.
    - Utilizar la fuente del visor actual (Arial 10) y texto del tema.
    - Heredar de QGraphicsItem y asociarse jerárquicamente a su DomainItem padre.
    - Instanciar e incorporar dos puertos (PortItem) de conexión centrado en la fila del año (top 15.0px).
    - Incorporar dinámicamente el CharacterRowItem abajo de la fila de puertos y año si existen personajes.
    """
    # Usar una instancia de CharacterManager estática para la carga en la vista
    _char_manager = None

    @classmethod
    def get_character_manager(cls) -> CharacterManager:
        if cls._char_manager is None:
            cls._char_manager = CharacterManager()
            # Realizar verificación básica al inicio de su uso
            cls._char_manager.verify_cache_at_startup()
        return cls._char_manager

    def __init__(self, x, y, width, height, year_value, parent=None):
        super().__init__(parent)
        self._x = float(x)
        self._y = float(y)
        self._width = float(width)
        self._height = float(height)
        self._year_value = year_value

        # 1. Instanciar puertos de conexión izquierdo y derecho (siempre en la primera fila de 15.0px)
        port_diameter = 8.0
        # Verticalmente centrados en los primeros 15.0px de altura
        port_y = self._y + (15.0 - port_diameter) / 2.0

        # El puerto izquierdo se ubica cerca del borde izquierdo
        left_port_x = self._x + 4.0
        self.left_port = PortItem(left_port_x, port_y, port_diameter, "left", parent=self)

        # El puerto derecho se ubica cerca del borde derecho
        right_port_x = self._x + self._width - 12.0
        self.right_port = PortItem(right_port_x, port_y, port_diameter, "right", parent=self)

        # 2. Obtener personajes para este año e instanciar CharacterRowItem si existen
        char_manager = self.get_character_manager()
        self._characters = char_manager.get_characters_for_year(self._year_value)

        self.row_item = None
        if self._characters:
            # Ubicación: abajo de la fila de los puertos y el año del year item
            # La fila del año mide 15.0px, sumamos un pequeño espacio/padding de 4px, y luego la fila de personajes
            self.row_item = CharacterRowItem(self._characters, self._width, parent=self)
            self.row_item.setPos(self._x, self._y + 15.0 + 4.0)

    def boundingRect(self) -> QRectF:
        # Retorna el área que cubre este ítem de año (coincide con la altura dinámica calculada en LayoutEngine)
        return QRectF(self._x, self._y, self._width, self._height)

    def paint(self, painter, option, widget=None):
        painter.save()

        # Activar suavizado para texto perfecto y bordes redondeados
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. Dibujar el borde punteado con esquinas redondeadas alrededor de todo el YearItem
        border_pen = QPen(QColor(Theme.TEXT_WHITE))
        border_pen.setStyle(Qt.PenStyle.DotLine)
        border_pen.setWidthF(1.0)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        rect = QRectF(self._x, self._y, self._width, self._height)
        painter.drawRoundedRect(rect, 4.0, 4.0)

        # 2. Dibujar el año centrado horizontalmente en la primera fila de 15.0px
        year_rect = QRectF(self._x, self._y, self._width, 15.0)
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor(Theme.TEXT_WHITE))
        painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(self._year_value))

        painter.restore()
