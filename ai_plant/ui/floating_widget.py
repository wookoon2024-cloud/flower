"""
Floating Plant Window (Main UI)
Frameless, translucent, HWND_TOPMOST floating desktop widget.
Supports dynamic size scaling (70% ~ 150%) via settings dialog, right-click menu, or Ctrl+MouseWheel zoom!
Bottom-aligned flowerpot design for 0-gap pixel-perfect taskbar & dock contact.
"""
import ctypes
import datetime
from PySide6.QtWidgets import QWidget, QMenu, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPainter

from .bubble_widget import SpeechBubbleWidget
from .character_widget import PlantCharacterWidget
from .control_bar import ControlBarWidget
from .chat_dialog import ChatDialog
from .garden_dialog import GardenDialog
from .settings_dialog import SettingsDialog
from ..ai_client import AIChatWorker, analyze_user_sentiment

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_system_idle_seconds() -> float:
    """Returns seconds since last keyboard or mouse activity on Windows."""
    try:
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
        self.ai_worker = None
        self._active_workers = []

        self.chat_dialog = None
        self.garden_dialog = None
        self.settings_dialog = None

        self.last_hourly_peek_hour = -1
        self.idle_notified = False

        self.init_window()
        self.init_ui()
        self.init_signals()
        self.init_timers()
        self.apply_scale()

        # Initial greeting (4 seconds)
        QTimer.singleShot(800, self.initial_greeting)
        QTimer.singleShot(500, self.force_topmost)

    def force_topmost(self):
        """Forces the window to the absolute highest Z-order above all toolbars, docks, and taskbars."""
        if not self.config.get("always_on_top", True):
            return
        try:
            hwnd = int(self.winId())
            # HWND_TOPMOST = -1, SWP_NOSIZE(1) | SWP_NOMOVE(2) | SWP_NOACTIVATE(16) | SWP_SHOWWINDOW(64)
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0053)
        except Exception:
            pass

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

    def init_ui(self):
        # 1. Top: Speech Bubble
        self.bubble = SpeechBubbleWidget(self)

        # 2. Middle: Control Bar (initially hidden, pops up above pot on click)
        self.control_bar = ControlBarWidget(self)
        self.control_bar.update_status(self.engine.get_state())
        self.control_bar.hide()

        # 3. Bottom: Plant Character (sits at absolute bottom)
        self.character = PlantCharacterWidget(self, scale_pct=self.config.get("plant_scale", 100))
        self.character.set_species(self.engine.get_species())
        self.character.set_stage(self.engine.get_state().get("stage", 1))

    def apply_scale(self):
        """Dynamically resize window and scale components cleanly with perfect horizontal centering (100% baseline = 120px pot)."""
        scale_pct = self.config.get("plant_scale", 100)
        s = max(60, min(160, scale_pct)) / 100.0
        w = max(240, int(240 * s))
        h = int(280 * s)

        old_geo = self.geometry()
        old_bottom = old_geo.bottom() if old_geo.isValid() else -1

        self.setFixedSize(w, h)

        # Center speech bubble horizontally with top margin (Y=6s..78s)
        w_b = min(w - 12, int(224 * s))
        h_b = int(72 * s)
        self.bubble.setGeometry((w - w_b) // 2, int(6 * s), w_b, h_b)

        # Center control bar horizontally with clean separation below bubble (Y=82s..140s)
        w_c = min(w - 12, int(184 * s))
        h_c = int(58 * s)
        self.control_bar.setGeometry((w - w_c) // 2, int(82 * s), w_c, h_c)

        # Center character horizontally at bottom (Y=160s..280s)
        char_sz = int(120 * s)
        char_x = (w - char_sz) // 2
        char_y = h - char_sz
        self.character.setGeometry(char_x, char_y, char_sz, char_sz)
        self.character.set_scale(scale_pct)

        # Keep anchored to bottom surface
        if old_bottom > 0:
            self.move(self.x(), old_bottom - h + 1)
        self.update()

    def set_user_scale(self, scale_pct: int):
        """Set scale and save to config."""
        self.config.set("plant_scale", scale_pct)
        self.apply_scale()
        self.bubble.show_message(f"화분 크기가 {scale_pct}%로 조절되었어요! 🌱", 3)

    def wheelEvent(self, event):
        """Ctrl + Mouse Wheel to zoom/scale plant size seamlessly."""
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

        # Character Click: Petting + Show Menu for 6 seconds
        self.character.clicked.connect(self.on_character_clicked)
        self.character.bug_cleared.connect(self.on_bug_cleared)
        self.character.visitor_greeted.connect(self.on_visitor_greeted)
        self.character.eco_visitor_arrived.connect(self.on_eco_visitor_arrived)

        # Control Bar Actions
        self.control_bar.water_clicked.connect(self.handle_water)
        self.control_bar.sun_clicked.connect(self.handle_sunlight)
        self.control_bar.chat_clicked.connect(self.open_chat_dialog)
        self.control_bar.garden_clicked.connect(self.open_garden_dialog)
        self.control_bar.settings_clicked.connect(self.open_settings_dialog)

    def on_character_clicked(self):
        """Show menu on click above pot and keep open for 6 seconds."""
        self.control_bar.show()
        self.control_bar.raise_()
        self.force_topmost()
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

        # Heartbeat Topmost enforcement timer (every 2.5s) to stay above 3rd-party docks/quickbars
        self.topmost_timer = QTimer(self)
        self.topmost_timer.timeout.connect(self.force_topmost)
        self.topmost_timer.start(2500)

        # Decay and Smart Peeking timer (every 1 minute)
        self.decay_timer = QTimer(self)
        self.decay_timer.timeout.connect(self.on_decay_timer_tick)
        self.decay_timer.start(60 * 1000)
        self.minutes_elapsed = 0

        # Fast idle check & Proactive Speech timer (every 15 seconds)
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.on_idle_timer_tick)
        self.idle_timer.start(15 * 1000)

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
        self.force_topmost()
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

    def on_eco_visitor_arrived(self, v_type: str):
        try:
            if v_type == "bee":
                self.bubble.show_message("🐝 윙윙~ 꿀벌 친구가 찾아왔어요! 꿀을 만드느라 목이 마르대요~ 💧", 5)
            elif v_type == "bug":
                self.bubble.show_message("🐛 앗! 나뭇잎에 벌레가 나타났어요! 클릭해서 쫓아내주세요! 💦", 5)
            elif v_type == "ladybug":
                self.bubble.show_message("🐞 행운을 부르는 칠성무당벌레가 화분을 찾아왔어요! 🍀", 5)
            elif v_type == "bird":
                self.bubble.show_message("🐦 짹짹~ 귀여운 아기 파랑새가 가지에 살포시 앉았어요 ✨", 5)
            elif v_type == "cat_paw":
                self.bubble.show_message("🐾 앗! 장난꾸러기 고양이 발이 빼꼼 나타났어요! 냥~ 🐱", 5)
            elif v_type == "rain_cloud":
                self.bubble.show_message("🌧️ 촉촉한 단비 구름이 지나가며 잎사귀를 적셔주고 있어요 🌈", 5)
                # Auto apply rain hydration bonus
                self.engine.on_eco_visitor_interacted("rain_cloud")
                self.character.spawn_particle("drop")
            elif v_type == "firefly":
                self.bubble.show_message("✨ 반짝반짝 반딧불이들이 춤추며 화분을 밝혀주고 있어요 🌌", 5)
            else:  # butterfly
                self.bubble.show_message("🦋 예쁜 나비가 찾아와 살랑살랑 쉬어가고 있어요 🌸", 5)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_eco_visitor_arrived error: {e}")

    def on_bug_cleared(self):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            success, msg = self.engine.on_bug_cleared()
            self.control_bar.update_status(self.engine.get_state())
            for _ in range(4):
                self.character.spawn_particle("drop")
            self.bubble.show_message(msg, 4)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_bug_cleared error: {e}")

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
            if not self.chat_dialog:
                self.chat_dialog = ChatDialog(self.db, self.config, None)
                self.chat_dialog.message_sent.connect(self.start_ai_chat)
            
            self.chat_dialog.refresh_header()
            self.chat_dialog.load_history()
            self.chat_dialog.show()
            self.chat_dialog.raise_()
            self.chat_dialog.activateWindow()
        except Exception as e:
            print(f"[FloatingPlantWindow] open_chat_dialog error: {e}")

    # --- Garden & Collection Dialog ---
    def open_garden_dialog(self):
        try:
            self.last_user_interaction_time = datetime.datetime.now()
            self.menu_auto_close_timer.stop()
            self.control_bar.hide()
            if not self.garden_dialog:
                self.garden_dialog = GardenDialog(self.engine, self.db, self.config, None)
                self.garden_dialog.plant_graduated.connect(self.on_plant_graduated)
                self.garden_dialog.fortune_drawn.connect(self.on_fortune_drawn)
            
            self.garden_dialog.show()
            self.garden_dialog.raise_()
            self.garden_dialog.activateWindow()
        except Exception as e:
            print(f"[FloatingPlantWindow] open_garden_dialog error: {e}")

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
            if self.chat_dialog:
                self.chat_dialog.load_history()

            # 4. Start real-time streaming on speech bubble
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
        try:
            self._stop_existing_workers()
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
            worker.chunk_received.connect(self.bubble.append_chunk)
            worker.response_received.connect(self.on_proactive_response_received)
            worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
            worker.start()
        except Exception as e:
            print(f"[FloatingPlantWindow] trigger_proactive_speech error: {e}")

    def on_proactive_response_received(self, reply_text: str, is_fallback: bool, action_tags: list):
        try:
            self.db.add_chat_message("assistant", reply_text)
            self.bubble.finish_streaming(reply_text, self.config.get("bubble_duration_sec", 5))
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

            self.bubble.finish_streaming(reply_text, self.config.get("bubble_duration_sec", 5))
        except Exception as e:
            print(f"[FloatingPlantWindow] on_ai_response_received error: {e}")

    # --- Settings Dialog ---
    def open_settings_dialog(self):
        try:
            self.menu_auto_close_timer.stop()
            self.control_bar.hide()
            if not self.settings_dialog:
                self.settings_dialog = SettingsDialog(self.config, None)
                self.settings_dialog.settings_saved.connect(self.apply_settings_changes)
                self.settings_dialog.clear_chat_requested.connect(self.on_clear_chat)
                self.settings_dialog.reset_plant_requested.connect(self.on_reset_plant)
            
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
            self.force_topmost()

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
            self.force_topmost()
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
            self.force_topmost()
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
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 4px;
                font-family: 'Malgun Gothic';
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #ECFDF5;
                color: #065F46;
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

        action_settings = menu.addAction("⚙️ 환경 설정")
        action_settings.triggered.connect(self.open_settings_dialog)

        menu.addSeparator()

        action_close = menu.addAction("❌ 위젯 종료")
        action_close.triggered.connect(QApplication.quit)

        menu.exec(global_pos)

    def toggle_always_on_top(self):
        new_val = not self.config.get("always_on_top", True)
        self.config.set("always_on_top", new_val)
        self.apply_settings_changes()
