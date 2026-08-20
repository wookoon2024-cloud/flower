"""
Speech Bubble Widget
Renders dynamic auto-sizing speech bubble above plant character with tail,
drop shadow, multi-page smooth text flowing animation for long text, auto-dismiss timer,
and real-time token streaming typing effect.
"""
import re
from typing import List
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush, QPen, QFont

def chunk_speech_text(text: str, max_chars_per_page: int = 34) -> List[str]:
    """
    Split long speech text into natural, readable multi-page flowing sentences.
    Ensures long fortunes, AI monologues, and alerts never get truncated or clipped!
    """
    if not text or len(text) <= max_chars_per_page:
        return [text] if text else [""]

    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    segments = []
    for line in raw_lines:
        # Split by sentence boundaries (. ! ? ~ \n)
        parts = re.split(r'(?<=[.!?~])\s+', line)
        for p in parts:
            if p.strip():
                segments.append(p.strip())

    if not segments:
        segments = [text]

    pages = []
    current_page = ""
    for seg in segments:
        if not current_page:
            current_page = seg
        elif len(current_page) + len(seg) + 1 <= max_chars_per_page:
            current_page += " " + seg
        else:
            pages.append(current_page)
            current_page = seg
    if current_page:
        pages.append(current_page)

    # Word wrap safety for long sentences without punctuation
    final_pages = []
    for pg in pages:
        if len(pg) <= max_chars_per_page + 6:
            final_pages.append(pg)
        else:
            words = pg.split(" ")
            buf = ""
            for w in words:
                if len(buf) + len(w) + 1 <= max_chars_per_page:
                    buf = (buf + " " + w).strip()
                else:
                    if buf:
                        final_pages.append(buf)
                    buf = w
            if buf:
                final_pages.append(buf)

    return final_pages if final_pages else [text]


class SpeechBubbleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(180, 55)

        # Multi-page flowing text timers
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bubble)

        self.page_timer = QTimer(self)
        self.page_timer.setSingleShot(True)
        self.page_timer.timeout.connect(self._advance_page)

        self.is_active = False
        self.streamed_text = ""
        self.pages: List[str] = []
        self.current_page_idx = 0
        self.page_duration_ms = 4500  # 4.5 seconds per page (1 second longer for comfortable reading)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 10)  # Bottom margin for tail
        
        self.content_widget = QWidget(self)
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(6, 2, 4, 2)
        self.content_layout.setSpacing(2)

        self.label = QLabel("", self.content_widget)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Malgun Gothic", 9, QFont.Weight.Medium)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #1E293B; background: transparent; padding: 0px; margin: 0px;")

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
        """
        Display text with speech bubble. If the text is longer than can fit in a single bubble,
        it automatically flows across readable sequential pages smoothly without cutting off.
        """
        self.hide_timer.stop()
        self.page_timer.stop()

        self.pages = chunk_speech_text(text, max_chars_per_page=34)
        self.current_page_idx = 0
        self.is_active = True
        self.content_widget.setVisible(True)

        if len(self.pages) <= 1:
            # Single page standard message
            self.label.setText(text)
            self.update()
            if duration_sec > 0:
                self.hide_timer.start(duration_sec * 1000)
        else:
            # Multi-page flowing text sequence
            self._render_current_page()
            self.page_timer.start(self.page_duration_ms)

    def _render_current_page(self):
        """Renders the active flowing page with page indicator if multi-page."""
        if not self.pages or self.current_page_idx >= len(self.pages):
            return

        page_content = self.pages[self.current_page_idx]
        total = len(self.pages)
        if total > 1:
            display_text = f"{page_content} <span style='color:#94A3B8; font-size:8pt;'>({self.current_page_idx + 1}/{total})</span>"
            self.label.setText(display_text)
        else:
            self.label.setText(page_content)
        self.update()

    def _advance_page(self):
        """Advance to next flowing page or auto-hide when completed."""
        self.current_page_idx += 1
        if self.current_page_idx < len(self.pages):
            self._render_current_page()
            # If last page, show slightly longer
            duration = self.page_duration_ms + 500 if self.current_page_idx == len(self.pages) - 1 else self.page_duration_ms
            self.page_timer.start(duration)
        else:
            self.hide_bubble()

    def start_streaming(self):
        """Prepares speech bubble for real-time token streaming."""
        self.hide_timer.stop()
        self.page_timer.stop()
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
        """Finishes token streaming and activates flowing pages if long."""
        self.show_message(final_text, duration_sec)

    def hide_bubble(self):
        self.hide_timer.stop()
        self.page_timer.stop()
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
