"""
Garden Dialog Module (나의 화원 및 도감 / 100종 업적 도감 / 오늘의 포춘 / 마음 날씨 감정 그래프)
Provides a rich endgame, 100 categorized achievements browser, sentiment trend visualization,
and visual image card selector for planting new seeds on graduation.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QPushButton, QScrollArea, QFrame, QLineEdit, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush, QLinearGradient, QPixmap

from ..plant_engine import SPECIES_INFO, ACHIEVEMENTS_DEF, STAGE_NAMES
from ..achievements_data import ACHIEVEMENTS_100, ACHIEVEMENT_CATEGORIES
from ..config import get_resource_path

MOOD_METADATA = {
    "happy": {"label": "기쁨/행복", "emoji": "😊", "color": "#10B981", "score": 5},
    "passionate": {"label": "열정/의욕", "emoji": "🔥", "color": "#F59E0B", "score": 4},
    "calm": {"label": "평온/보통", "emoji": "🌿", "color": "#3B82F6", "score": 3},
    "tired": {"label": "피로/지침", "emoji": "😴", "color": "#8B5CF6", "score": 2},
    "stressed": {"label": "스트레스", "emoji": "🌧️", "color": "#EF4444", "score": 1}
}

class MoodChartWidget(QWidget):
    """
    7-Day Calendar-based Daily Mood Trend Vector Chart.
    Aggregates conversation moods per day into daily average scores.
    Pre-populates upcoming/future dates in advance on the X-axis.
    """
    def __init__(self, daily_records, parent=None):
        super().__init__(parent)
        self.daily_records = daily_records or []
        self.setMinimumHeight(215)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        padding_left = 60
        padding_right = 30
        padding_top = 28
        padding_bottom = 44

        chart_w = w - padding_left - padding_right
        chart_h = h - padding_top - padding_bottom

        # 1. Background Grid & Y-Axis Labels
        y_labels = [
            (5, "최고 😊"),
            (4, "좋음 🔥"),
            (3, "평온 🌿"),
            (2, "지침 😴"),
            (1, "힘듦 🌧️")
        ]

        font = QFont("Malgun Gothic", 9)
        painter.setFont(font)

        for score, label in y_labels:
            y = padding_top + (5 - score) * (chart_h / 4.0)
            painter.setPen(QPen(QColor(241, 245, 249), 1))
            painter.drawLine(int(padding_left), int(y), int(w - padding_right), int(y))
            
            painter.setPen(QColor(100, 116, 139))
            painter.drawText(QRectF(0, y - 10, padding_left - 10, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        if not self.daily_records:
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Malgun Gothic", 10))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "대화를 나누면 공직자님의 마음 날씨 추이가 일별로 기록됩니다 🌱")
            return

        num_slots = len(self.daily_records)
        slot_step = chart_w / max(1, num_slots - 1) if num_slots > 1 else chart_w / 2.0

        points_with_data = []
        all_points = []

        for i, day in enumerate(self.daily_records):
            x = padding_left + i * slot_step
            if day.get("has_data") and day.get("avg_score") is not None:
                sc = max(1.0, min(5.0, day["avg_score"]))
                y = padding_top + (5.0 - sc) * (chart_h / 4.0)
                points_with_data.append((x, y, day))
            else:
                y = padding_top + 2.0 * (chart_h / 4.0) # Neutral score 3.0 baseline
            all_points.append((x, y, day))

        # 2. Gradient Area fill under curve (for recorded days)
        if len(points_with_data) >= 2:
            path = QPainterPath()
            path.moveTo(points_with_data[0][0], padding_top + chart_h)
            for x, y, _ in points_with_data:
                path.lineTo(x, y)
            path.lineTo(points_with_data[-1][0], padding_top + chart_h)
            path.closeSubpath()

            grad = QLinearGradient(0, padding_top, 0, padding_top + chart_h)
            grad.setColorAt(0.0, QColor(16, 185, 129, 85))
            grad.setColorAt(1.0, QColor(16, 185, 129, 0))
            painter.fillPath(path, QBrush(grad))

            # 3. Main Trend Line (solid emerald for recorded trajectory)
            line_path = QPainterPath()
            line_path.moveTo(points_with_data[0][0], points_with_data[0][1])
            for x, y, _ in points_with_data[1:]:
                line_path.lineTo(x, y)

            painter.setPen(QPen(QColor(16, 185, 129), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(line_path)

        # 4. If future slots exist, draw subtle dashed guide line from last recorded point
        if points_with_data and len(all_points) > len(points_with_data):
            last_recorded_idx = -1
            for idx, p in enumerate(all_points):
                if p[2].get("has_data"):
                    last_recorded_idx = idx
            
            if last_recorded_idx != -1 and last_recorded_idx < len(all_points) - 1:
                dash_pen = QPen(QColor(203, 213, 225), 1.5, Qt.PenStyle.DashLine)
                painter.setPen(dash_pen)
                guide_path = QPainterPath()
                guide_path.moveTo(all_points[last_recorded_idx][0], all_points[last_recorded_idx][1])
                for idx in range(last_recorded_idx + 1, len(all_points)):
                    guide_path.lineTo(all_points[idx][0], all_points[idx][1])
                painter.drawPath(guide_path)

        # 5. Draw Point Nodes and Labels
        for x, y, day in all_points:
            has_data = day.get("has_data", False)
            is_today = day.get("is_today", False)
            is_future = day.get("is_future", False)

            if has_data:
                # Outer glow ring
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(16, 185, 129, 60))
                painter.drawEllipse(QPointF(x, y), 8, 8)

                # Inner mood colored node
                m_info = MOOD_METADATA.get(day.get("mood_type"), MOOD_METADATA["calm"])
                painter.setBrush(QColor(m_info["color"]))
                painter.drawEllipse(QPointF(x, y), 4.5, 4.5)

                # Score text pill above node
                sc_val = day.get("avg_score", 3.0)
                painter.setPen(QColor(15, 118, 110))
                painter.setFont(QFont("Malgun Gothic", 8, QFont.Weight.Bold))
                painter.drawText(QRectF(x - 20, y - 18, 40, 16), Qt.AlignmentFlag.AlignCenter, f"{sc_val:.1f}")
            else:
                # Future / Unrecorded placeholder slot
                painter.setPen(QPen(QColor(203, 213, 225), 1.5, Qt.PenStyle.DotLine))
                painter.setBrush(QColor(248, 250, 252))
                painter.drawEllipse(QPointF(x, y), 3.5, 3.5)

            # 6. X-Axis Date & Weekday Labels at bottom
            d_str = day.get("date", "")
            w_str = day.get("weekday", "")

            if is_today:
                # Highlight TODAY with bold emerald
                painter.setFont(QFont("Malgun Gothic", 8, QFont.Weight.Bold))
                painter.setPen(QColor(5, 150, 105)) # #059669
                painter.drawText(QRectF(x - 28, padding_top + chart_h + 6, 56, 14), Qt.AlignmentFlag.AlignCenter, d_str)
                painter.setFont(QFont("Malgun Gothic", 7.5, QFont.Weight.Bold))
                painter.drawText(QRectF(x - 28, padding_top + chart_h + 20, 56, 14), Qt.AlignmentFlag.AlignCenter, "(오늘)")
            elif is_future:
                # Soft gray for upcoming pre-populated days
                painter.setFont(QFont("Malgun Gothic", 8))
                painter.setPen(QColor(148, 163, 184)) # #94A3B8
                painter.drawText(QRectF(x - 28, padding_top + chart_h + 6, 56, 14), Qt.AlignmentFlag.AlignCenter, d_str)
                painter.setFont(QFont("Malgun Gothic", 7.5))
                painter.drawText(QRectF(x - 28, padding_top + chart_h + 20, 56, 14), Qt.AlignmentFlag.AlignCenter, f"({w_str})")
            else:
                # Regular past date
                painter.setFont(QFont("Malgun Gothic", 8))
                painter.setPen(QColor(71, 85, 105)) # #475569
                painter.drawText(QRectF(x - 28, padding_top + chart_h + 6, 56, 14), Qt.AlignmentFlag.AlignCenter, d_str)
                painter.setFont(QFont("Malgun Gothic", 7.5))
                painter.drawText(QRectF(x - 28, padding_top + chart_h + 20, 56, 14), Qt.AlignmentFlag.AlignCenter, f"({w_str})")


class GardenDialog(QDialog):
    plant_graduated = Signal(str, str) # (new_species, new_name)
    fortune_drawn = Signal(str) # (fortune_text)

    def __init__(self, plant_engine, db_manager, config_manager, parent=None):
        super().__init__(parent)
        self.engine = plant_engine
        self.db = db_manager
        self.config = config_manager
        self.init_ui()

    def init_ui(self):
        plant_name = self.config.get("plant_name", "초록이")
        self.setWindowTitle(f"🌿 나의 화원 & 도감 - {plant_name}")
        self.resize(560, 640)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
                color: #1E293B;
                font-family: 'Malgun Gothic', 'Segoe UI';
            }
            QLabel {
                border: none;
                background: transparent;
                color: #1E293B;
            }
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background-color: #FFFFFF;
                border-radius: 10px;
                padding: 10px;
            }
            QTabBar::tab {
                background: #F1F5F9;
                color: #475569;
                padding: 9px 16px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #10B981;
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header Row
        header_row = QHBoxLayout()
        header_lbl = QLabel("🌿 <b>나의 반려식물 정원 & 마음 케어</b>", self)
        header_lbl.setStyleSheet("color: #1E293B; font-size: 16px; border: none;")
        
        btn_close = QPushButton("닫기 ✕", self)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 5px 12px;
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
        btn_close.clicked.connect(self.close)
        
        header_row.addWidget(header_lbl, 1)
        header_row.addWidget(btn_close, 0)
        layout.addLayout(header_row)

        # Tabs
        self.tabs = QTabWidget(self)
        
        # 1. Garden / Collection Tab
        self.tab_garden = self.create_garden_tab()
        self.tabs.addTab(self.tab_garden, "🪴 화원 & 졸업")

        # 2. Fortune Tab
        self.tab_fortune = self.create_fortune_tab()
        self.tabs.addTab(self.tab_fortune, "🥠 오늘의 포춘")

        # 3. Mood Chart Tab
        self.tab_mood = self.create_mood_tab()
        self.tabs.addTab(self.tab_mood, "📈 마음 날씨")

        # 4. Achievements Tab (110 Achievements)
        self.tab_achievements = self.create_achievements_tab()
        self.tabs.addTab(self.tab_achievements, "🏆 110종 업적 도감")

        layout.addWidget(self.tabs, 1)

    def create_garden_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Current Plant Summary Card (Single border)
        state = self.engine.get_state()
        species_id = self.engine.get_species()
        sp_info = SPECIES_INFO.get(species_id, SPECIES_INFO["classic"])
        plant_name = self.config.get("plant_name", "초록이")
        stage = state.get("stage", 1)

        summary_card = QFrame()
        summary_card.setStyleSheet("""
            QFrame {
                background-color: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 10px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        card_layout = QVBoxLayout(summary_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        title_lbl = QLabel(f"{sp_info['emoji']} <b>현재 키우는 화분:</b> {plant_name} ({sp_info['name']})")
        title_lbl.setStyleSheet("color: #065F46; font-size: 13px;")
        desc_lbl = QLabel(f"성장 단계: <b>{STAGE_NAMES.get(stage)}</b> | 경험치: <b>{state.get('exp', 0)} EXP</b> | 애정도: <b>{state.get('affection', 20)}💖</b>")
        desc_lbl.setStyleSheet("color: #047857; font-size: 11px;")
        
        card_layout.addWidget(title_lbl)
        card_layout.addWidget(desc_lbl)
        layout.addWidget(summary_card)

        # Graduation Button Area (Active if Stage 6)
        if stage >= 6:
            grad_btn = QPushButton("🎓 6단계 만개 달성! 화원에 졸업 등록하고 새 씨앗 심기! ✨")
            grad_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            grad_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F59E0B;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 14px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D97706;
                }
            """)
            grad_btn.clicked.connect(self.show_graduation_dialog)
            layout.addWidget(grad_btn)
        else:
            hint_lbl = QLabel("💡 최종 <b>6단계(영광의 만개)</b>에 도달하면 <b>화원 졸업 등록</b> 후 새로운 품종의 씨앗을 키울 수 있습니다!")
            hint_lbl.setStyleSheet("color: #64748B; font-size: 11px; padding: 2px;")
            layout.addWidget(hint_lbl)

        # Graduated Plants List (Scroll Area)
        list_title = QLabel("📜 <b>화원 명예의 전당 (졸업생 목록)</b>")
        list_title.setStyleSheet("color: #334155; font-size: 12px; margin-top: 4px;")
        layout.addWidget(list_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E2E8F0; border-radius: 8px; background: #FAFAFA; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(6, 6, 6, 6)
        scroll_layout.setSpacing(6)

        graduated = self.db.get_graduated_plants()
        if not graduated:
            empty_lbl = QLabel("아직 졸업한 화분이 없습니다.\n정성껏 키워 6단계 만개 후 첫 번째 졸업생을 배출해보세요! 🌸")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 24px;")
            scroll_layout.addWidget(empty_lbl)
        else:
            for plant in graduated:
                p_sp = plant.get("species", "classic")
                p_info = SPECIES_INFO.get(p_sp, SPECIES_INFO["classic"])
                p_card = QFrame()
                p_card.setStyleSheet("""
                    QFrame {
                        background-color: #FFFFFF;
                        border: 1px solid #E2E8F0;
                        border-radius: 8px;
                    }
                    QLabel {
                        border: none;
                        background: transparent;
                    }
                """)
                p_layout = QHBoxLayout(p_card)
                p_layout.setContentsMargins(10, 8, 10, 8)
                p_layout.setSpacing(8)
                
                icon_lbl = QLabel(p_info["emoji"])
                icon_lbl.setFixedWidth(28)
                icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_lbl.setStyleSheet("font-size: 20px;")
                
                info_text = QLabel(f"<b>{plant.get('name')}</b> ({p_info['name']})<br><span style='color: #64748B; font-size: 10px;'>졸업일: {plant.get('graduated_at')} | 교감 횟수: {plant.get('total_interactions')}회</span>")
                info_text.setStyleSheet("font-size: 11px;")
                info_text.setWordWrap(True)
                
                badge_lbl = QLabel("🎓 명예 졸업")
                badge_lbl.setFixedSize(80, 24)
                badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_lbl.setStyleSheet("color: #2563EB; font-weight: bold; font-size: 10px; background-color: #EFF6FF; border-radius: 4px; border: none;")
                
                p_layout.addWidget(icon_lbl)
                p_layout.addWidget(info_text, 1)
                p_layout.addWidget(badge_lbl, 0)
                scroll_layout.addWidget(p_card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        return widget

    def create_fortune_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        info_lbl = QLabel("🥠 <b>오늘의 포춘 쿠키 (일일 행운 메시지)</b>")
        info_lbl.setStyleSheet("color: #1E293B; font-size: 13px;")
        layout.addWidget(info_lbl)

        sub_lbl = QLabel("매일 1회 포춘 쿠키를 열어 공직자님을 위한 다정한 응원과 보너스 경험치를 받으세요!")
        sub_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(sub_lbl)

        # Fortune Result Card (Single border)
        self.fortune_card = QFrame()
        self.fortune_card.setStyleSheet("""
            QFrame {
                background-color: #FFFBEB;
                border: 1px solid #FDE68A;
                border-radius: 12px;
                padding: 16px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        f_layout = QVBoxLayout(self.fortune_card)
        f_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.fortune_text_lbl = QLabel("🥠 아래 버튼을 눌러 오늘의 포춘을 확인해보세요!")
        self.fortune_text_lbl.setWordWrap(True)
        self.fortune_text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fortune_text_lbl.setStyleSheet("color: #92400E; font-size: 13px; font-weight: bold; line-height: 1.5;")
        f_layout.addWidget(self.fortune_text_lbl)

        layout.addWidget(self.fortune_card, 1)

        self.btn_draw_fortune = QPushButton("🥠 오늘의 행운 포춘 쿠키 열기 (+25 EXP)")
        self.btn_draw_fortune.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_draw_fortune.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        self.btn_draw_fortune.clicked.connect(self.on_draw_fortune_clicked)
        layout.addWidget(self.btn_draw_fortune)

        import datetime
        today_str = datetime.date.today().isoformat()
        saved = self.db.get_daily_fortune(today_str)
        if saved:
            self.fortune_text_lbl.setText(f"🌟 <b>오늘의 행운 메시지:</b><br><br>{saved}")
            self.btn_draw_fortune.setText("✅ 오늘의 포춘을 이미 확인하셨습니다")
            self.btn_draw_fortune.setEnabled(False)

        return widget

    def on_draw_fortune_clicked(self):
        msg, is_first = self.engine.draw_daily_fortune()
        self.fortune_text_lbl.setText(f"🌟 <b>오늘의 행운 메시지:</b><br><br>{msg}")
        self.btn_draw_fortune.setText("✅ 오늘의 포춘을 확인하셨습니다 (+25 EXP 획득!)")
        self.btn_draw_fortune.setEnabled(False)
        self.fortune_drawn.emit(msg)

    def create_mood_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Header Info Card (7-Day Daily Aggregated Mental Wellness Summary)
        daily_records = self.db.get_daily_mood_summary(num_days=7)
        recorded_days = [d for d in daily_records if d.get("has_data")]
        total_convos = sum(d.get("count", 0) for d in recorded_days)
        avg_score = (
            sum(d["avg_score"] for d in recorded_days) / max(1, len(recorded_days))
            if recorded_days else 3.5
        )

        stat_card = QFrame()
        stat_card.setStyleSheet("""
            QFrame {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 10px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        s_layout = QHBoxLayout(stat_card)
        s_layout.setContentsMargins(12, 10, 12, 10)

        today_entry = next((d for d in daily_records if d.get("is_today") and d.get("has_data")), None)
        if today_entry:
            t_score = today_entry["avg_score"]
            s_left = QLabel(f"📈 <b>오늘 마음 날씨:</b> <span style='color: #2563EB; font-size: 14px;'><b>{t_score:.1f}</b> / 5.0</span> (주간 평균 {avg_score:.1f})")
        else:
            s_left = QLabel(f"📈 <b>주간 마음 날씨 평균:</b> <span style='color: #2563EB; font-size: 14px;'><b>{avg_score:.1f}</b> / 5.0</span>")
        s_left.setStyleSheet("color: #1E293B; font-size: 12px;")

        s_right = QLabel(f"🗓️ <b>7일 일별 케어</b> (기록 {len(recorded_days)}일 / 총 {total_convos}회)")
        s_right.setStyleSheet("color: #64748B; font-size: 11px;")

        s_layout.addWidget(s_left, 1)
        s_layout.addWidget(s_right, 0)
        layout.addWidget(stat_card)

        # Chart Frame (Single clean border)
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        c_layout = QVBoxLayout(chart_frame)
        c_layout.setContentsMargins(6, 6, 6, 6)

        chart_widget = MoodChartWidget(daily_records)
        c_layout.addWidget(chart_widget)
        layout.addWidget(chart_frame, 1)

        # Mood Tips footer (Single clean border)
        tip_card = QFrame()
        tip_card.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        t_layout = QVBoxLayout(tip_card)
        t_layout.setContentsMargins(10, 8, 10, 8)

        tip_lbl = QLabel("💡 <b>힐링 가이드:</b> AI 화분과 편안하게 대화를 나눌수록 마음의 피로도가 낮아지고 애정도가 증가합니다 🌿")
        tip_lbl.setStyleSheet("color: #475569; font-size: 11px;")
        tip_lbl.setWordWrap(True)
        t_layout.addWidget(tip_lbl)
        layout.addWidget(tip_card)

        return widget

    def create_achievements_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        unlocked = set(self.db.get_unlocked_achievements())
        total_count = len(ACHIEVEMENTS_100)
        unlocked_count = len(unlocked)
        pct = int((unlocked_count / max(1, total_count)) * 100)

        # 1. Header Progress Bar & Count
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 10px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(12, 10, 12, 10)
        h_layout.setSpacing(6)

        p_row = QHBoxLayout()
        progress_lbl = QLabel(f"🏆 <b>달성 업적:</b> <span style='color: #059669; font-size: 14px;'><b>{unlocked_count}</b> / {total_count}개</span> ({pct}%)")
        progress_lbl.setStyleSheet("color: #1E293B; font-size: 12px;")
        p_row.addWidget(progress_lbl, 1)

        prog_bar = QProgressBar()
        prog_bar.setRange(0, 100)
        prog_bar.setValue(pct)
        prog_bar.setTextVisible(False)
        prog_bar.setFixedHeight(8)
        prog_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E2E8F0;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 4px;
            }
        """)

        h_layout.addLayout(p_row)
        h_layout.addWidget(prog_bar)
        layout.addWidget(header_card)

        # 2. Filter Selector Row (Category + Status)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)

        cat_combo = QComboBox()
        cat_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                color: #334155;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                selection-background-color: #ECFDF5;
                selection-color: #065F46;
                padding: 4px;
            }
        """)
        for cat_id, cat_name in ACHIEVEMENT_CATEGORIES.items():
            cat_combo.addItem(cat_name, cat_id)

        status_combo = QComboBox()
        status_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                color: #334155;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                selection-background-color: #ECFDF5;
                selection-color: #065F46;
                padding: 4px;
            }
        """)
        status_combo.addItem("전체 상태 보기", "all")
        status_combo.addItem("달성 완료만 보기 ✅", "unlocked")
        status_combo.addItem("진행 중만 보기 🔒", "locked")

        filter_row.addWidget(QLabel("📂 <b>카테고리:</b>"), 0)
        filter_row.addWidget(cat_combo, 1)
        filter_row.addWidget(QLabel("상태:"), 0)
        filter_row.addWidget(status_combo, 1)
        layout.addLayout(filter_row)

        # 3. Scroll Area for 100 Achievements
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E2E8F0; border-radius: 8px; background: #FAFAFA; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(6, 6, 6, 6)
        scroll_layout.setSpacing(6)

        def populate_achievements():
            while scroll_layout.count():
                child = scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            sel_cat = cat_combo.currentData()
            sel_status = status_combo.currentData()

            visible_count = 0
            for ach in ACHIEVEMENTS_100:
                is_unlocked = ach["id"] in unlocked
                
                if sel_cat != "all" and ach.get("cat") != sel_cat:
                    continue
                if sel_status == "unlocked" and not is_unlocked:
                    continue
                if sel_status == "locked" and is_unlocked:
                    continue

                visible_count += 1
                a_card = QFrame()
                if is_unlocked:
                    a_card.setStyleSheet("""
                        QFrame {
                            background-color: #F0FDF4;
                            border: 1px solid #86EFAC;
                            border-radius: 8px;
                        }
                        QLabel {
                            border: none;
                            background: transparent;
                        }
                    """)
                else:
                    a_card.setStyleSheet("""
                        QFrame {
                            background-color: #F8FAFC;
                            border: 1px solid #E2E8F0;
                            border-radius: 8px;
                        }
                        QLabel {
                            border: none;
                            background: transparent;
                        }
                    """)
                
                a_layout = QHBoxLayout(a_card)
                a_layout.setContentsMargins(10, 7, 10, 7)
                a_layout.setSpacing(10)

                icon_lbl = QLabel(ach["icon"] if is_unlocked else "🔒")
                icon_lbl.setFixedWidth(28)
                icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_lbl.setStyleSheet("font-size: 20px; border: none; background: transparent;")
                
                title_text = f"<b>{ach['title']}</b>" if is_unlocked else f"<span style='color: #64748B;'>🔒 {ach['title']}</span>"
                desc_text = f"<span style='color: #475569; font-size: 11px;'>{ach['desc']}</span>" if is_unlocked else f"<span style='color: #94A3B8; font-size: 11px;'>{ach['desc']}</span>"
                info_lbl = QLabel(f"{title_text}<br>{desc_text}")
                info_lbl.setStyleSheet("font-size: 12px; border: none; background: transparent;")
                info_lbl.setWordWrap(True)

                status_lbl = QLabel("달성 완료 ✅" if is_unlocked else "도전 중 🔒")
                status_lbl.setFixedSize(80, 24)
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_unlocked:
                    status_lbl.setStyleSheet("color: #059669; font-weight: bold; font-size: 11px; background-color: #DCFCE7; border-radius: 4px; border: none;")
                else:
                    status_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; background-color: #F1F5F9; border-radius: 4px; border: none;")

                a_layout.addWidget(icon_lbl)
                a_layout.addWidget(info_lbl, 1)
                a_layout.addWidget(status_lbl, 0)
                scroll_layout.addWidget(a_card)

            if visible_count == 0:
                empty_lbl = QLabel("해당 필터에 해당하는 업적이 없습니다.")
                empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 30px;")
                scroll_layout.addWidget(empty_lbl)

            scroll_layout.addStretch()

        cat_combo.currentIndexChanged.connect(populate_achievements)
        status_combo.currentIndexChanged.connect(populate_achievements)

        populate_achievements()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        return widget

    def show_graduation_dialog(self):
        """Modal dialog displaying 5 plant species as visual image cards with full-bloom previews."""
        dlg = QDialog(self)
        dlg.setWindowTitle("🎓 화원 졸업 및 새 씨앗 심기")
        dlg.resize(540, 600)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
                font-family: 'Malgun Gothic', 'Segoe UI';
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        d_layout = QVBoxLayout(dlg)
        d_layout.setContentsMargins(18, 16, 18, 16)
        d_layout.setSpacing(10)

        # Header celebration banner
        h_card = QFrame()
        h_card.setStyleSheet("""
            QFrame {
                background-color: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 10px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        h_l = QVBoxLayout(h_card)
        h_l.setContentsMargins(12, 10, 12, 10)
        t_lbl = QLabel("🌸 <b>축하합니다! 영광의 6단계 만개를 달성했습니다!</b><br><span style='color: #047857; font-size: 11px;'>현재 화분을 화원에 영구 등록하고, 다음에 함께할 <b>새로운 씨앗 품종</b>을 아래 카드에서 선택해주세요.</span>")
        t_lbl.setStyleSheet("color: #065F46; font-size: 12px; line-height: 1.5;")
        h_l.addWidget(t_lbl)
        d_layout.addWidget(h_card)

        d_layout.addWidget(QLabel("🌱 <b>새로 심을 식물 품종 카드 선택:</b>"))

        # Scroll area for 5 species visual cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E2E8F0; border-radius: 8px; background: #FAFAFA; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(6, 6, 6, 6)
        scroll_layout.setSpacing(8)

        selected_species = ["sunflower"]
        card_widgets = {}

        completed_cnt, total_req = self.engine.get_species_unlock_progress("starlight_rose")

        def update_card_styles():
            for sp_id, (card, badge, is_unlocked) in card_widgets.items():
                if not is_unlocked:
                    card.setStyleSheet("""
                        QFrame {
                            background-color: #F1F5F9;
                            border: 1px dashed #CBD5E1;
                            border-radius: 10px;
                        }
                        QLabel {
                            border: none;
                            background: transparent;
                        }
                    """)
                    badge.setText("🔒 잠김")
                    badge.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 11px; background-color: #E2E8F0; border-radius: 6px; padding: 4px 8px; border: none;")
                    continue

                is_sel = (sp_id == selected_species[0])
                info = SPECIES_INFO.get(sp_id, {})
                is_secret = info.get("is_secret", False)

                if is_sel:
                    if is_secret:
                        card.setStyleSheet("""
                            QFrame {
                                background-color: #FAF5FF;
                                border: 2.5px solid #8B5CF6;
                                border-radius: 10px;
                            }
                            QLabel { border: none; background: transparent; }
                        """)
                        badge.setText("전설 선택됨 ✨")
                        badge.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; background-color: #8B5CF6; border-radius: 6px; padding: 4px 8px; border: none;")
                    else:
                        card.setStyleSheet("""
                            QFrame {
                                background-color: #ECFDF5;
                                border: 2px solid #10B981;
                                border-radius: 10px;
                            }
                            QLabel { border: none; background: transparent; }
                        """)
                        badge.setText("선택됨 ✨")
                        badge.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 11px; background-color: #10B981; border-radius: 6px; padding: 4px 8px; border: none;")
                else:
                    if is_secret:
                        card.setStyleSheet("""
                            QFrame {
                                background-color: #FDF4FF;
                                border: 1.5px solid #E879F9;
                                border-radius: 10px;
                            }
                            QFrame:hover { background-color: #FAE8FF; border-color: #C084FC; }
                            QLabel { border: none; background: transparent; }
                        """)
                        badge.setText("👑 전설 선택")
                        badge.setStyleSheet("color: #7E22CE; font-size: 11px; font-weight: bold; background-color: #F3E8FF; border-radius: 6px; padding: 4px 8px; border: none;")
                    else:
                        card.setStyleSheet("""
                            QFrame {
                                background-color: #FFFFFF;
                                border: 1px solid #E2E8F0;
                                border-radius: 10px;
                            }
                            QFrame:hover {
                                border-color: #CBD5E1;
                                background-color: #F8FAFC;
                            }
                            QLabel {
                                border: none;
                                background: transparent;
                            }
                        """)
                        badge.setText("선택하기")
                        badge.setStyleSheet("color: #64748B; font-size: 11px; background-color: #F1F5F9; border-radius: 6px; padding: 4px 8px; border: none;")

        for sp_id, info in SPECIES_INFO.items():
            is_unlocked = self.engine.is_species_unlocked(sp_id)
            card = QFrame()
            card.setCursor(Qt.CursorShape.PointingHandCursor if is_unlocked else Qt.CursorShape.ForbiddenCursor)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 12, 8)
            c_layout.setSpacing(12)

            # Left: Full-bloom Preview Image
            img_lbl = QLabel()
            img_lbl.setFixedSize(54, 54)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_path = get_resource_path(os.path.join("assets", f"stage_{sp_id}_6.png"))
            if os.path.exists(img_path):
                pm = QPixmap(img_path).scaled(52, 52, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(pm)
            else:
                img_lbl.setText(info["emoji"])
                img_lbl.setStyleSheet("font-size: 28px;")

            # Middle: Name & Desc
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            if info.get("is_secret"):
                if is_unlocked:
                    name_lbl = QLabel(f"<b>{info['emoji']} {info['name']}</b> <span style='font-size:10px; color:#7E22CE; background:#F3E8FF; padding:1px 5px; border-radius:4px;'>👑 전설 해금</span>")
                    name_lbl.setStyleSheet("font-size: 13px; color: #581C87;")
                    desc_lbl = QLabel(info["desc"])
                    desc_lbl.setStyleSheet("font-size: 11px; color: #6B21A8; font-weight: bold;")
                else:
                    name_lbl = QLabel(f"<b>{info['emoji']} {info['name']}</b> <span style='font-size:10px; color:#DC2626; background:#FEE2E2; padding:1px 5px; border-radius:4px;'>🔒 전설의 봉인</span>")
                    name_lbl.setStyleSheet("font-size: 13px; color: #64748B;")
                    desc_lbl = QLabel(f"🔒 5대 기본 품종을 모두 화원에 졸업시키면 봉인이 해제됩니다. (현재 {completed_cnt}/{total_req}종 졸업 완료)")
                    desc_lbl.setStyleSheet("font-size: 11px; color: #DC2626; font-weight: bold;")
            else:
                name_lbl = QLabel(f"<b>{info['emoji']} {info['name']}</b>")
                name_lbl.setStyleSheet("font-size: 13px; color: #1E293B;")
                desc_lbl = QLabel(info["desc"])
                desc_lbl.setStyleSheet("font-size: 11px; color: #64748B;")

            desc_lbl.setWordWrap(True)
            info_layout.addWidget(name_lbl)
            info_layout.addWidget(desc_lbl)

            # Right: Selection Badge
            badge_lbl = QLabel("선택하기")
            badge_lbl.setFixedSize(80, 26)
            badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            c_layout.addWidget(img_lbl, 0)
            c_layout.addLayout(info_layout, 1)
            c_layout.addWidget(badge_lbl, 0)

            # Click handler on card
            def make_click_handler(sid, unlocked):
                def handler(event):
                    if not unlocked:
                        return
                    selected_species[0] = sid
                    update_card_styles()
                return handler

            card.mousePressEvent = make_click_handler(sp_id, is_unlocked)
            card_widgets[sp_id] = (card, badge_lbl, is_unlocked)
            scroll_layout.addWidget(card)

        update_card_styles()
        scroll.setWidget(scroll_content)
        d_layout.addWidget(scroll, 1)

        # Name input
        name_box = QHBoxLayout()
        name_box.addWidget(QLabel("🏷️ <b>새 화분의 애칭:</b>"))
        name_edit = QLineEdit("초록이", dlg)
        name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                color: #1E293B;
            }
            QLineEdit:focus {
                border: 1.5px solid #10B981;
            }
        """)
        name_box.addWidget(name_edit, 1)
        d_layout.addLayout(name_box)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("취소", dlg)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 9px 18px;
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                font-size: 12px;
                color: #475569;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        btn_cancel.clicked.connect(dlg.reject)

        btn_ok = QPushButton("🎓 이 씨앗으로 심고 키우기! ✨", dlg)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                padding: 9px 22px;
                background-color: #10B981;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        def on_confirm():
            chosen_species = selected_species[0]
            new_name = name_edit.text().strip() or "초록이"
            self.engine.graduate_current_plant(chosen_species, new_name)
            self.plant_graduated.emit(chosen_species, new_name)
            dlg.accept()
            self.accept()

        btn_ok.clicked.connect(on_confirm)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        d_layout.addLayout(btn_row)

        dlg.exec()

    def accept(self):
        """Prevent default QDialog closing on Enter key."""
        pass

    def reject(self):
        self.hide()

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
