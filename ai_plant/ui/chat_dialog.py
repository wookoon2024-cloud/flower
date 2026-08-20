"""
Chat Dialog Widget
A friendly, modern chat window with 100% native PySide6 KakaoTalk-style message bubbles,
guaranteed right-aligned user messages, custom plant-inspired emerald/white theme,
micro-assistant chips, and rock-solid thread/event safety.
"""
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QWidget, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

def format_chat_time(timestamp_str: str) -> str:
    """Format ISO timestamp into clean AM/PM hour:minute."""
    if not timestamp_str:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str)
        hour = dt.hour
        minute = dt.minute
        ampm = "오전" if hour < 12 else "오후"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{ampm} {display_hour}:{minute:02d}"
    except Exception:
        return ""


class UserMessageBubble(QWidget):
    """Native right-aligned user speech bubble with timestamp."""
    def __init__(self, content: str, time_str: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 4, 2)
        layout.setSpacing(6)

        # Push completely to the right edge
        layout.addStretch(1)

        # Timestamp on the left of user bubble, bottom-aligned
        if time_str:
            time_lbl = QLabel(time_str, self)
            time_lbl.setStyleSheet("color: #8C9CAE; font-size: 10px; border: none; background: transparent;")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignBottom)

        # Bubble content
        bubble = QLabel(content, self)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(265)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #059669;
                color: #FFFFFF;
                border-radius: 14px;
                border-top-right-radius: 2px;
                padding: 9px 13px;
                font-size: 12px;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
        """)
        layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignRight)


class BotMessageBubble(QWidget):
    """Native left-aligned companion plant speech bubble with avatar and timestamp."""
    def __init__(self, plant_name: str, content: str, time_str: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 0, 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Plant Avatar Icon
        avatar = QLabel("🌱", self)
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 16px;
                font-size: 15px;
            }
        """)
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        # Content Column (Name + Bubble + Time)
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)

        name_lbl = QLabel(f"🌱 {plant_name}", self)
        name_lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        col.addWidget(name_lbl)

        bubble_row = QHBoxLayout()
        bubble_row.setContentsMargins(0, 0, 0, 0)
        bubble_row.setSpacing(6)

        bubble = QLabel(content, self)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(265)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 14px;
                border-top-left-radius: 2px;
                padding: 9px 13px;
                font-size: 12px;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
        """)
        bubble_row.addWidget(bubble, 0, Qt.AlignmentFlag.AlignLeft)

        if time_str:
            time_lbl = QLabel(time_str, self)
            time_lbl.setStyleSheet("color: #8C9CAE; font-size: 10px; border: none; background: transparent;")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
            bubble_row.addWidget(time_lbl, 0, Qt.AlignmentFlag.AlignBottom)

        col.addLayout(bubble_row)
        layout.addLayout(col)

        # Push to left
        layout.addStretch(1)


class TypingIndicatorBubble(QWidget):
    """Typing indicator shown while AI is thinking."""
    def __init__(self, plant_name: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 0, 2)
        layout.setSpacing(8)

        avatar = QLabel("🌱", self)
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 16px;
                font-size: 15px;
            }
        """)
        layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)

        name_lbl = QLabel(f"🌱 {plant_name}", self)
        name_lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        col.addWidget(name_lbl)

        bubble = QLabel("답변을 작성하고 있어요... 💭", self)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                color: #059669;
                border: 1px solid #A7F3D0;
                border-radius: 14px;
                border-top-left-radius: 2px;
                padding: 8px 12px;
                font-size: 11.5px;
                font-style: italic;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
        """)
        col.addWidget(bubble)
        layout.addLayout(col)
        layout.addStretch(1)


class ChatDialog(QDialog):
    message_sent = Signal(str)

    def __init__(self, db_manager, config_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.config = config_manager
        self.is_thinking = False
        self.init_ui()

    def init_ui(self):
        plant_name = self.config.get("plant_name", "초록이")
        self.setWindowTitle(f"🌱 {plant_name}와(과) 대화하기")
        self.resize(440, 580)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Header Row (Title + Close Button)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 4)

        user_name = self.config.get("user_nickname", "공직자님")
        self.header_lbl = QLabel(f"💬 <b>{user_name}</b> 님과 <b>{plant_name}</b>의 힐링 대화방", self)
        self.header_lbl.setStyleSheet("color: #334155; font-size: 13px;")

        self.btn_header_close = QPushButton("닫기 ✕", self)
        self.btn_header_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_header_close.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                color: #64748B;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                border-color: #FCA5A5;
                color: #DC2626;
            }
        """)
        self.btn_header_close.clicked.connect(self.close)

        header_row.addWidget(self.header_lbl, 1)
        header_row.addWidget(self.btn_header_close, 0)
        layout.addLayout(header_row)

        # Message History Canvas (Native QScrollArea with soft messenger background)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #EBF1F6;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 0px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.scroll_content.setStyleSheet("#scrollContent { background-color: #EBF1F6; }")
        self.chat_vbox = QVBoxLayout(self.scroll_content)
        self.chat_vbox.setContentsMargins(10, 10, 10, 10)
        self.chat_vbox.setSpacing(10)
        self.chat_vbox.addStretch(1)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, 1)

        # Smart AI Assistant Chips Container
        chips_frame = QFrame(self)
        chips_frame.setStyleSheet("""
            QFrame {
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        chips_vbox = QVBoxLayout(chips_frame)
        chips_vbox.setContentsMargins(6, 6, 6, 6)
        chips_vbox.setSpacing(5)

        # Chip Row 1: Emotional Healing & Empathy
        row1 = QHBoxLayout()
        row1.setSpacing(5)
        r1_chips = [
            ("🌿 오늘 하루 위로해줘", "오늘 하루 너무 수고 많았다고 따뜻하게 위로해줘 🌸"),
            ("✨ 비타민 응원", "기운 팍팍 나는 비타민 같은 응원 한마디 부탁해! ☀️"),
            ("☕ 피로회복 스트레칭", "나른한데 3분 스트레칭 방법 추천해줘 💧")
        ]
        for label, full_prompt in r1_chips:
            btn = self.create_chip_btn(label, full_prompt, direct_send=True)
            row1.addWidget(btn)
        chips_vbox.addLayout(row1)

        # Chip Row 2: Office & Desk Micro-Assistant
        row2 = QHBoxLayout()
        row2.setSpacing(5)
        r2_chips = [
            ("✉️ 문장 다듬기", f"{plant_name}아, 다음 문장을 공직자용으로 정중하고 부드럽게 다듬어줘: ", False),
            ("💡 3줄 아이디어", f"{plant_name}아, 다음에 대한 창의적인 아이디어 3가지만 제안해줘: ", False),
            ("📝 오늘의 3줄 일기", f"{plant_name}아, 오늘 우리 함께한 하루를 귀여운 3줄 일기로 요약해줘! 🌸", True)
        ]
        for label, prompt_or_prefix, is_direct in r2_chips:
            btn = self.create_chip_btn(label, prompt_or_prefix, direct_send=is_direct)
            row2.addWidget(btn)
        chips_vbox.addLayout(row2)

        layout.addWidget(chips_frame)

        # Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_edit = QLineEdit(self)
        self.input_edit.setPlaceholderText("메시지를 입력하세요 (Enter로 전송)...")
        self.input_edit.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1.5px solid #10B981;
            }
        """)
        self.input_edit.returnPressed.connect(self.handle_send)

        self.btn_send = QPushButton("전송 🚀", self)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.clicked.connect(self.handle_send)

        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.btn_send)
        layout.addLayout(input_row)

        self.load_history()

    def create_chip_btn(self, label: str, prompt_text: str, direct_send: bool) -> QPushButton:
        btn = QPushButton(label, self)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 11px;
                color: #334155;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #ECFDF5;
                border-color: #6EE7B7;
                color: #065F46;
            }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if direct_send:
            btn.clicked.connect(lambda checked=False, t=prompt_text: self.send_chip(t))
        else:
            btn.clicked.connect(lambda checked=False, p=prompt_text: self.prefill_prompt(p))
        return btn

    def prefill_prompt(self, prefix: str):
        self.input_edit.setText(prefix)
        self.input_edit.setFocus()
        self.input_edit.setCursorPosition(len(prefix))

    def refresh_header(self):
        plant_name = self.config.get("plant_name", "초록이")
        user_name = self.config.get("user_nickname", "공직자님")
        self.setWindowTitle(f"🌱 {plant_name}와(과) 대화하기")
        self.header_lbl.setText(f"💬 <b>{user_name}</b> 님과 <b>{plant_name}</b>의 힐링 대화방")

    def load_history(self):
        """Render native KakaoTalk style message bubble widgets into the scroll area."""
        # 1. Remove all existing bubble widgets
        while self.chat_vbox.count() > 1:
            item = self.chat_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. Fetch recent chat logs
        chats = self.db.get_recent_chat_history(limit=30)
        plant_name = self.config.get("plant_name", "초록이")

        # 3. Add bubble widgets before the bottom stretch
        insert_idx = 0
        for chat in chats:
            role = chat.get("role")
            content = str(chat.get("content", "")).strip()
            if not content:
                continue
            time_str = format_chat_time(chat.get("timestamp", ""))

            if role == "user":
                bubble_w = UserMessageBubble(content, time_str, self.scroll_content)
            else:
                bubble_w = BotMessageBubble(plant_name, content, time_str, self.scroll_content)
            
            self.chat_vbox.insertWidget(insert_idx, bubble_w)
            insert_idx += 1

        # 4. If AI is thinking, add typing indicator
        if self.is_thinking:
            typing_w = TypingIndicatorBubble(plant_name, self.scroll_content)
            self.chat_vbox.insertWidget(insert_idx, typing_w)

        self.scroll_to_bottom()

    def append_message(self, role: str, content: str):
        self.load_history()

    def scroll_to_bottom(self):
        QTimer.singleShot(40, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def send_chip(self, text: str):
        self.input_edit.setText(text)
        self.handle_send()

    def handle_send(self):
        text = self.input_edit.text().strip()
        if not text:
            return

        self.input_edit.clear()
        self.set_loading(True)
        self.message_sent.emit(text)

    def set_loading(self, is_loading: bool):
        self.is_thinking = is_loading
        self.input_edit.setEnabled(not is_loading)
        self.btn_send.setEnabled(not is_loading)
        self.load_history()
        if not is_loading:
            self.input_edit.setFocus()
