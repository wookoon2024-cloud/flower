import sys
import os
import random
import datetime
import ctypes
import ctypes.wintypes
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QApplication, QMenu
)
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QAction, QCursor, QPainter

from .bubble_widget import SpeechBubbleWidget
from .character_widget import PlantCharacterWidget
from .control_bar import ControlBarWidget
from .chat_dialog import ChatDialog
from .garden_dialog import GardenDialog
from .settings_dialog import SettingsDialog
from ..shop_data import PET_CATALOG, SAUCER_CATALOG
from ..ai_client import AIChatWorker, analyze_user_sentiment
from ..config import set_autostart_registry

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.UINT),
        ("dwTime", ctypes.wintypes.DWORD)
    ]

def get_idle_duration_sec() -> float:
    try:
        if sys.platform != "win32":
            return 0.0
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
    except Exception:
        pass
    return 0.0

class FloatingPlantWindow(QWidget):
    def __init__(self, plant_engine, db_manager, config_manager):
        super().__init__()
        self.engine = plant_engine
        self.db = db_manager
        self.config = config_manager
        
        self.drag_position = QPoint()
        self.is_dragging = False
        self.active_dialogs = []
        self._active_workers = []

        self.chat_dialog = None
        self.garden_dialog = None
        self.settings_dialog = None
        self.last_hourly_peek_hour = -1
        self.last_pet_bubble_time = None

        # Workload & Activity Empathy Monitor State
        self.active_work_seconds = 0
        self.idle_duration_accumulated = 0.0
        self.was_idle = False
        self.last_workload_nudge_time = None

        self.init_window()
        self.init_ui()
        self.init_signals()
        self.init_timers()
        self.apply_scale()

        # Initial greeting (4 seconds)
        QTimer.singleShot(800, self.initial_greeting)

    def init_window(self):
        # Frameless, Tool Window & Always-on-top so it stays on the topmost layer above taskbar & quickbars
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.config.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Base size scaled
        scale_pct = self.config.get("plant_scale", 100)
        s = max(60, min(160, scale_pct)) / 100.0
        w = max(240, int(240 * s))
        h = int(280 * s)
        self.setFixedSize(w, h)

        # Restore saved position if available
        px = self.config.get("window_pos_x", -1)
        py = self.config.get("window_pos_y", -1)
        if px > 0 and py > 0:
            self.move(px, py)
        else:
            # Default to bottom-right resting directly on the taskbar
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.width() - w - 15, screen.bottom() - h)

        # Ghost mode opacity
        if self.config.get("ghost_mode", False):
            self.setWindowOpacity(0.45)
        else:
            self.setWindowOpacity(1.0)

        # Sync Windows startup registry on boot
        if self.config.get("auto_start", True):
            set_autostart_registry(True)

    def init_ui(self):
        # 1. Speech Bubble Widget
        self.bubble = SpeechBubbleWidget(self)

        # 2. Control Bar Widget (Floating menu bar)
        self.control_bar = ControlBarWidget(self)
        self.control_bar.hide()

        # 3. Plant Character Widget
        scale_pct = self.config.get("plant_scale", 100)
        self.character = PlantCharacterWidget(self, scale_pct=scale_pct)
        self.character.set_species(self.engine.get_species())
        self.character.set_stage(self.engine.get_state().get("stage", 1))
        self.character.set_equipped_saucer(self.engine.get_equipped_saucer())
        self.character.set_equipped_pet(self.engine.get_equipped_pet())

    def apply_scale(self):
        scale_pct = self.config.get("plant_scale", 100)
        s = max(60, min(160, scale_pct)) / 100.0
        w = max(240, int(240 * s))
        h = max(290, int(290 * s))

        old_geo = self.geometry()
        old_bottom = old_geo.bottom() if old_geo.isValid() else -1

        self.setFixedSize(w, h)

        # 1. Bottom: Plant Character (sits at bottom of window spanning full width so pets walk on floor)
        char_w = w
        char_h = max(135, int(135 * s))
        char_x = 0
        char_y = h - char_h
        self.character.set_scale_and_size(scale_pct, char_w, char_h)
        self.character.setGeometry(char_x, char_y, char_w, char_h)

        # 2. Middle: Speech Bubble (sits right above plant leaves)
        bubble_w = min(w - 16, int(224 * s))
        bubble_h = max(60, int(68 * s))
        bubble_x = (w - bubble_w) // 2
        bubble_y = char_y - bubble_h + int(14 * s)
        self.bubble.setGeometry(bubble_x, bubble_y, bubble_w, bubble_h)

        # 3. Top: Control Bar (sits cleanly ABOVE the speech bubble)
        bar_w = min(w - 12, max(184, int(204 * s)))
        bar_h = max(52, int(58 * s))
        bar_x = (w - bar_w) // 2
        bar_y = max(4, bubble_y - bar_h - int(4 * s))
        self.control_bar.setGeometry(bar_x, bar_y, bar_w, bar_h)

        # Keep anchored to bottom screen edge during scaling
        if old_bottom > 0:
            self.move(self.x(), old_bottom - h + 1)
        self.update()

    def set_user_scale(self, scale_pct: int):
        self.config.set("plant_scale", scale_pct)
        self.apply_scale()
        self.update()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            curr_s = self.config.get("plant_scale", 100)
            if delta > 0:
                new_s = min(150, curr_s + 10)
            else:
                new_s = max(60, curr_s - 10)
            if new_s != curr_s:
                self.set_user_scale(new_s)
            event.accept()
        else:
            super().wheelEvent(event)

    def init_signals(self):
        # Engine Signals
        self.engine.state_changed.connect(self.on_engine_state_changed)
        self.engine.evolved.connect(self.on_plant_evolved)
        self.engine.warning_triggered.connect(self.on_plant_warning)
        self.engine.interaction_occurred.connect(self.on_plant_interaction)
        self.engine.achievement_unlocked.connect(self.on_achievement_unlocked)
        self.engine.item_equipped.connect(self.on_item_equipped)

        # Character Click & Eco Events & Pets
        self.character.clicked.connect(self.on_character_clicked)
        self.character.bug_cleared.connect(self.on_bug_cleared)
        self.character.pest_escaped.connect(self.on_pest_escaped)
        self.character.visitor_greeted.connect(self.on_visitor_greeted)
        self.character.eco_visitor_arrived.connect(self.on_eco_visitor_arrived)
        self.character.pet_clicked.connect(self.on_pet_clicked)

        # Control Bar Actions
        self.control_bar.water_clicked.connect(self.handle_water)
        self.control_bar.sun_clicked.connect(self.handle_sunlight)
        self.control_bar.chat_clicked.connect(self.open_chat_dialog)
        self.control_bar.garden_clicked.connect(self.open_garden_dialog)
        self.control_bar.settings_clicked.connect(self.open_settings_dialog)

    def on_item_equipped(self, item_type: str, item_id: str):
        """React to newly equipped saucer or pet."""
        if item_type == "saucer":
            self.character.set_equipped_saucer(item_id)
        elif item_type == "pet":
            self.character.set_equipped_pet(item_id)

    def on_pet_clicked(self, pet_id: str):
        """React to user clicking the animated pet companion."""
        pet_info = PET_CATALOG.get(pet_id)
        if pet_info and pet_info.get("dialogues"):
            speech = random.choice(pet_info["dialogues"])
            self.bubble.show_message(speech, 3)
            # Affection boost (+3)
            self.engine.state["affection"] = min(100, self.engine.state.get("affection", 0) + 3)
            self.engine.save()
            self.engine.state_changed.emit(self.engine.state)

    def on_character_clicked(self):
        """Show menu on click above pot and keep open for 6 seconds."""
        self.control_bar.show()
        self.control_bar.raise_()
        self.raise_()
        self.menu_auto_close_timer.start(6000) # 6 seconds auto-close
        self.engine.pet()

    def hide_menu_gracefully(self):
        """Auto-close menu if user is not currently hovering over it."""
        if self.control_bar.underMouse():
            self.menu_auto_close_timer.start(3000)
            return
        self.control_bar.hide()

    def init_timers(self):
        # Menu auto-close timer (6 seconds)
        self.menu_auto_close_timer = QTimer(self)
        self.menu_auto_close_timer.setSingleShot(True)
        self.menu_auto_close_timer.timeout.connect(self.hide_menu_gracefully)

        # Decay and Smart Peeking timer (every 1 minute)
        self.decay_timer = QTimer(self)
        self.decay_timer.timeout.connect(self.on_decay_timer_tick)
        self.decay_timer.start(60 * 1000)
        self.minutes_elapsed = 0

        # Gentle idle check & Proactive Speech timer (every 30 seconds)
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.on_idle_timer_tick)
        self.idle_timer.start(30 * 1000)

        # Workload & Activity Empathy Monitor Timer (every 15 seconds)
        self.workload_timer = QTimer(self)
        self.workload_timer.timeout.connect(self.on_workload_monitor_tick)
        self.workload_timer.start(15 * 1000)

        self.last_user_interaction_time = datetime.datetime.now()
        self.notified_proactive_events = set()

    def on_decay_timer_tick(self):
        self.minutes_elapsed += 1
        interval = self.config.get("decay_interval_minutes", 30)
        if self.minutes_elapsed >= interval:
            self.minutes_elapsed = 0
            self.engine.tick_decay()

        # Hourly Routine Peeking with exact clock announcement
        if self.config.get("hourly_peek", True):
            now = datetime.datetime.now()
            if now.minute == 0 and now.hour != self.last_hourly_peek_hour:
                self.last_hourly_peek_hour = now.hour
                announcement = self.engine.get_hourly_time_announcement()
                self.bubble.show_message(announcement, 4)

    def on_idle_timer_tick(self):
        if not self.config.get("proactive_speech", True):
            return

        try:
            now = datetime.datetime.now()
            today = datetime.date.today().isoformat()
            state = self.engine.get_state()

            # 1. Low Water / Low Sunlight State Triggers (< 20%)
            if state.get("water", 80) < 20:
                if "water_low" not in self.notified_proactive_events:
                    self.notified_proactive_events.add("water_low")
                    self.trigger_proactive_speech("thirsty")
            elif state.get("water", 80) >= 35 and "water_low" in self.notified_proactive_events:
                self.notified_proactive_events.remove("water_low")

            if state.get("sunlight", 80) < 20:
                if "sun_low" not in self.notified_proactive_events:
                    self.notified_proactive_events.add("sun_low")
                    self.trigger_proactive_speech("hungry_sun")
            elif state.get("sunlight", 80) >= 35 and "sun_low" in self.notified_proactive_events:
                self.notified_proactive_events.remove("sun_low")

            # 2. Specific Time Triggers (12:00 Lunch, 15:30 Afternoon Care, 18:00 Leaving, 21:00 Overtime)
            if now.hour == 12 and now.minute <= 15:
                if f"lunch_{today}" not in self.notified_proactive_events:
                    self.notified_proactive_events.add(f"lunch_{today}")
                    self.trigger_proactive_speech("lunch")

            elif now.hour == 15 and 25 <= now.minute <= 45:
                if f"afternoon_{today}" not in self.notified_proactive_events:
                    self.notified_proactive_events.add(f"afternoon_{today}")
                    self.trigger_proactive_speech("afternoon_care")

            elif now.hour == 18 and now.minute <= 15:
                if f"leave_{today}" not in self.notified_proactive_events:
                    self.notified_proactive_events.add(f"leave_{today}")
                    self.trigger_proactive_speech("leave_work")

            elif now.hour >= 21 and now.minute <= 15:
                if f"overtime_{today}" not in self.notified_proactive_events:
                    self.notified_proactive_events.add(f"overtime_{today}")
                    self.trigger_proactive_speech("overtime")

            # 3. 1~2 Hours Random Idle Nudge Trigger (No interaction for configured minutes)
            idle_minutes = (now - self.last_user_interaction_time).total_seconds() / 60.0
            nudge_thresh = self.config.get("proactive_idle_minutes", 90)
            if idle_minutes >= nudge_thresh:
                self.last_user_interaction_time = now
                self.trigger_proactive_speech("idle_nudge")

        except Exception as e:
            print(f"[FloatingPlantWindow] on_idle_timer_tick error: {e}")

    def enterEvent(self, event):
        if self.config.get("ghost_mode", False):
            self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.config.get("ghost_mode", False):
            self.setWindowOpacity(0.45)
        super().leaveEvent(event)

    def initial_greeting(self):
        time_msg = self.engine.get_time_of_day_greeting()
        self.bubble.show_message(f"{time_msg}", 4)

    # --- Interaction Handlers ---
    def handle_water(self):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            self.menu_auto_close_timer.start(6000)

            # Special Eco Interaction: If Bee is currently visiting, reward extra bonus!
            if self.character.eco_visitor and self.character.eco_visitor.alive and self.character.eco_visitor.v_type == "bee":
                self.character.eco_visitor.flee()
                self.engine.give_water()
                self.engine.on_eco_visitor_interacted("bee")
                for _ in range(4):
                    self.character.spawn_particle("drop")
                self.character.spawn_particle("heart")
                self.bubble.show_message("🐝 꿀벌이 시원한 물을 함께 마시고 꿀을 가득 선물하며 날아갔어요! 🍯✨ (+30 EXP)", 4)
                return

            success, msg = self.engine.give_water()
            self.character.spawn_particle("drop")
            self.bubble.show_message(msg, 3)
        except Exception as e:
            print(f"[FloatingPlantWindow] handle_water error: {e}")

    def handle_sunlight(self):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            self.menu_auto_close_timer.start(6000)
            success, msg = self.engine.give_sunlight()
            self.character.spawn_particle("sun")
            self.bubble.show_message(msg, 3)
        except Exception as e:
            print(f"[FloatingPlantWindow] handle_sunlight error: {e}")

    def on_workload_monitor_tick(self):
        """Monitors user continuous keyboard/mouse workload intensity using Win32 API and provides caring empathy nudges."""
        try:
            idle_sec = get_idle_duration_sec()
            user_name = self.config.get("user_nickname", "공직자님")
            now = datetime.datetime.now()

            # Active work (< 45 sec since last keystroke/mouse action)
            if idle_sec < 45.0:
                if self.was_idle:
                    self.was_idle = False
                    # Return from idle greeting if idle was >= 5 minutes (300s)
                    if self.idle_duration_accumulated >= 300.0:
                        self.idle_duration_accumulated = 0.0
                        return_greetings = [
                            f"{user_name}, 자리 비우셨다가 돌아오셨군요! 기다리고 있었어요 🌱 오늘도 화이팅!",
                            f"어서오세요, {user_name}! 따뜻한 물 한잔 챙겨오셨나요? ☕",
                            f"{user_name}, 반가워요! 다시 함께 열일 모드로 힘내봐요 ✨"
                        ]
                        self.character.spawn_particle("heart")
                        self.bubble.show_message(random.choice(return_greetings), 4)

                self.active_work_seconds += 15
                self.idle_duration_accumulated = 0.0

                # Continuous intensive work for 30 minutes (1800s) without resting
                if self.active_work_seconds >= 1800:
                    if not self.last_workload_nudge_time or (now - self.last_workload_nudge_time).total_seconds() > 2100: # 35 min cooldown
                        self.last_workload_nudge_time = now
                        self.active_work_seconds = 0
                        nudge_messages = [
                            f"{user_name}, 타자 치시는 손길이 정말 분주하시네요! 오늘 업무가 많이 몰리셨나요? 잠시 1분만 기지개 켜고 손목을 가볍게 털어주세요 🍵✨",
                            f"열심히 몰입하시는 모습이 정말 멋져요, {user_name}! 그래도 눈 건강을 위해 10초간 먼 곳을 바라보고 시원한 물 한 모금 드세요 🌸",
                            f"30분 넘게 쉼 없이 달리고 계시네요! {user_name}, 어깨 한번 으쓱~ 펴시고 심호흡 한번 하실까요? 🍃💖",
                            f"{user_name}의 노고를 제가 늘 곁에서 지켜보며 응원하고 있어요! 무리하지 마시고 잠시 30초만 눈을 감고 쉬어가요 ☕"
                        ]
                        self.character.spawn_particle("sweat")
                        self.bubble.show_message(random.choice(nudge_messages), 6)
            else:
                # User is away / idle
                self.was_idle = True
                self.idle_duration_accumulated += 15.0
                self.active_work_seconds = 0
        except Exception as e:
            print(f"[FloatingPlantWindow] on_workload_monitor_tick error: {e}")

    def on_eco_visitor_arrived(self, v_type: str):
        try:
            visitor_lines = {
                "bee": "🐝 윙윙~ 꿀벌 친구가 찾아왔어요! 꿀을 만드느라 목이 마르대요~ 💧",
                "bug": "🐛 앗! 나뭇잎에 애벌레가 나타났어요! 방치하면 잎을 갉아먹으니 얼른 클릭해서 쫓아내주세요! 🚨",
                "aphid": "🌱 앗! 진딧물 무리가 잎에 달라붙었어요! 방치하면 경험치가 깎이니 어서 클릭하세요! 🚨",
                "snail": "🐌 앗! 잎을 갉아먹는 달팽이가 올라오고 있어요! 얼른 클릭해서 쫓아내주세요! 🚨",
                "locust": "🦗 앗! 풀밭 메뚜기가 잎을 노리고 있어요! 도망가기 전에 클릭하세요! 🚨",
                "butterfly": "🦋 예쁜 나비가 찾아와 살랑살랑 쉬어가고 있어요 🌸",
                "ladybug": "🐞 행운을 부르는 칠성무당벌레가 화분을 찾아왔어요! 🍀",
                "bird": "🐦 짹짹~ 귀여운 아기 파랑새가 가지에 살포시 앉았어요 ✨",
                "cat_paw": "🐾 앗! 장난꾸러기 고양이 발이 빼꼼 나타났어요! 냥~ 🐱",
                "rain_cloud": "🌧️ 촉촉한 단비 구름이 지나가며 잎사귀를 적셔주고 있어요 🌈",
                "firefly": "✨ 반짝반짝 반딧불이들이 춤추며 화분을 밝혀주고 있어요 🌌",
                "ant": "🐜 영양분을 물고 온 부지런한 개미 친구를 만났어요! 🌾",
                "frog": "🐸 개굴개굴~ 귀여운 초록 청개구리가 놀러왔어요! 🌿",
                "squirrel": "🐿️ 볼이 빵빵한 도토리 다람쥐가 화분 옆에 멈춰 섰어요! 🌰",
                "shooting_star": "🌠 밤하늘의 소원 별똥별이 떨어졌어요! 오늘 하루도 소원성취 ✨",
                "forest_fairy": "🧚 숲의 요정이 찾아와 반짝이는 축복 가루를 뿌려주고 있어요 🌟",
                "puppy_nose": "🐕 킁킁! 사랑스러운 댕댕이가 반갑게 인사를 건네요 🐾",
                "dandelion": "🌾 바람을 타고 포근한 민들레 홀씨가 둥실 날아왔어요 🍃",
                "coffee": "☕ 향긋한 커피 한 잔의 여유! 잠시 피로를 녹여보세요 🍵",
                "heart_balloon": "🎈 둥실둥실 사랑의 하트 풍선이 화분 위로 떠올랐어요 💖"
            }
            line = visitor_lines.get(v_type, f"🌿 자연의 친구 {v_type}가 찾아왔어요! ✨")
            self.bubble.show_message(line, 5)

            if v_type == "rain_cloud":
                self.engine.on_eco_visitor_interacted("rain_cloud")
                self.character.spawn_particle("drop")
        except Exception as e:
            print(f"[FloatingPlantWindow] on_eco_visitor_arrived error: {e}")

    def on_bug_cleared(self, pest_type: str = "bug"):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            success, msg = self.engine.on_bug_cleared(pest_type)
            self.control_bar.update_status(self.engine.get_state())
            for _ in range(4):
                self.character.spawn_particle("sparkle")
            self.bubble.show_message(msg, 4)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_bug_cleared error: {e}")

    def on_pest_escaped(self, pest_type: str):
        try:
            success, msg = self.engine.on_pest_escaped(pest_type)
            self.control_bar.update_status(self.engine.get_state())
            self.character.spawn_particle("sweat")
            self.bubble.show_message(msg, 5)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_pest_escaped error: {e}")

    def on_visitor_greeted(self, v_type: str):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            success, msg = self.engine.on_eco_visitor_interacted(v_type)
            self.control_bar.update_status(self.engine.get_state())
            for _ in range(4):
                self.character.spawn_particle("heart")
            self.bubble.show_message(msg, 4)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_visitor_greeted error: {e}")

    def on_engine_state_changed(self, state: dict):
        try:
            self.character.set_species(self.engine.get_species())
            self.character.set_stage(state.get("stage", 1))
            self.control_bar.update_status(state)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_engine_state_changed error: {e}")

    def on_plant_evolved(self, new_stage: int, message: str):
        try:
            self.character.set_species(self.engine.get_species())
            self.character.set_stage(new_stage)
            self.bubble.show_message(message, 5)
            for _ in range(6):
                self.character.spawn_particle("heart")
        except Exception as e:
            print(f"[FloatingPlantWindow] on_plant_evolved error: {e}")

    def on_plant_warning(self, message: str):
        try:
            self.bubble.show_message(message, 4)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_plant_warning error: {e}")

    def on_plant_interaction(self, action_name: str, bubble_text: str):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            if action_name == "pet":
                self.character.spawn_particle("heart")
                now = datetime.datetime.now()
                # Show speech bubble comfortably (at least 20s gap or 35% chance so it never spams!)
                should_show = False
                if not self.last_pet_bubble_time or (now - self.last_pet_bubble_time).total_seconds() > 20:
                    should_show = True
                elif random.random() < 0.35:
                    should_show = True

                if should_show:
                    self.last_pet_bubble_time = now
                    self.bubble.show_message(bubble_text, 3)
            else:
                self.bubble.show_message(bubble_text, 3)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_plant_interaction error: {e}")

    def on_achievement_unlocked(self, ach: dict):
        try:
            for _ in range(5):
                self.character.spawn_particle("heart")
            self.bubble.show_message(f"🏆 업적 달성! [{ach.get('title')}] 뱃지 획득! ✨", 5)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_achievement_unlocked error: {e}")

    # --- AI Chat Handling ---
    def open_chat_dialog(self):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            self.menu_auto_close_timer.stop()
            self.control_bar.hide()
            self.bubble.hide_bubble()  # Close speech bubble when opening chat dialog
            if self.chat_dialog is not None:
                try:
                    self.chat_dialog.close()
                    self.chat_dialog.deleteLater()
                except Exception:
                    pass
                self.chat_dialog = None

            self.chat_dialog = ChatDialog(self.db, self.config, None)
            self.chat_dialog.message_sent.connect(self.start_ai_chat)
            self.chat_dialog.refresh_header()
            self.chat_dialog.load_history()
            
            self.chat_dialog.setWindowState(
                (self.chat_dialog.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive
            )
            self.chat_dialog.show()
            self.chat_dialog.raise_()
            self.chat_dialog.activateWindow()
            print("[FloatingPlantWindow] ChatDialog opened successfully.")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[FloatingPlantWindow] open_chat_dialog ERROR:\n{tb}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "대화창 실행 오류",
                f"대화창을 여는 도중 오류가 발생했습니다.\n\n오류 내용:\n{e}\n\n상세 정보는 mindkeeper_debug.log 파일을 확인해주세요."
            )

    # --- Garden & Collection Dialog ---
    def open_garden_dialog(self):
        try:
            print("[FloatingPlantWindow] Opening GardenDialog...")
            self.last_user_interaction_time = datetime.datetime.now()
            self.menu_auto_close_timer.stop()
            self.control_bar.hide()
            if self.garden_dialog is not None:
                try:
                    self.garden_dialog.close()
                    self.garden_dialog.deleteLater()
                except Exception:
                    pass
                self.garden_dialog = None

            self.garden_dialog = GardenDialog(self.engine, self.db, self.config, None)
            self.garden_dialog.plant_graduated.connect(self.on_plant_graduated)
            self.garden_dialog.fortune_drawn.connect(self.on_fortune_drawn)
            
            self.garden_dialog.setWindowState(
                (self.garden_dialog.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive
            )
            self.garden_dialog.show()
            self.garden_dialog.raise_()
            self.garden_dialog.activateWindow()
            print("[FloatingPlantWindow] GardenDialog opened successfully.")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[FloatingPlantWindow] open_garden_dialog ERROR:\n{tb}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "도감 실행 오류",
                f"나의 화원 & 도감 창을 여는 도중 오류가 발생했습니다.\n\n오류 내용:\n{e}\n\n상세 정보는 mindkeeper_debug.log 파일을 확인해주세요."
            )

    def on_plant_graduated(self, new_species: str, new_name: str):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            self.character.set_species(new_species)
            self.character.set_stage(1)
            self.control_bar.update_status(self.engine.get_state())
            for _ in range(6):
                self.character.spawn_particle("heart")
            self.bubble.show_message(f"🎓 축하합니다! 새로운 {new_name} 화분을 키우기 시작했어요! 🌱", 5)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_plant_graduated error: {e}")

    def on_fortune_drawn(self, msg: str):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            self.character.spawn_particle("sun")
            self.bubble.show_message(f"🥠 {msg}", 4)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_fortune_drawn error: {e}")

    def _stop_existing_workers(self):
        """Safely stops and joins any ongoing background AI worker threads."""
        for w in list(self._active_workers):
            try:
                w.stop()
                w.quit()
                w.wait(400)
            except Exception:
                pass
        self._active_workers.clear()

    def start_ai_chat(self, user_text: str):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            # Stop previous worker if still running
            self._stop_existing_workers()

            # 1. Extract recent history BEFORE saving current message
            history = self.db.get_recent_chat_history(limit=6)

            # 2. Save sentiment analysis and user message
            mood_type, score = analyze_user_sentiment(user_text)
            self.db.add_mood_entry(mood_type, score, user_text)
            self.db.add_chat_message("user", user_text)

            # 3. Refresh chat dialog immediately so user message appears on the right
            is_chat_open = bool(self.chat_dialog and self.chat_dialog.isVisible())
            if self.chat_dialog:
                self.chat_dialog.load_history()

            # 4. Only stream to widget speech bubble if chat dialog is NOT open
            if not is_chat_open:
                self.bubble.start_streaming()

            # 5. Start async AI worker thread safely with parent=self
            worker = AIChatWorker(
                config=dict(self.config.config),
                plant_state=dict(self.engine.get_state()),
                chat_history=list(history),
                user_message=user_text,
                parent=self
            )
            self._active_workers.append(worker)
            if not is_chat_open:
                worker.chunk_received.connect(self.bubble.append_chunk)
            worker.response_received.connect(self.on_ai_response_received)
            worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
            worker.start()
        except Exception as e:
            print(f"[FloatingPlantWindow] start_ai_chat error: {e}")
            if self.chat_dialog:
                self.chat_dialog.set_loading(False)

    def trigger_proactive_speech(self, mode: str):
        """Triggers autonomous speech by the plant (Thirst, Sunlight, 1~2hr Idle Nudge, Lunch, Leaving)."""
        if not self.config.get("proactive_speech", True):
            return
        is_chat_open = bool(self.chat_dialog and self.chat_dialog.isVisible())
        try:
            self._stop_existing_workers()
            if not is_chat_open:
                self.bubble.start_streaming()
            history = self.db.get_recent_chat_history(limit=6)
            worker = AIChatWorker(
                config=dict(self.config.config),
                plant_state=dict(self.engine.get_state()),
                chat_history=list(history),
                user_message="",
                proactive_mode=mode,
                parent=self
            )
            self._active_workers.append(worker)
            if not is_chat_open:
                worker.chunk_received.connect(self.bubble.append_chunk)
            worker.response_received.connect(self.on_proactive_response_received)
            worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
            worker.start()
        except Exception as e:
            print(f"[FloatingPlantWindow] trigger_proactive_speech error: {e}")

    def on_proactive_response_received(self, reply_text: str, is_fallback: bool, action_tags: list):
        try:
            self.db.add_chat_message("assistant", reply_text)
            is_chat_open = bool(self.chat_dialog and self.chat_dialog.isVisible())
            if not is_chat_open:
                self.bubble.finish_streaming(reply_text, self.config.get("bubble_duration_sec", 5))
            else:
                self.bubble.hide_bubble()

            self.character.spawn_particle("heart")
            if self.chat_dialog:
                self.chat_dialog.load_history()
        except Exception as e:
            print(f"[FloatingPlantWindow] on_proactive_response_received error: {e}")

    def _on_worker_finished(self, worker):
        try:
            worker.wait(300)
            if worker in self._active_workers:
                self._active_workers.remove(worker)
        except Exception:
            pass

    def cleanup_threads(self):
        """Gracefully wait for all background worker threads before shutdown."""
        self._stop_existing_workers()

    def closeEvent(self, event):
        self.cleanup_threads()
        super().closeEvent(event)

    def on_ai_response_received(self, reply_text: str, is_fallback: bool, action_tags: list):
        try:
            self.db.add_chat_message("assistant", reply_text)
            if self.chat_dialog:
                self.chat_dialog.set_loading(False)
                self.chat_dialog.load_history()

            self.engine.on_chat_completed()

            # In-Chat Interactive Actions (Water / Sun / Pet)
            if "water" in action_tags:
                self.engine.give_water()
                self.character.spawn_particle("drop")
            if "sun" in action_tags:
                self.engine.give_sunlight()
                self.character.spawn_particle("sun")
            if "pet" in action_tags:
                self.engine.pet()
                self.character.spawn_particle("heart")

            # Only show speech bubble on the widget if the chat dialog is NOT open!
            is_chat_open = bool(self.chat_dialog and self.chat_dialog.isVisible())
            if not is_chat_open:
                self.bubble.finish_streaming(reply_text, self.config.get("bubble_duration_sec", 5))
            else:
                self.bubble.hide_bubble()
        except Exception as e:
            print(f"[FloatingPlantWindow] on_ai_response_received error: {e}")

    # --- Settings Dialog ---
    def open_settings_dialog(self):
        try:
            self.menu_auto_close_timer.stop()
            self.control_bar.hide()
            if self.settings_dialog is not None:
                try:
                    self.settings_dialog.close()
                    self.settings_dialog.deleteLater()
                except Exception:
                    pass
                self.settings_dialog = None

            self.settings_dialog = SettingsDialog(self.config, None)
            self.settings_dialog.settings_saved.connect(self.apply_settings_changes)
            self.settings_dialog.clear_chat_requested.connect(self.on_clear_chat)
            self.settings_dialog.reset_plant_requested.connect(self.on_reset_plant)
            
            self.settings_dialog.setWindowState(
                (self.settings_dialog.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive
            )
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
        except Exception as e:
            print(f"[FloatingPlantWindow] open_settings_dialog error: {e}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

    def apply_settings_changes(self):
        always_on_top = self.config.get("always_on_top", True)
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        if self.config.get("ghost_mode", False) and not self.underMouse():
            self.setWindowOpacity(0.45)
        else:
            self.setWindowOpacity(1.0)

        self.apply_scale()
        self.show()
        if always_on_top:
            self.raise_()
            self.activateWindow()

        if self.chat_dialog:
            self.chat_dialog.refresh_header()

        self.control_bar.update_status(self.engine.get_state())

    def on_clear_chat(self):
        self.db.clear_chat_history()
        if self.chat_dialog:
            self.chat_dialog.load_history()

    def on_reset_plant(self):
        self.engine.reset_state()
        self.bubble.show_message("화분이 1단계 새싹으로 다시 태어났어요! 🌱", 4)

    # --- Mouse Drag & Magnetic Snapping & Context Menu ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.drag_start_pos = event.globalPosition().toPoint()
            self.window_start_pos = self.pos()
            self.raise_()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            curr_pos = event.globalPosition().toPoint()
            if not hasattr(self, 'drag_start_pos') or self.drag_start_pos is None:
                self.drag_start_pos = curr_pos
                self.window_start_pos = self.pos()

            # Only start dragging if mouse moved beyond threshold (5px)
            if not self.is_dragging:
                if (curr_pos - self.drag_start_pos).manhattanLength() > 5:
                    self.is_dragging = True
                    self.menu_auto_close_timer.stop()
                    if self.control_bar.isVisible():
                        self.control_bar.hide()
                    if self.bubble.isVisible():
                        self.bubble.hide()

            if self.is_dragging:
                target_x = self.window_start_pos.x() + (curr_pos.x() - self.drag_start_pos.x())
                target_y = self.window_start_pos.y() + (curr_pos.y() - self.drag_start_pos.y())

                # Magnetic Snapping to Taskbar, Quickbar and Screen Edges (자석 스냅)
                screen = QApplication.screenAt(curr_pos) or QApplication.primaryScreen()
                if screen:
                    avail = screen.availableGeometry()
                    snap_dist = 28 # Pixel distance to trigger magnetic snap

                    # 1. Bottom edge (Taskbar / Dock top surface): bottom of pot is at Y = height (0 gap!)
                    if abs((target_y + self.height()) - avail.bottom()) <= snap_dist:
                        target_y = avail.bottom() - self.height()
                    
                    # 2. Right edge
                    if abs((target_x + self.width()) - avail.right()) <= snap_dist:
                        target_x = avail.right() - self.width() + 1

                    # 3. Left edge
                    if abs(target_x - avail.left()) <= snap_dist:
                        target_x = avail.left()

                    # 4. Top edge
                    if abs(target_y - avail.top()) <= snap_dist:
                        target_y = avail.top()

                self.move(target_x, target_y)
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_dragging:
                # Direct click on floating window -> trigger menu show!
                self.on_character_clicked()
            self.is_dragging = False
            self.raise_()
            # Save position
            pos = self.pos()
            self.config.set("window_pos_x", pos.x(), auto_save=False)
            self.config.set("window_pos_y", pos.y(), auto_save=True)
            event.accept()

    def show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 4px;
                font-family: 'Malgun Gothic', 'Segoe UI';
                font-size: 12px;
            }
            QMenu::item {
                background-color: transparent;
                color: #1E293B;
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #ECFDF5;
                color: #065F46;
            }
            QMenu::item:disabled {
                color: #94A3B8;
            }
            QMenu::separator {
                height: 1px;
                background-color: #E2E8F0;
                margin: 4px 6px;
            }
        """)

        action_chat = menu.addAction("💬 대화하기")
        action_chat.triggered.connect(self.open_chat_dialog)

        action_water = menu.addAction("💧 물주기")
        action_water.triggered.connect(self.handle_water)

        action_sun = menu.addAction("☀️ 햇빛쬐기")
        action_sun.triggered.connect(self.handle_sunlight)

        action_pet = menu.addAction("💕 쓰다듬기")
        action_pet.triggered.connect(self.engine.pet)

        action_garden = menu.addAction("🌿 나의 화원 & 마음 도감")
        action_garden.triggered.connect(self.open_garden_dialog)

        menu.addSeparator()

        # Dynamic Scale submenu
        scale_menu = menu.addMenu("🔍 화분 크기 조절")
        scale_menu.setStyleSheet(menu.styleSheet())
        curr_s = self.config.get("plant_scale", 100)
        scale_options = [
            ("75% (아주 아담한 미니 화분)", 75),
            ("85% (약간 작게)", 85),
            ("100% (표준 크기 - 기본)", 100),
            ("115% (약간 크게)", 115),
            ("130% (크게 보기)", 130),
            ("150% (시원한 대형 화분)", 150)
        ]
        for label, s_val in scale_options:
            act = scale_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(curr_s == s_val)
            def make_handler(v):
                return lambda: self.set_user_scale(v)
            act.triggered.connect(make_handler(s_val))

        ontop_action = menu.addAction("📌 항상 위에 고정")
        ontop_action.setCheckable(True)
        ontop_action.setChecked(self.config.get("always_on_top", True))
        ontop_action.triggered.connect(self.toggle_always_on_top)

        autostart_action = menu.addAction("🚀 윈도우 시작 시 자동 실행")
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.config.get("auto_start", True))
        autostart_action.triggered.connect(self.toggle_auto_start)

        action_settings = menu.addAction("⚙️ 환경 설정")
        action_settings.triggered.connect(self.open_settings_dialog)

        action_log = menu.addAction("📋 실행 로그 확인 (디버그)")
        action_log.triggered.connect(self.open_log_file)

        menu.addSeparator()

        action_close = menu.addAction("❌ 위젯 종료")
        action_close.triggered.connect(QApplication.quit)

        menu.exec(global_pos)

    def open_log_file(self):
        import os
        import sys
        import subprocess
        from ..config import get_base_dir
        log_path = os.path.join(get_base_dir(), "mindkeeper_debug.log")
        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== 마음지킴이 로그 (생성됨: {datetime.datetime.now()}) ===\n")
        try:
            if sys.platform == "win32":
                os.startfile(log_path)
            else:
                subprocess.Popen(["notepad", log_path])
        except Exception as e:
            print(f"[FloatingPlantWindow] open_log_file error: {e}")

    def toggle_always_on_top(self):
        new_val = not self.config.get("always_on_top", True)
        self.config.set("always_on_top", new_val)
        self.apply_settings_changes()

    def toggle_auto_start(self):
        new_val = not self.config.get("auto_start", True)
        self.config.set("auto_start", new_val)
        set_autostart_registry(new_val)
        if new_val:
            self.bubble.show_message("🚀 윈도우 시작 시 자동 실행이 설정되었어요!", 4)
        else:
            self.bubble.show_message("윈도우 시작 시 자동 실행이 해제되었어요.", 3)
