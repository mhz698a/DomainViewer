# domain_visor/year_item.py

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QGraphicsItem

from domain_visor.port_item import PortItem
from domain_visor.theme import Theme

class YearItem(QGraphicsItem):
    """
    Representa un año individual dentro de un dominio (Paso de Commit 5, 6 y 11).
    Responsabilidades:
    - Dibujar el número del año centrado en su rectángulo.
    - Dibujar un borde punteado blanco con esquinas redondeadas y sin fondo.
    - Utilizar la fuente del visor actual (Arial 10) y texto del tema.
    - Heredar de QGraphicsItem y asociarse jerárquicamente a su DomainItem padre.
    - Instanciar e incorporar dos puertos (PortItem) de conexión.
    """
    def __init__(self, x, y, width, height, year_value, parent=None):
        super().__init__(parent)
        self._x = float(x)
        self._y = float(y)
        self._width = float(width)
        self._height = float(height)
        self._year_value = year_value

        # Instanciar puertos de conexión izquierdo y derecho
        port_diameter = 8.0
        port_y = self._y + (self._height - port_diameter) / 2.0

        # El puerto izquierdo se ubica cerca del borde izquierdo
        left_port_x = self._x + 4.0
        self.left_port = PortItem(left_port_x, port_y, port_diameter, "left", parent=self)

        # El puerto derecho se ubica cerca del borde derecho
        right_port_x = self._x + self._width - 12.0
        self.right_port = PortItem(right_port_x, port_y, port_diameter, "right", parent=self)

    def boundingRect(self) -> QRectF:
        # Retorna el área que cubre este ítem de año
        return QRectF(self._x, self._y, self._width, self._height)

    def paint(self, painter, option, widget=None):
        painter.save()

        # Activar suavizado para texto perfecto y bordes redondeados
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. Dibujar el borde punteado con esquinas redondeadas y sin fondo
        border_pen = QPen(QColor(Theme.TEXT_WHITE))
        border_pen.setStyle(Qt.PenStyle.DotLine)
        border_pen.setWidthF(1.0)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        rect = QRectF(self._x, self._y, self._width, self._height)
        painter.drawRoundedRect(rect, 4.0, 4.0)

        # 2. Dibujar el año centrado en su rectángulo usando el tema centralizado
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor(Theme.TEXT_WHITE))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._year_value))

        painter.restore()
