"""
Control Bar Widget
Interactive popup control bar providing mini status gauges (water, sunlight, affection)
and quick interaction buttons (water, sun, chat, garden, settings).
All buttons and gauges are dynamically sized and cleanly centered without clipping.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

class StatusMiniBar(QWidget):
    def __init__(self, icon: str, tooltip: str, color_hex: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.icon_lbl = QLabel(icon, self)
        self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 11px; padding: 0px;")
        
        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)
        self.bar.setValue(50)
        self.bar.setTextVisible(False)
        self.bar.setFixedSize(34, 6)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(226, 232, 240, 0.9);
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 3px;
            }}
        """)
        self.setToolTip(tooltip)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.bar)

    def set_value(self, val: int):
        self.bar.setValue(max(0, min(100, val)))


class ControlBarWidget(QWidget):
    water_clicked = Signal()
    sun_clicked = Signal()
    chat_clicked = Signal()
    garden_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Capsule background container
        self.container = QWidget(self)
        self.container.setObjectName("controlContainer")
        self.container.setStyleSheet("""
            #controlContainer {
                background-color: rgba(255, 255, 255, 0.97);
                border: 1px solid rgba(203, 213, 225, 0.9);
                border-radius: 12px;
            }
            QWidget {
                border: none;
                background: transparent;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(4)

        # 1. Mini Status Gauges row
        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(5)
        gauge_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.water_bar = StatusMiniBar("💧", "수분 상태", "#3B82F6", self.container)
        self.sun_bar = StatusMiniBar("☀️", "햇빛 상태", "#F59E0B", self.container)
        self.aff_bar = StatusMiniBar("💖", "애정도", "#EC4899", self.container)

        gauge_row.addWidget(self.water_bar)
        gauge_row.addWidget(self.sun_bar)
        gauge_row.addWidget(self.aff_bar)
        container_layout.addLayout(gauge_row)

        # 2. Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(3)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_style_normal = """
            QPushButton {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 3px 4px;
                font-size: 11px;
                font-family: 'Malgun Gothic', 'Segoe UI';
                font-weight: bold;
                color: #334155;
                height: 24px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border-color: #94A3B8;
            }
            QPushButton:pressed {
                background-color: #E2E8F0;
            }
        """

        self.btn_water = QPushButton("💧 물주기", self.container)
        self.btn_water.setStyleSheet(btn_style_normal)
        self.btn_water.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_water.setToolTip("화분에 물을 줍니다 (+25 수분)")
        self.btn_water.clicked.connect(self.water_clicked.emit)

        self.btn_sun = QPushButton("☀️ 햇빛", self.container)
        self.btn_sun.setStyleSheet(btn_style_normal)
        self.btn_sun.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sun.setToolTip("화분에 햇빛을 쬡니다 (+25 햇빛)")
        self.btn_sun.clicked.connect(self.sun_clicked.emit)

        self.btn_chat = QPushButton("💬 대화", self.container)
        self.btn_chat.setStyleSheet("""
            QPushButton {
                background-color: #ECFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 6px;
                padding: 3px 4px;
                font-size: 11px;
                font-family: 'Malgun Gothic', 'Segoe UI';
                font-weight: bold;
                color: #065F46;
                height: 24px;
            }
            QPushButton:hover {
                background-color: #D1FAE5;
                border-color: #6EE7B7;
            }
            QPushButton:pressed {
                background-color: #A7F3D0;
            }
        """)
        self.btn_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chat.setToolTip("AI 반려식물과 대화합니다")
        self.btn_chat.clicked.connect(self.chat_clicked.emit)

        self.btn_garden = QPushButton("🌿", self.container)
        self.btn_garden.setStyleSheet("""
            QPushButton {
                background-color: #FEF3C7;
                border: 1px solid #FDE68A;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FDE68A;
            }
        """)
        self.btn_garden.setFixedSize(24, 24)
        self.btn_garden.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_garden.setToolTip("나의 화원 & 100종 업적 도감 / 졸업 / 포춘")
        self.btn_garden.clicked.connect(self.garden_clicked.emit)

        self.btn_settings = QPushButton("⚙️", self.container)
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
            }
        """)
        self.btn_settings.setFixedSize(24, 24)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("환경 설정")
        self.btn_settings.clicked.connect(self.settings_clicked.emit)

        btn_row.addWidget(self.btn_water, 1)
        btn_row.addWidget(self.btn_sun, 1)
        btn_row.addWidget(self.btn_chat, 1)
        btn_row.addWidget(self.btn_garden, 0)
        btn_row.addWidget(self.btn_settings, 0)
        container_layout.addLayout(btn_row)

        main_layout.addWidget(self.container)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def update_status(self, state: dict):
        """Update gauges with plant state values."""
        self.water_bar.set_value(state.get("water", 80))
        self.sun_bar.set_value(state.get("sunlight", 80))
        self.aff_bar.set_value(state.get("affection", 20))
