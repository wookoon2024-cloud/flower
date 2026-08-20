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
        s = max(70, min(160, scale_pct)) / 100.0
        w = int(280 * s)
        h = int(320 * s)
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
        """Dynamically resize window and scale components cleanly with perfect horizontal centering."""
        scale_pct = self.config.get("plant_scale", 100)
        s = max(70, min(160, scale_pct)) / 100.0
        w = int(280 * s)
        h = int(320 * s)

        old_geo = self.geometry()
        old_bottom = old_geo.bottom() if old_geo.isValid() else -1

        self.setFixedSize(w, h)

        # Center speech bubble horizontally
        w_b = min(w - 16, int(244 * s))
        self.bubble.setGeometry((w - w_b) // 2, int(4 * s), w_b, int(72 * s))

        # Center control bar horizontally (never clipped!)
        w_c = min(w - 20, int(232 * s))
        self.control_bar.setGeometry((w - w_c) // 2, int(80 * s), w_c, int(72 * s))

        # Center character horizontally at bottom
        char_sz = int(160 * s)
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
                new_s = max(70, curr_s - 10)
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

        # Fast idle check timer (every 10 seconds)
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.on_idle_timer_tick)
        self.idle_timer.start(10 * 1000)

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
        if not self.config.get("idle_peek", True):
            return

        idle_sec = get_system_idle_seconds()
        # If user has been idle for >= 3 minutes (180s)
        if idle_sec >= 180:
            if not self.idle_notified:
                self.idle_notified = True
                user_name = self.config.get("user_nickname", "공직자님")
                self.bubble.show_message(f"잠시 쉬어가시는 중인가요, {user_name}? ☕ 심호흡 한 번 하고 편안한 휴식 되세요 🌿", 4)
        elif idle_sec < 40:
            self.idle_notified = False

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
        self.menu_auto_close_timer.start(6000)
        success, msg = self.engine.give_water()
        self.character.spawn_particle("drop")
        self.bubble.show_message(msg, 3)

    def handle_sunlight(self):
        self.menu_auto_close_timer.start(6000)
        success, msg = self.engine.give_sunlight()
        self.character.spawn_particle("sun")
        self.bubble.show_message(msg, 3)

    def on_engine_state_changed(self, state: dict):
        self.character.set_species(self.engine.get_species())
        self.character.set_stage(state.get("stage", 1))
        self.control_bar.update_status(state)

    def on_plant_evolved(self, new_stage: int, message: str):
        self.character.set_species(self.engine.get_species())
        self.character.set_stage(new_stage)
        self.bubble.show_message(message, 5)
        for _ in range(6):
            self.character.spawn_particle("heart")

    def on_plant_warning(self, message: str):
        self.bubble.show_message(message, 4)

    def on_plant_interaction(self, action_name: str, bubble_text: str):
        if action_name == "pet":
            self.character.spawn_particle("heart")
        self.bubble.show_message(bubble_text, 3)

    def on_achievement_unlocked(self, ach: dict):
        for _ in range(5):
            self.character.spawn_particle("heart")
        self.bubble.show_message(f"🏆 업적 달성! [{ach.get('title')}] 뱃지 획득! ✨", 5)

    # --- AI Chat Handling ---
    def open_chat_dialog(self):
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

    # --- Garden & Collection Dialog ---
    def open_garden_dialog(self):
        self.menu_auto_close_timer.stop()
        self.control_bar.hide()
        if not self.garden_dialog:
            self.garden_dialog = GardenDialog(self.engine, self.db, self.config, None)
            self.garden_dialog.plant_graduated.connect(self.on_plant_graduated)
            self.garden_dialog.fortune_drawn.connect(self.on_fortune_drawn)
        
        self.garden_dialog.show()
        self.garden_dialog.raise_()
        self.garden_dialog.activateWindow()

    def on_plant_graduated(self, new_species: str, new_name: str):
        self.character.set_species(new_species)
        self.character.set_stage(1)
        self.control_bar.update_status(self.engine.get_state())
        for _ in range(6):
            self.character.spawn_particle("heart")
        self.bubble.show_message(f"🎓 축하합니다! 새로운 {new_name} 화분을 키우기 시작했어요! 🌱", 5)

    def on_fortune_drawn(self, msg: str):
        self.character.spawn_particle("sun")
        self.bubble.show_message(f"🥠 {msg}", 4)

    def start_ai_chat(self, user_text: str):
        try:
            # 1. Extract recent history BEFORE saving current message
            history = self.db.get_recent_chat_history(limit=6)

            # 2. Save sentiment analysis and user message
            mood_type, score = analyze_user_sentiment(user_text)
            self.db.add_mood_entry(mood_type, score, user_text)
            self.db.add_chat_message("user", user_text)

            # 3. Refresh chat dialog immediately so user message appears on the right
            if self.chat_dialog:
                self.chat_dialog.load_history()

            # 4. Start async AI worker thread safely with lifetime tracking
            worker = AIChatWorker(
                config=dict(self.config.config),
                plant_state=dict(self.engine.get_state()),
                chat_history=list(history),
                user_message=user_text
            )
            self._active_workers.append(worker)
            worker.response_received.connect(self.on_ai_response_received)
            worker.finished.connect(lambda w=worker: self._on_worker_finished(w))
            worker.start()
        except Exception as e:
            print(f"[FloatingPlantWindow] start_ai_chat error: {e}")
            if self.chat_dialog:
                self.chat_dialog.set_loading(False)

    def _on_worker_finished(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        worker.deleteLater()

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

            self.bubble.show_message(reply_text, 4)
        except Exception as e:
            print(f"[FloatingPlantWindow] on_ai_response_received error: {e}")

    # --- Settings Dialog ---
    def open_settings_dialog(self):
        self.menu_auto_close_timer.stop()
        self.control_bar.hide()
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config, None)
            self.settings_dialog.settings_saved.connect(self.apply_settings_changes)
            self.settings_dialog.clear_chat_requested.connect(self.on_clear_chat)
            self.settings_dialog.reset_plant_requested.connect(self.on_reset_plant)
        
        self.settings_dialog.exec()

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
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.force_topmost()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            # Hide menu and bubble while dragging so only the clean pot is visible!
            self.menu_auto_close_timer.stop()
            if self.control_bar.isVisible():
                self.control_bar.hide()
            if self.bubble.isVisible():
                self.bubble.hide()

            curr_pos = event.globalPosition().toPoint()
            target_x = curr_pos.x() - self.drag_position.x()
            target_y = curr_pos.y() - self.drag_position.y()

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
            ("75% (아담한 미니 화분)", 75),
            ("85% (약간 작게)", 85),
            ("100% (보통 크기 - 기본)", 100),
            ("115% (약간 크게)", 115),
            ("130% (크게 보기)", 130),
            ("145% (시원한 대형 화분)", 145)
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
