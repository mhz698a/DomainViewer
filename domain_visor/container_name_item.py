# domain_visor/container_name_item.py

import json
from pathlib import Path
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QFontMetrics, QPen, QBrush, QColor, QPainterPath
from domain_visor.theme import Theme

class ContainerTitleDialog(QDialog):
    """
    Diálogo modal para modificar el valor de 'title_container' en container.json.
    """
    def __init__(self, container_path, current_title, parent=None):
        super().__init__(parent)
        self.container_path = Path(container_path)
        self.current_title = current_title
        self.saved = False

        self.setWindowTitle("Modificar Nombre del Contenedor")
        self.setModal(True)
        self.setMinimumWidth(400)

        # Quitar botón de ayuda
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Estilo coherente con el tema oscuro de la aplicación
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.APP_BACKGROUND};
                color: {Theme.TEXT_WHITE};
            }}
            QLabel {{
                color: {Theme.TEXT_WHITE};
                font-family: Arial;
                font-size: 11px;
                font-weight: bold;
            }}
            QLineEdit {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: {Theme.TEXT_WHITE};
                font-family: Arial;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: #85c1e9;
            }}
            QPushButton {{
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 14px;
                color: {Theme.TEXT_WHITE};
                font-family: Arial;
                font-size: 11px;
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

        layout.addWidget(QLabel("Nombre de la infraestructura (title_container):"))
        self.txt_title = QLineEdit(self.current_title)
        layout.addWidget(self.txt_title)

        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_save = QPushButton("Guardar")
        self.btn_save.clicked.connect(self.save_data)
        self.btn_discard = QPushButton("Descartar")
        self.btn_discard.clicked.connect(self.reject)

        footer_layout.addWidget(self.btn_save)
        footer_layout.addWidget(self.btn_discard)
        layout.addLayout(footer_layout)

    def save_data(self):
        new_title = self.txt_title.text().strip()
        if not new_title:
            QMessageBox.warning(self, "Validación", "El título no puede estar vacío.")
            return

        try:
            container_data = [{"title_container": new_title}]
            self.container_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.container_path, "w", encoding="utf-8") as f:
                json.dump(container_data, f, indent=4, ensure_ascii=False)

            self.saved = True
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo container.json:\n{e}")


class ContainerNameItem(QGraphicsItem):
    """
    QGraphicsItem para mostrar la etiqueta del nombre de la infraestructura (title_container).
    - Margen interior de 5px alrededor del texto.
    - Contorno blanco grueso.
    - Fondo gris.
    - Esquina redondeada de 6px.
    - Puntero hand al ponerse encima.
    - Diálogo modal para modificar el valor al hacer clic.
    """
    def __init__(self, x, y, width, height, title, container_path, parent=None):
        super().__init__(parent)
        self.setPos(x, y)
        self.width = width
        self.height = height
        self.title = title
        self.container_path = container_path

        self.font = QFont("Arial", 11, QFont.Weight.Bold)

        # Habilitar puntero de mano
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        # Dibujar fondo gris con bordes redondeados de 6px y contorno blanco grueso
        rect = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(rect, 6.0, 6.0)

        # Fondo gris y contorno blanco grueso (width 2.5)
        painter.fillPath(path, QBrush(QColor("#3e3e42")))
        pen = QPen(QColor("#ffffff"), 2.5)
        painter.setPen(pen)
        painter.drawPath(path)

        # Dibujar texto exacto centrado
        painter.setFont(self.font)
        painter.setPen(QPen(QColor(Theme.TEXT_WHITE)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.title)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.open_edit_dialog()
        else:
            super().mouseReleaseEvent(event)

    def open_edit_dialog(self):
        parent_widget = None
        if self.scene() and self.scene().views():
            parent_widget = self.scene().views()[0].window()

        dlg = ContainerTitleDialog(self.container_path, self.title, parent=parent_widget)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.saved:
            if parent_widget and hasattr(parent_widget, 'trigger_render'):
                parent_widget.trigger_render()
