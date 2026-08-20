"""
Chat Dialog Widget
A friendly, modern chat window with KakaoTalk-style floating speech bubbles,
custom plant-inspired color themes (distinct from Kakao's yellow),
micro-assistant chips, in-dialogue typing status, and smooth scrolling.
"""
import html
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QLineEdit,
    QPushButton, QLabel, QWidget, QScrollArea, QFrame
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

        # Message History Browser (KakaoTalk style chatroom canvas)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #EBF1F6;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                padding: 4px;
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
        """KakaoTalk-style messenger bubble view with clean custom emerald theme."""
        self.browser.clear()
        chats = self.db.get_recent_chat_history(limit=30)
        plant_name = self.config.get("plant_name", "초록이")

        esc_plant = html.escape(str(plant_name))

        html_body = []
        html_body.append("""
        <html>
        <head>
        <style>
            body {
                background-color: #EBF1F6;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
                margin: 0;
                padding: 8px 4px;
            }
            .msg-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }
            .user-bubble {
                background-color: #059669;
                color: #FFFFFF;
                padding: 8px 12px;
                border-radius: 14px;
                border-top-right-radius: 2px;
                font-size: 12.5px;
                line-height: 1.45;
                max-width: 250px;
                word-wrap: break-word;
            }
            .bot-bubble {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                padding: 8px 12px;
                border-radius: 14px;
                border-top-left-radius: 2px;
                font-size: 12.5px;
                line-height: 1.45;
                max-width: 250px;
                word-wrap: break-word;
            }
            .bot-name {
                font-size: 11px;
                font-weight: bold;
                color: #475569;
                margin-bottom: 3px;
            }
            .avatar {
                width: 32px;
                height: 32px;
                background-color: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 16px;
                text-align: center;
                line-height: 28px;
                font-size: 16px;
            }
            .time-str {
                font-size: 10px;
                color: #8C9CAE;
                white-space: nowrap;
            }
        </style>
        </head>
        <body>
        """)

        for chat in chats:
            role = chat.get("role")
            content = chat.get("content", "")
            time_str = format_chat_time(chat.get("timestamp", ""))
            esc_content = html.escape(str(content)).replace("\n", "<br>")

            if role == "user":
                html_body.append(f"""
                <table class="msg-table" border="0" cellpadding="0" cellspacing="0">
                  <tr>
                    <td align="right">
                      <table border="0" cellpadding="0" cellspacing="0">
                        <tr>
                          <td valign="bottom" style="padding-right: 5px; padding-bottom: 2px;">
                            <span class="time-str">{time_str}</span>
                          </td>
                          <td class="user-bubble">
                            {esc_content}
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
                """)
            else:
                html_body.append(f"""
                <table class="msg-table" border="0" cellpadding="0" cellspacing="0">
                  <tr>
                    <td valign="top" width="36" style="padding-right: 8px;">
                      <div class="avatar">🌱</div>
                    </td>
                    <td align="left">
                      <div class="bot-name">{esc_plant}</div>
                      <table border="0" cellpadding="0" cellspacing="0">
                        <tr>
                          <td class="bot-bubble">
                            {esc_content}
                          </td>
                          <td valign="bottom" style="padding-left: 5px; padding-bottom: 2px;">
                            <span class="time-str">{time_str}</span>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
                """)
        
        if self.is_thinking:
            html_body.append(f"""
            <table class="msg-table" border="0" cellpadding="0" cellspacing="0">
              <tr>
                <td valign="top" width="36" style="padding-right: 8px;">
                  <div class="avatar">🌱</div>
                </td>
                <td align="left">
                  <div class="bot-name">{esc_plant}</div>
                  <table border="0" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background-color: #FFFFFF; color: #059669; border: 1px solid #A7F3D0; padding: 8px 12px; border-radius: 14px; border-top-left-radius: 2px; font-size: 12px; font-style: italic;">
                        답변을 작성하고 있어요... 💭
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
            """)

        html_body.append("</body></html>")
        self.browser.setHtml("".join(html_body))
        self.scroll_to_bottom()

    def append_message(self, role: str, content: str):
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
