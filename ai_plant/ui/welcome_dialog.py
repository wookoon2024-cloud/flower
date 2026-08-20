"""
Welcome & Initial Plant Setup Dialog
Allows users on first launch to configure their name, choose their initial plant species,
and give their companion plant a custom nickname before starting.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QApplication, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ..plant_engine import SPECIES_INFO
from ..config import get_resource_path

class WelcomeSetupDialog(QDialog):
    setup_completed = Signal(str, str, str)  # (user_nickname, plant_name, species)

    def __init__(self, config_manager, plant_engine, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.engine = plant_engine
        self.selected_species = ["classic"]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🌱 환영합니다! 나만의 AI 반려화분 입양하기")
        self.resize(620, 600)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # 1. Welcome Banner
        banner = QFrame(self)
        banner.setObjectName("WelcomeBanner")
        banner.setStyleSheet("""
            QFrame#WelcomeBanner {
                background-color: #ECFDF5;
                border: 1.5px solid #A7F3D0;
                border-radius: 12px;
            }
            #WelcomeBanner QLabel {
                border: none;
                background: transparent;
            }
        """)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(14, 12, 14, 12)
        b_layout.setSpacing(4)

        t_lbl = QLabel("👋 <b>환영합니다! 공직자님의 책상 위 힐링 메이트</b>", banner)
        t_lbl.setStyleSheet("color: #065F46; font-size: 15px; border: none; background: transparent;")
        desc_lbl = QLabel("매일의 업무 피로와 스트레스를 덜어주고 힘이 되어줄 나만의 반려식물 정보를 설정해주세요 🌸", banner)
        desc_lbl.setStyleSheet("color: #047857; font-size: 11px; border: none; background: transparent;")
        desc_lbl.setWordWrap(True)

        b_layout.addWidget(t_lbl)
        b_layout.addWidget(desc_lbl)
        layout.addWidget(banner)

        # 2. User Nickname
        user_row = QHBoxLayout()
        user_lbl = QLabel("👤 <b>공직자님의 호칭/닉네임:</b>")
        user_lbl.setStyleSheet("border: none; background: transparent;")
        user_row.addWidget(user_lbl)
        self.edit_user_name = QLineEdit("공직자님", self)
        self.edit_user_name.setPlaceholderText("예: 김주무관, 민원해결사 등")
        self.edit_user_name.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 12px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 1.5px solid #10B981; }
        """)
        user_row.addWidget(self.edit_user_name, 1)
        layout.addLayout(user_row)

        # 3. Plant Species Card Grid (2 cards per row)
        species_title = QLabel("🪴 <b>함께 시작할 반려식물 품종 선택 (한 줄에 2종류씩):</b>")
        species_title.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(species_title)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E2E8F0; border-radius: 10px; background: #FAFAFA; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("QWidget { background: transparent; }")
        scroll_layout = QGridLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        scroll_layout.setHorizontalSpacing(8)
        scroll_layout.setVerticalSpacing(8)

        self.card_widgets = {}

        def update_cards():
            for sid, (card, badge, is_unlocked) in self.card_widgets.items():
                if not is_unlocked:
                    card.setStyleSheet(f"""
                        QFrame#PlantCard_{sid} {{
                            background-color: #F1F5F9;
                            border: 1px dashed #CBD5E1;
                            border-radius: 10px;
                        }}
                        #PlantCard_{sid} QLabel {{
                            border: none;
                            background: transparent;
                        }}
                    """)
                    badge.setText("🔒 잠김")
                    badge.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: bold; background-color: #E2E8F0; border-radius: 5px; padding: 2px 6px; border: none;")
                    continue

                if sid == self.selected_species[0]:
                    card.setStyleSheet(f"""
                        QFrame#PlantCard_{sid} {{
                            background-color: #ECFDF5;
                            border: 2px solid #10B981;
                            border-radius: 10px;
                        }}
                        #PlantCard_{sid} QLabel {{
                            border: none;
                            background: transparent;
                        }}
                    """)
                    badge.setText("선택됨 ✨")
                    badge.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 10px; background-color: #10B981; border-radius: 5px; padding: 2px 6px; border: none;")
                else:
                    card.setStyleSheet(f"""
                        QFrame#PlantCard_{sid} {{
                            background-color: #FFFFFF;
                            border: 1px solid #E2E8F0;
                            border-radius: 10px;
                        }}
                        QFrame#PlantCard_{sid}:hover {{
                            border-color: #CBD5E1;
                            background-color: #F8FAFC;
                        }}
                        #PlantCard_{sid} QLabel {{
                            border: none;
                            background: transparent;
                        }}
                    """)
                    badge.setText("선택하기")
                    badge.setStyleSheet("color: #64748B; font-size: 10px; background-color: #F1F5F9; border-radius: 5px; padding: 2px 6px; border: none;")

        for idx, (sp_id, info) in enumerate(SPECIES_INFO.items()):
            is_unlocked = self.engine.is_species_unlocked(sp_id)
            card = QFrame()
            card.setObjectName(f"PlantCard_{sp_id}")
            card.setCursor(Qt.CursorShape.PointingHandCursor if is_unlocked else Qt.CursorShape.ForbiddenCursor)
            
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(8, 8, 8, 8)
            c_layout.setSpacing(8)

            img_lbl = QLabel()
            img_lbl.setFixedSize(44, 44)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_path = get_resource_path(os.path.join("assets", f"stage_{sp_id}_6.png"))
            if os.path.exists(img_path):
                pm = QPixmap(img_path).scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(pm)
            else:
                img_lbl.setText(info["emoji"])
                img_lbl.setStyleSheet("font-size: 24px;")

            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)

            top_row = QHBoxLayout()
            if info.get("is_secret"):
                if is_unlocked:
                    name_lbl = QLabel(f"<b>{info['emoji']} {info['name']}</b> <span style='font-size:9px; color:#7E22CE;'>👑 전설</span>")
                else:
                    name_lbl = QLabel(f"<b>{info['emoji']} {info['name']}</b> <span style='font-size:9px; color:#DC2626;'>🔒 전설</span>")
            else:
                name_lbl = QLabel(f"<b>{info['emoji']} {info['name']}</b>")
            name_lbl.setStyleSheet("font-size: 12px; color: #1E293B;")
            badge_lbl = QLabel("선택하기")
            badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            top_row.addWidget(name_lbl, 1)
            top_row.addWidget(badge_lbl, 0)

            if info.get("is_secret") and not is_unlocked:
                desc_lbl = QLabel("🔒 5대 기본 품종을 모두 화원에 졸업시키면 봉인이 해제됩니다.")
                desc_lbl.setStyleSheet("font-size: 9.5px; color: #DC2626; font-weight: bold;")
            else:
                desc_lbl = QLabel(info["desc"])
                desc_lbl.setStyleSheet("font-size: 10px; color: #64748B;")
            desc_lbl.setWordWrap(True)

            info_layout.addLayout(top_row)
            info_layout.addWidget(desc_lbl)

            c_layout.addWidget(img_lbl, 0)
            c_layout.addLayout(info_layout, 1)

            def make_handler(sid, unlocked):
                def handler(event):
                    if not unlocked:
                        return
                    self.selected_species[0] = sid
                    update_cards()
                return handler

            card.mousePressEvent = make_handler(sp_id, is_unlocked)
            self.card_widgets[sp_id] = (card, badge_lbl, is_unlocked)

            row = idx // 2
            col = idx % 2
            scroll_layout.addWidget(card, row, col)

        update_cards()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # 4. Plant Nickname
        plant_row = QHBoxLayout()
        plant_lbl = QLabel("🏷️ <b>반려화분의 애칭/이름:</b>")
        plant_lbl.setStyleSheet("border: none; background: transparent;")
        plant_row.addWidget(plant_lbl)
        self.edit_plant_name = QLineEdit("초록이", self)
        self.edit_plant_name.setPlaceholderText("예: 초록이, 햇살이, 뽀송이 등")
        self.edit_plant_name.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 12px;
                color: #1E293B;
            }
            QLineEdit:focus { border: 1.5px solid #10B981; }
        """)
        plant_row.addWidget(self.edit_plant_name, 1)
        layout.addLayout(plant_row)

        # 5. Start Button
        btn_start = QPushButton("🌱 나만의 반려화분 키우기 시작! ✨", self)
        btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 11px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        btn_start.clicked.connect(self.on_start_clicked)
        layout.addWidget(btn_start)

    def on_start_clicked(self):
        user_name = self.edit_user_name.text().strip() or "공직자님"
        plant_name = self.edit_plant_name.text().strip() or "초록이"
        species = self.selected_species[0]

        self.config.set("user_nickname", user_name, auto_save=False)
        self.config.set("plant_name", plant_name, auto_save=False)
        self.config.set("initial_setup_done", True, auto_save=True)

        # Update initial plant state species
        st = self.engine.get_state()
        st["species"] = species
        self.engine.save()

        self.setup_completed.emit(user_name, plant_name, species)
        self.accept()
