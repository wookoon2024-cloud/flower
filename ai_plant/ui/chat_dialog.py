"""
Chat Dialog Widget
A friendly, modern chat window for conversing with the AI companion plant,
equipped with smart micro-assistant chips (emotional care, business text polisher, brainstorming, mini-diary),
in-browser thinking indicator (no layout jitter), and smooth message bubbles.
"""
import html
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit,
    QPushButton, QLabel, QWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

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
        self.resize(440, 560)
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

        # Message History Browser
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.browser, 1)

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
        """Load and safely render chat logs into the browser with HTML escaping."""
        self.browser.clear()
        chats = self.db.get_recent_chat_history(limit=25)
        user_name = self.config.get("user_nickname", "나")
        plant_name = self.config.get("plant_name", "초록이")

        esc_user = html.escape(str(user_name))
        esc_plant = html.escape(str(plant_name))

        html_parts = []
        for chat in chats:
            role = chat.get("role")
            content = chat.get("content", "")
            esc_content = html.escape(str(content)).replace("\n", "<br>")
            if role == "user":
                html_parts.append(f"""
                <div style="text-align: right; margin-bottom: 8px;">
                    <span style="display: inline-block; background-color: #DCF8C6; color: #1F2937; padding: 6px 10px; border-radius: 10px; font-size: 12px; max-width: 80%; text-align: left;">
                        <b>{esc_user}</b>: {esc_content}
                    </span>
                </div>
                """)
            else:
                html_parts.append(f"""
                <div style="text-align: left; margin-bottom: 8px;">
                    <span style="display: inline-block; background-color: #F1F5F9; color: #1F2937; padding: 6px 10px; border-radius: 10px; font-size: 12px; max-width: 80%;">
                        <b>{esc_plant}</b>: {esc_content}
                    </span>
                </div>
                """)
        
        if self.is_thinking:
            html_parts.append(f"""
            <div style="text-align: left; margin-bottom: 8px;">
                <span style="display: inline-block; background-color: #F1F5F9; color: #059669; padding: 6px 10px; border-radius: 10px; font-size: 12px; max-width: 80%; font-style: italic;">
                    🌱 <b>{esc_plant}</b>이(가) 생각을 가다듬고 있어요... 💭
                </span>
            </div>
            """)

        self.browser.setHtml("".join(html_parts))
        self.scroll_to_bottom()

    def append_message(self, role: str, content: str):
        """Appends a new message in real-time."""
        self.load_history()

    def scroll_to_bottom(self):
        QTimer.singleShot(30, lambda: self.browser.verticalScrollBar().setValue(
            self.browser.verticalScrollBar().maximum()
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
