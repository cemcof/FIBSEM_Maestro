import logging
import time

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QPen, QPixmap, QColor, QImage, QTransform
from PySide6.QtCore import QRect, Qt, QPoint, QSize

from fibsem_maestro.GUI.gui_tools import get_pixmap
from fibsem_maestro.tools.support import Image, ScanningArea


def create_image_label(layout):
    for i in range(layout.count()):
        field_item = layout.itemAt(i)
        if field_item is not None:
            widget = field_item.widget()
            if isinstance(widget, ImageLabel):
                return widget
    # image label
    label = ImageLabel()
    layout.insertWidget(0, label)
    layout.setAlignment(label, Qt.AlignTop | Qt.AlignLeft)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return label

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # actual drawing rect
        self.rect = QRect()
        self.adjusted_rect = QRect()  # zoom and pan applied
        # handles of actual drawing rect
        self.handles = [QRect() for _ in range(4)]
        self.handleSize = 10
        self.handleSelected = -1
        self.mousePressPos = None

        # panning
        self.delta = QPoint(0,0)  # offset used for panning

        # zoom in/out
        self.scale = 1
        self.original_scale = 1  # scale after initial resize (after image load)

        self.original_pixmap = None

        self.hide_graphics = False  # used form overlay hiding
        self.image = None  # original image (class Image)
        self.rects_to_draw = []  # buffer for rectangle drawing (ScanningArea, (R,G,B))

        # Setting up the buttons for zooming in and out
        self.zoom_in_button = QtWidgets.QPushButton("+", self)
        self.zoom_in_button.setFixedWidth(20)
        self.zoom_in_button.clicked.connect(self.zoom_in)

        self.zoom_out_button = QtWidgets.QPushButton("-", self)
        self.zoom_out_button.setFixedWidth(20)
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.hide_button = QtWidgets.QPushButton("o", self)
        self.hide_button.setFixedWidth(20)
        self.hide_button.clicked.connect(self.hide)

        # Positioning the buttons at the top left corner of ImageLabel
        self.zoom_in_button.move(5, 5)
        self.zoom_out_button.move(self.zoom_in_button.width() + 5, 5)
        self.hide_button.move(self.zoom_out_button.width() + self.zoom_in_button.width() + 10, 5)

        # double-click handling
        self.last_right_click_time = 0
        self.last_left_click_time = 0
        self.click_interval = 0.5

        # event of repainting
        self.repaint_events = []

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.hide_graphics:
            painter = QPainter(self)

            lime = QColor(0, 255, 0)
            painter.setPen(QPen(lime, 2, Qt.SolidLine))
            painter.drawRect(self.adjusted_rect)
            painter.setPen(QPen(lime, 2, Qt.SolidLine))
            for handle in self.handles:
                if not handle.isNull():
                    painter.fillRect(handle, lime)
            for r in self.rects_to_draw:
                if r[0] is not None and r[1] is not None and self.image is not None:
                    pen_color = QColor(*r[1])
                    painter.setPen(QPen(pen_color, 2, Qt.SolidLine))
                    left_top, [width, height] = r[0].to_img_coordinates(self.image.shape)
                    rect_to_paint = QRect(left_top.x, left_top.y, width, height)
                    rect_to_paint = self.calculate_coordinates(rect_to_paint)
                    painter.drawRect(rect_to_paint)

            painter.end()

    def mousePressEvent(self, event):
        mousePos = event.position().toPoint()
        self.mousePressPos = mousePos
        if event.buttons() == Qt.LeftButton:
            # resizing by handle or retangle drawing
            self.handleSelected = -1
            for i, handle in enumerate(self.handles):
                if handle.contains(mousePos):
                    self.handleSelected = i
            if self.handleSelected == -1:
                self.rect.setTopLeft((mousePos-self.delta) / self.scale)
                self.rect.setBottomRight((mousePos-self.delta) / self.scale)

            current_time = time.time()
            if current_time - self.last_left_click_time < self.click_interval:
                # set maximal rectangle if left double click
                self.reset_zoom_pan()
                self.rect.setRect(0, 0, self.original_pixmap.width(), self.original_pixmap.height())  # maximize rectangle
            self.last_left_click_time = current_time

            self.update()

        if event.button() == Qt.RightButton:
            # zero zoom pan
            current_time = time.time()
            if current_time - self.last_right_click_time < self.click_interval:
                # reset zoom and pan if right double click
                self.reset_zoom_pan()
            self.last_right_click_time = current_time

    def mouseMoveEvent(self, event):
        mousePos = event.position().toPoint()
        if event.buttons() == Qt.RightButton:
            # panning
            self.pan((mousePos - self.mousePressPos) / self.scale)
            self.mousePressPos = mousePos
        elif event.buttons() == Qt.LeftButton:  # when left button is held down
            # rect drawing
            if self.handleSelected >= 0:  # if a handle is selected
                self.resizeRectangle(mousePos)
            else:  # if no handle is selected, draw rectangle
                self.rect.setBottomRight((mousePos-self.delta) / self.scale)
                self.updateHandles()
        elif event.buttons() == Qt.NoButton:  # when mouse is just hovering
            # check if the mouse is on some handle
            handleHovered = -1
            for i, handle in enumerate(self.handles):
                if handle.contains(mousePos):
                    handleHovered = i
            self.handleHovered = handleHovered
        self.update()

    def mouseReleaseEvent(self, event):
        """ Release dragging handle """
        self.handleSelected = -1
        self.mousePressPos = None
        self.update()

    def wheelEvent(self, event):
        """ Function to handle mouse wheel event """
        wheel_direction = event.angleDelta().y()

        if wheel_direction < 0:
            self.zoom_out()
        else:
            self.zoom_in()

    def resizeRectangle(self, mousePos):
        if self.handleSelected == 0:  # left
            dx = (mousePos.x() - self.mousePressPos.x()) / self.scale
            self.rect.setLeft(self.rect.left() + dx)
        elif self.handleSelected == 1:  # top
            dy = (mousePos.y() - self.mousePressPos.y()) / self.scale
            self.rect.setTop(self.rect.top() + dy)
        elif self.handleSelected == 2:  # right
            dx = (mousePos.x() - self.mousePressPos.x()) / self.scale
            self.rect.setRight(self.rect.right() + dx)
        elif self.handleSelected == 3:  # bottom
            dy = (mousePos.y() - self.mousePressPos.y()) / self.scale
            self.rect.setBottom(self.rect.bottom() + dy)
        self.mousePressPos = mousePos

    def update(self):
        super().update()
        self.updateHandles()
        self.repaint_pixmap()

    def update_pan_zoom(self, scale: float, delta: QPoint):
        self.scale = scale
        self.delta = delta
        self.update()

    def updateHandles(self):
        handleSize = self.handleSize
        self.adjusted_rect = self.calculate_coordinates(self.rect)
        self.handles[0].setRect(self.adjusted_rect.left(), self.adjusted_rect.top() + self.adjusted_rect.height() // 2, handleSize,
                                handleSize)  # left
        self.handles[1].setRect(self.adjusted_rect.left() + self.adjusted_rect.width() // 2, self.adjusted_rect.top(), handleSize,
                                handleSize)  # top
        self.handles[2].setRect(self.adjusted_rect.right() - handleSize, self.adjusted_rect.top() + self.adjusted_rect.height() // 2, handleSize,
                                handleSize)  # right
        self.handles[3].setRect(self.adjusted_rect.left() + self.adjusted_rect.width() // 2, self.adjusted_rect.bottom() - handleSize, handleSize,
                                handleSize)  # bottom

    def setImage(self, image: Image):
        self.image = image
        # Qt displays image in format [y,x] -> need transpose
        pixmap = get_pixmap(image, transpose=True)
        self.setPixmap(pixmap)

    def setPixmap(self, pixmap):
        """ Resize if too big """
        app = QApplication.instance()  # get instance of current QApplication
        window = app.activeWindow()  # get reference to active window
        size = window.size()  # get size of current window
        width = size.width() * 0.75  # The image will cover 75% of primary screen
        height = size.height() * 0.6  # The image will cover 60% of primary screen

        if pixmap.width() > width or pixmap.height() > height:
            # Keep aspect ratio and use smooth transformation while scaling
            scaled_pixmap = pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        else:
            scaled_pixmap = pixmap

        if pixmap.width() > 0:
            self.scale = scaled_pixmap.width() / pixmap.width()
            self.original_scale = self.scale
            self.original_pixmap = pixmap
            self.update()

    def pan(self, pan):
        self.delta += pan
        self.repaint_connections()

    def zoom(self, scale):
        self.scale *= scale
        self.delta *= scale
        self.update()
        self.repaint_connections()

    def repaint_connections(self):
        """ Zoom on connected images """
        for repaint_event in self.repaint_events:
            repaint_event(self.scale, self.delta)

    def zoom_in(self):
        """Zoom in the image"""
        self.zoom(1.1)

    def zoom_out(self):
        """Zoom out the image"""
        self.zoom(1/1.1)

    def reset_zoom_pan(self):
        """ zoom to 1 and panning to 0"""
        self.zoom(self.original_scale/self.scale)
        self.delta = QPoint(0, 0)
        self.update()

    def hide(self):
        self.hide_graphics = not self.hide_graphics
        self.update()

    def repaint_pixmap(self):
        """Repaint the pixmap with new scale"""
        if self.original_pixmap is not None:
            original_pixmap = self.original_pixmap.copy()  # get a copy of original pixmap
            width = original_pixmap.width() * self.scale
            height = original_pixmap.height() * self.scale
            scaled_pixmap = original_pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.updateHandles()

            # shift
            shifted_pixmap = QPixmap(scaled_pixmap.size())
            shifted_pixmap.fill(Qt.white)
            painter = QPainter(shifted_pixmap)
            painter.drawPixmap(self.delta, scaled_pixmap)
            painter.end()

            super().setPixmap(shifted_pixmap)

    def calculate_coordinates(self, r):
        """ From source coordinates to display coordinates (scale + panning)"""
        x = r.left() * self.scale + self.delta.x()
        y = r.top() * self.scale + self.delta.y()
        width = r.width() * self.scale
        height = r.height() * self.scale
        return QRect(x, y, width, height)

    def get_selected_area(self) -> ScanningArea:
        """ Get selected rect position and size (ScanningArea)"""
        if self.image is None:
            logging.warning('Trying to get scanning area without image')
            return None
        else:
            return ScanningArea.from_image_coordinates(self.image.shape, self.rect.left(), self.rect.top(),
                                                       self.rect.width(), self.rect.height())