"""
Speech Bubble Widget
Renders dynamic auto-sizing speech bubble above plant character with tail,
drop shadow, auto-dismiss timer, and real-time token streaming typing effect.
"""
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush, QPen, QFont

class SpeechBubbleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(180, 55)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bubble)

        self.is_active = False
        self.streamed_text = ""
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 12)  # Bottom margin for tail
        
        self.content_widget = QWidget(self)
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 4, 6, 4)
        self.content_layout.setSpacing(4)

        self.label = QLabel("", self.content_widget)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Malgun Gothic", 9, QFont.Weight.Medium)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #1E293B; background: transparent; line-height: 1.3;")

        self.close_btn = QPushButton("✕", self.content_widget)
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94A3B8;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        self.close_btn.clicked.connect(self.hide_bubble)

        self.content_layout.addWidget(self.label, 1)
        self.content_layout.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignTop)

        main_layout.addWidget(self.content_widget)

        # Drop shadow on the bubble widget
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        self.content_widget.setVisible(False)

    def show_message(self, text: str, duration_sec: int = 5):
        """Display text with speech bubble and start auto-hide timer."""
        self.hide_timer.stop()
        self.label.setText(text)
        self.is_active = True
        self.content_widget.setVisible(True)
        self.update()

        if duration_sec > 0:
            self.hide_timer.start(duration_sec * 1000)

    def start_streaming(self):
        """Prepares speech bubble for real-time token streaming."""
        self.hide_timer.stop()
        self.streamed_text = ""
        self.label.setText("")
        self.is_active = True
        self.content_widget.setVisible(True)
        self.update()

    def append_chunk(self, chunk: str):
        """Appends streaming token chunk in real-time."""
        self.streamed_text += chunk
        self.label.setText(self.streamed_text)
        self.update()

    def finish_streaming(self, final_text: str, duration_sec: int = 5):
        """Finishes token streaming and activates auto-hide timer."""
        self.label.setText(final_text)
        self.update()
        if duration_sec > 0:
            self.hide_timer.start(duration_sec * 1000)

    def hide_bubble(self):
        self.hide_timer.stop()
        self.is_active = False
        self.content_widget.setVisible(False)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.is_active:
            return

        rect = self.rect()
        bubble_rect = rect.adjusted(3, 2, -3, -12)

        path = QPainterPath()
        path.addRoundedRect(bubble_rect.x(), bubble_rect.y(), bubble_rect.width(), bubble_rect.height(), 12, 12)

        tail_center_x = rect.width() // 2
        tail_top_y = bubble_rect.bottom()
        tail_bottom_y = rect.height() - 1
        
        tail_path = QPainterPath()
        tail_path.moveTo(tail_center_x - 8, tail_top_y)
        tail_path.lineTo(tail_center_x, tail_bottom_y)
        tail_path.lineTo(tail_center_x + 8, tail_top_y)
        tail_path.closeSubpath()

        full_path = path.united(tail_path)

        painter.fillPath(full_path, QBrush(QColor(255, 255, 255, 250)))
        pen = QPen(QColor(203, 213, 225, 255), 1.2)
        painter.setPen(pen)
        painter.drawPath(full_path)
