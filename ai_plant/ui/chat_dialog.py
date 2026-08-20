"""
Chat Dialog Widget
A friendly, modern chat window with 100% native PySide6 KakaoTalk-style message bubbles,
guaranteed right-aligned user messages with comfortable margin protection (no text clipping),
custom plant-inspired emerald/white theme, micro-assistant chips, and rock-solid thread safety.
"""
import random
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QWidget, QScrollArea, QFrame, QSizePolicy, QApplication
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
    """Native right-aligned user speech bubble with timestamp and generous padding."""
    def __init__(self, content: str, time_str: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        # 10px right margin so vertical scrollbar never clips the bubble
        layout.setContentsMargins(0, 2, 10, 2)
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
        bubble.setMaximumWidth(280)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #059669;
                color: #FFFFFF;
                border-radius: 14px;
                border-top-right-radius: 2px;
                padding: 9px 15px 9px 15px;
                font-size: 12px;
                line-height: 1.4;
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
        layout.setContentsMargins(6, 2, 0, 2)
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
        bubble.setMaximumWidth(280)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 14px;
                border-top-left-radius: 2px;
                padding: 9px 15px 9px 15px;
                font-size: 12px;
                line-height: 1.4;
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
        layout.setContentsMargins(6, 2, 0, 2)
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
                padding: 8px 14px;
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
        self.resize(460, 600)
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
        self.btn_header_close.setAutoDefault(False)
        self.btn_header_close.setDefault(False)
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
        # Auto-scroll to bottom whenever layout height expands
        self.scroll_area.verticalScrollBar().rangeChanged.connect(self._on_scroll_range_changed)
        layout.addWidget(self.scroll_area, 1)

        # Smart AI Assistant Chips Container
        chips_frame = QFrame(self)
        chips_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        chips_vbox = QVBoxLayout(chips_frame)
        chips_vbox.setContentsMargins(8, 6, 8, 6)
        chips_vbox.setSpacing(4)

        # Header Row (Title + Shuffle button)
        header_chip_row = QHBoxLayout()
        header_chip_row.setContentsMargins(0, 0, 0, 0)
        lbl_chip_title = QLabel("💡 <b>AI 스마트 추천 질문</b>", chips_frame)
        lbl_chip_title.setStyleSheet("color: #475569; font-size: 11px; border: none; background: transparent;")

        self.btn_refresh_chips = QPushButton("🔄 다른 질문 보기", chips_frame)
        self.btn_refresh_chips.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_chips.setAutoDefault(False)
        self.btn_refresh_chips.setDefault(False)
        self.btn_refresh_chips.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #059669;
                font-size: 11px;
                font-weight: bold;
                padding: 1px 4px;
            }
            QPushButton:hover {
                color: #047857;
                text-decoration: underline;
            }
        """)
        self.btn_refresh_chips.clicked.connect(self.shuffle_chips)

        header_chip_row.addWidget(lbl_chip_title, 1)
        header_chip_row.addWidget(self.btn_refresh_chips, 0)
        chips_vbox.addLayout(header_chip_row)

        self.chips_row1 = QHBoxLayout()
        self.chips_row1.setSpacing(5)
        self.chips_row2 = QHBoxLayout()
        self.chips_row2.setSpacing(5)

        chips_vbox.addLayout(self.chips_row1)
        chips_vbox.addLayout(self.chips_row2)

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
        self.btn_send.setAutoDefault(False)
        self.btn_send.setDefault(False)
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

        self.shuffle_chips()
        self.load_history()

    def shuffle_chips(self):
        """Randomly select and render 6 diverse prompt chips from 25+ curated presets."""
        plant_name = self.config.get("plant_name", "초록이")

        # 1. Clear existing chip buttons
        while self.chips_row1.count():
            item = self.chips_row1.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while self.chips_row2.count():
            item = self.chips_row2.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. 4 Diverse Preset Pools (25+ items)
        pools = [
            # Group 1: Workplace Stress & Mentoring (직장 스트레스 & 멘토링)
            [
                ("🍵 직장 고민 상담소", f"{plant_name}아, 오늘 회사에서 스트레스 받는 일이 있었는데 내 이야기 좀 들어줘...", True),
                ("👔 상사·동료 갈등 털어놓기", f"{plant_name}아, 오늘 계장님/과장님/팀원 때문에 답답하고 속상한 일이 있어: ", False),
                ("📑 업무 과부하 토닥토닥", f"{plant_name}아, 일이 너무 몰리고 지쳐서 번아웃 올 것 같아... 힐링 위로 부탁해 🌸", True),
                ("😤 악성 민원/무리한 요구", f"{plant_name}아, 오늘 억지 민원/무리한 업무 요구를 받아서 멘탈이 흔들려... 토닥여줘 🥺", True),
                ("🕊️ 퇴근 후 머리 비우기", f"{plant_name}아, 오늘 퇴근하고 집에 왔는데 업무 생각 안 나게 머릿속을 비우는 힐링 가이드 해줘", True),
                ("💪 월요병/출근 극복 응원", f"{plant_name}아, 오늘따라 출근하기 너무 힘들고 무기력해... 힘나는 응원 한마디 해줘!", True),
                ("☕ 3분 티타임 힐링", f"{plant_name}아, 잠깐 3분 동안 심호흡하고 마음을 안정시키는 짧은 명상 가이드 해줘 🍵", True)
            ],
            # Group 2: Office & Desk Micro-Assistant (공직/오피스 업무 비서)
            [
                ("✉️ 문장 다듬기", f"{plant_name}아, 다음 문장을 공직자용으로 정중하고 명확하게 다듬어줘: ", False),
                ("💡 3줄 아이디어", f"{plant_name}아, 다음에 대한 창의적인 기획 아이디어 3가지만 제안해줘: ", False),
                ("📊 긴 글 3줄 핵심 요약", f"{plant_name}아, 다음 긴 글이나 보고 자료를 핵심만 3줄로 알기 쉽게 요약해줘: ", False),
                ("📧 공손한 메일/답장 작성", f"{plant_name}아, 다음 상황에 맞는 공손하고 깔끔한 업무 메신저/메일 답장을 작성해줘: ", False),
                ("🗓️ 오늘 할 일 우선순위 정리", f"{plant_name}아, 오늘 해야 할 일들을 중요도/긴급도별로 깔끔하게 정리해줘: ", False),
                ("⚖️ 상사/동료 완곡한 거절", f"{plant_name}아, 업무 부탁이나 요청을 정중하고 기분 상하지 않게 거절하는 표현 알려줘: ", False)
            ],
            # Group 3: Plant Tamagotchi & Fun (반려식물 교감 & 재미)
            [
                ("📝 오늘의 3줄 일기", f"{plant_name}아, 오늘 우리 함께한 하루를 귀여운 3줄 일기로 요약해줘! 🌸", True),
                ("🥠 오늘의 힐링 포춘", f"{plant_name}아, 오늘 나를 위한 행운의 포춘 메시지와 행운의 색상을 알려줘! 🍀", True),
                ("🌱 화분아 뭐하고 있어?", f"{plant_name}아, 지금 화분에서 무슨 생각하고 있어? 오늘 기분 어때? 💕", True),
                ("🎧 집중/힐링 음악 추천", f"{plant_name}아, 지금 차분하게 집중하기 좋은 음악 장르나 플레이리스트 키워드 추천해줘 🎶", True),
                ("🍱 오늘 점심/저녁 메뉴", f"{plant_name}아, 오늘 먹으면 든든하고 기운 나는 점심/저녁 메뉴 3가지만 추천해줘! 🥗", True),
                ("🎯 가벼운 힐링 퀴즈", f"{plant_name}아, 머리 식힐 겸 가볍게 맞출 수 있는 힐링 넌센스나 상식 퀴즈 하나 내줘! 🧠", True)
            ],
            # Group 4: Mindfulness & Self-Care (마음 챙김 & 자기 돌봄)
            [
                ("🙆 1분 오피스 스트레칭", f"{plant_name}아, 오래 앉아 일하느라 뻐근한 목과 어깨를 풀어주는 1분 스트레칭 알려줘 ✨", True),
                ("💖 나를 칭찬하는 한마디", f"{plant_name}아, 오늘 하루도 열심히 버텨낸 나 자신에게 해줄 수 있는 따뜻한 칭찬 메시지 해줘 🌿", True),
                ("☀️ 아침 긍정 확언", f"{plant_name}아, 오늘 하루를 활기차고 긍정적으로 시작할 수 있는 아침 확언 한 줄 들려줘 🌈", True),
                ("💤 숙면을 돕는 밤 인사", f"{plant_name}아, 오늘 밤 편안하게 푹 잘 수 있도록 다정한 밤 인사와 수면 팁 건네줘 🌙", True)
            ]
        ]

        # 3. Pick 6 diverse chips: 2 from group 1, 2 from group 2, 1 from group 3, 1 from group 4
        chosen = []
        chosen.extend(random.sample(pools[0], min(2, len(pools[0]))))
        chosen.extend(random.sample(pools[1], min(2, len(pools[1]))))
        chosen.extend(random.sample(pools[2], min(1, len(pools[2]))))
        chosen.extend(random.sample(pools[3], min(1, len(pools[3]))))
        random.shuffle(chosen)

        # 4. Distribute into Row 1 (3 chips) and Row 2 (3 chips)
        for i, (label, prompt_or_prefix, is_direct) in enumerate(chosen):
            btn = self.create_chip_btn(label, prompt_or_prefix, direct_send=is_direct)
            if i < 3:
                self.chips_row1.addWidget(btn)
            else:
                self.chips_row2.addWidget(btn)

    def create_chip_btn(self, label: str, prompt_text: str, direct_send: bool) -> QPushButton:
        btn = QPushButton(label, self)
        btn.setAutoDefault(False)
        btn.setDefault(False)
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
        self.shuffle_chips()

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

    def _on_scroll_range_changed(self, min_val, max_val):
        """Automatically scroll to bottom whenever new message bubbles expand the canvas."""
        self.scroll_area.verticalScrollBar().setValue(max_val)

    def append_message(self, role: str, content: str):
        self.load_history()

    def scroll_to_bottom(self):
        """Forces immediate and deferred scroll to the lowest bottom pixel."""
        vbar = self.scroll_area.verticalScrollBar()
        vbar.setValue(vbar.maximum())
        QTimer.singleShot(20, lambda: vbar.setValue(vbar.maximum()))
        QTimer.singleShot(80, lambda: vbar.setValue(vbar.maximum()))

    def send_chip(self, text: str):
        self.input_edit.setText(text)
        self.handle_send()

    def handle_send(self):
        if self.is_thinking:
            return
        text = self.input_edit.text().strip()
        if not text:
            return

        self.input_edit.clear()
        self.set_loading(True)
        self.message_sent.emit(text)

    def set_loading(self, is_loading: bool):
        self.is_thinking = is_loading
        self.input_edit.setReadOnly(is_loading)
        self.btn_send.setEnabled(not is_loading)
        if is_loading:
            self.input_edit.setPlaceholderText("답변을 정성껏 작성하는 중입니다... 🌱")
        else:
            self.input_edit.setPlaceholderText("메시지를 입력하세요 (Enter로 전송)...")
            self.input_edit.setFocus()
        self.load_history()

    def accept(self):
        """Prevent default QDialog accept from closing on Enter key."""
        pass

    def reject(self):
        """Hide dialog on cancel."""
        self.hide()

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not self.is_thinking and not self.input_edit.isReadOnly():
                self.handle_send()
            event.accept()
        else:
            super().keyPressEvent(event)
