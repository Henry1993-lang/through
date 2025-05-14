from PyQt6.QtWidgets import (
    QApplication, QLabel, QFileDialog, QWidget, QColorDialog,
    QMenu, QSlider, QVBoxLayout
)
from PyQt6.QtGui import QPixmap, QImage, QMouseEvent, QPainter, QPen
from PyQt6.QtCore import Qt, QPoint
from PIL import Image
import sys

class TransparentImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel(self)
        self.label.setStyleSheet("background: transparent;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_label = QLabel("透過範囲: 10", self)
        self.slider_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 80%);")
        self.slider_label.move(10, 10)

        self.tolerance_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.tolerance_slider.setGeometry(120, 10, 150, 20)
        self.tolerance_slider.setMinimum(0)
        self.tolerance_slider.setMaximum(100)
        self.tolerance_slider.setValue(10)
        self.tolerance_slider.valueChanged.connect(self.slider_changed)

        self.image_pixmap = None
        self.drag_pos = QPoint()
        self.resizing = False

        self.triangle_size = 40
        self.header_height = 40
        self.tolerance = 10
        self.target_rgb = (255, 255, 255)
        self.current_image_path = None

        self.load_image_dialog()

    def load_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "画像ファイルを選択", "", "画像 (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.process_and_show(file_path)
        else:
            self.close()

    def process_and_show(self, path):
        self.current_image_path = path
        img = Image.open(path).convert("RGBA")
        datas = img.getdata()
        new_data = []

        for item in datas:
            r, g, b, a = item
            if (
                abs(r - self.target_rgb[0]) <= self.tolerance and
                abs(g - self.target_rgb[1]) <= self.tolerance and
                abs(b - self.target_rgb[2]) <= self.tolerance
            ):
                new_data.append((r, g, b, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)
        qimg = QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)
        self.image_pixmap = QPixmap.fromImage(qimg)
        self.update_display()

    def update_display(self):
        if self.image_pixmap:
            scaled = self.image_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.label.setPixmap(scaled)
        self.label.setGeometry(self.rect())

    def resizeEvent(self, event):
        self.label.setGeometry(self.rect())
        self.slider_label.move(10, 10)
        self.tolerance_slider.setGeometry(120, 10, 150, 20)
        self.update_display()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._in_resize_corner(event.pos()):
                self.resizing = True
            elif self._in_drag_header(event.pos()):
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.resizing:
            delta = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.resize(max(delta.x(), 100), max(delta.y(), 100))
        elif event.buttons() & Qt.MouseButton.LeftButton and self._in_drag_header(event.pos()):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
        else:
            if self._in_resize_corner(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif self._in_drag_header(event.pos()):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.resizing = False

    def _in_resize_corner(self, pos):
        return pos.x() >= self.width() - self.triangle_size and pos.y() >= self.height() - self.triangle_size

    def _in_drag_header(self, pos):
        return pos.y() <= self.header_height

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.white)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))

        points = [
            QPoint(self.width(), self.height()),
            QPoint(self.width() - self.triangle_size, self.height()),
            QPoint(self.width(), self.height() - self.triangle_size)
        ]
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawPolygon(*points)

        painter.drawRect(0, 0, self.width(), self.header_height)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        change_color_action = menu.addAction("色を変更する")
        action = menu.exec(event.globalPos())
        if action == change_color_action:
            self.select_color_and_reprocess()

    def select_color_and_reprocess(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.target_rgb = (color.red(), color.green(), color.blue())
            if self.current_image_path:
                self.process_and_show(self.current_image_path)

    def slider_changed(self, value):
        self.tolerance = value
        self.slider_label.setText(f"透過範囲: {value}")
        if self.current_image_path:
            self.process_and_show(self.current_image_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TransparentImageViewer()
    viewer.show()
    sys.exit(app.exec())
