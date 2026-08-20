"""
Plant Character Widget
Renders stage-based plant sprite with rich animated facial expressions on the flowerpot:
- Natural eye blinking (눈 깜빡임)
- Cute sleepy yawn with zZZ (하품)
- Playful tongue sticking out (메롱 😋)
- Flirty wink & blushing cheeks (윙크 & 볼홍조)
- Flowerpot body remains 100% stationary and solidly anchored to the desktop!
"""
import os
import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QLinearGradient, QRadialGradient, QPolygonF
from ..config import get_resource_path

class FloatingParticle:
    def __init__(self, pixmap: QPixmap, start_pos: QPoint):
        self.pixmap = pixmap
        self.x = float(start_pos.x() + random.randint(-15, 15))
        self.y = float(start_pos.y())
        self.vy = -2.0 - random.random() * 1.5
        self.alpha = 255.0
        self.fade_rate = 6.0
        self.alive = True

    def update(self):
        self.y += self.vy
        self.alpha -= self.fade_rate
        if self.alpha <= 0:
            self.alive = False


class EcoVisitor:
    """
    Animated Environmental Creature & Magical Eco-Events:
    - 🐝 Bee (꿀벌)
    - 🐛 Bug / Earthworm / Caterpillar (바닥에서 기어서 화분을 타고 올라가는 지렁이/애벌레)
    - 🦋 Butterfly (나비)
    - 🐞 Ladybug (칠성무당벌레)
    - 🐦 Bluebird (아기 파랑새)
    - 🐾 Kitty Paw (길고양이 젤리 발)
    - 🌧️ Rain Cloud & Rainbow (단비 구름과 무지개)
    - ✨ Fireflies (밤하늘 반딧불이)
    """
    def __init__(self, v_type: str, canvas_w: int, canvas_h: int):
        self.v_type = v_type
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.alive = True
        self.frame = 0
        self.total_frames = random.randint(230, 310)  # ~7~10 seconds
        self.wing_phase = 0.0
        self.crawl_angle = 0.0
        self.state = "fly_in"  # "fly_in", "landed", "fly_out", "fleeing"
        self.is_fleeing = False

        if self.v_type == "bug":
            # Crawls in from bottom floor, climbs up pot wall, nibbles leaf, climbs down
            self.side = random.choice([-1, 1])
            self.start_x = -15.0 if self.side < 0 else float(canvas_w + 15)
            self.start_y = float(canvas_h - 6)
            self.pot_base_x = float(canvas_w // 2 + self.side * 22)
            self.pot_base_y = float(canvas_h - 6)
            self.pot_rim_x = float(canvas_w // 2 + self.side * 28)
            self.pot_rim_y = float(canvas_h - 44)
            self.pot_leaf_x = float(canvas_w // 2 + self.side * 16)
            self.pot_leaf_y = float(canvas_h - 56)
            self.target_x = self.pot_leaf_x
            self.target_y = self.pot_leaf_y
            self.x, self.y = self.start_x, self.start_y
            self.crawl_angle = 0.0
        elif self.v_type == "ladybug":
            self.side = random.choice([-1, 1])
            self.start_x = float(canvas_w // 2 - self.side * 40)
            self.start_y = float(canvas_h - 38)
            self.target_x = float(canvas_w // 2 + self.side * 28)
            self.target_y = float(canvas_h - 48)
            self.x, self.y = self.start_x, self.start_y
            self.crawl_angle = 0.0
        elif self.v_type == "bird":
            self.from_left = random.choice([True, False])
            self.start_x = -25.0 if self.from_left else float(canvas_w + 25)
            self.start_y = float(random.randint(5, 25))
            self.target_x = float(canvas_w // 2 + (-30 if self.from_left else 30))
            self.target_y = float(canvas_h - 50)
            self.x, self.y = self.start_x, self.start_y
        elif self.v_type == "cat_paw":
            self.start_x = float(canvas_w + 20)
            self.start_y = -15.0
            self.target_x = float(canvas_w // 2 + 28)
            self.target_y = float(canvas_h // 2 - 12)
            self.x, self.y = self.start_x, self.start_y
        elif self.v_type == "rain_cloud":
            self.start_x = -40.0
            self.start_y = 18.0
            self.target_x = float(canvas_w // 2)
            self.target_y = 18.0
            self.x, self.y = self.start_x, self.start_y
        elif self.v_type == "firefly":
            self.start_x = float(canvas_w // 2)
            self.start_y = float(canvas_h // 2 - 20)
            self.target_x = self.start_x
            self.target_y = self.start_y
            self.x, self.y = self.start_x, self.start_y
        elif self.v_type == "bee":
            self.from_left = random.choice([True, False])
            self.start_x = -20.0 if self.from_left else float(canvas_w + 20)
            self.start_y = float(random.randint(8, 35))
            self.target_x = float(canvas_w // 2 + random.randint(-20, 20))
            self.target_y = float(canvas_h // 2 - random.randint(18, 36))
            self.x, self.y = self.start_x, self.start_y
        else:  # butterfly
            self.from_left = random.choice([True, False])
            self.start_x = -25.0 if self.from_left else float(canvas_w + 25)
            self.start_y = float(random.randint(15, 45))
            self.target_x = float(canvas_w // 2 + random.randint(-24, 24))
            self.target_y = float(canvas_h // 2 - random.randint(8, 26))
            self.x, self.y = self.start_x, self.start_y

    def update(self):
        self.frame += 1
        self.wing_phase += 0.45

        # 1. Fleeing / Scared Behavior
        if self.is_fleeing:
            if self.v_type == "bug":
                # Drops to floor and scurries rapidly along the bottom taskbar floor!
                self.y = min(float(self.canvas_h - 6), self.y + 4.0)
                self.x += (-5.0 if self.side < 0 else 5.0)
                self.crawl_angle = 0.0
                if self.x < -30 or self.x > self.canvas_w + 30:
                    self.alive = False
                return
            else:
                self.y -= 4.5
                self.x += (3.5 if self.x > self.canvas_w // 2 else -3.5)
                if self.y < -40 or self.x < -50 or self.x > self.canvas_w + 50:
                    self.alive = False
                return

        # 2. Bug (Earthworm / Caterpillar) Ground & Pot-climbing State Machine
        if self.v_type == "bug":
            p1 = 45                               # Crawl along floor to pot base
            p2 = 85                               # Climb up pot wall to rim
            p3 = 110                              # Reach leaf
            p4 = self.total_frames - 75           # Nibble on leaf
            p5 = self.total_frames - 40           # Climb down pot wall to floor
            p6 = self.total_frames                # Crawl away along floor

            if self.frame < p1:
                self.state = "fly_in"
                t = self.frame / float(p1)
                self.x = self.start_x + (self.pot_base_x - self.start_x) * t
                self.y = float(self.canvas_h - 6)
                self.crawl_angle = 0.0
            elif self.frame < p2:
                self.state = "fly_in"
                t = (self.frame - p1) / float(p2 - p1)
                self.x = self.pot_base_x + (self.pot_rim_x - self.pot_base_x) * t
                self.y = self.pot_base_y + (self.pot_rim_y - self.pot_base_y) * t
                # Tilted along pot wall
                self.crawl_angle = -62.0 if self.side < 0 else 62.0
            elif self.frame < p3:
                self.state = "fly_in"
                t = (self.frame - p2) / float(p3 - p2)
                self.x = self.pot_rim_x + (self.pot_leaf_x - self.pot_rim_x) * t
                self.y = self.pot_rim_y + (self.pot_leaf_y - self.pot_rim_y) * t
                self.crawl_angle = -25.0 if self.side < 0 else 25.0
            elif self.frame < p4:
                self.state = "landed"
                self.x = self.pot_leaf_x + math.sin(self.wing_phase * 0.4) * 1.2
                self.y = self.pot_leaf_y + math.cos(self.wing_phase * 0.3) * 0.6
                self.crawl_angle = math.sin(self.wing_phase * 0.3) * 8.0
            elif self.frame < p5:
                self.state = "fly_out"
                t = (self.frame - p4) / float(p5 - p4)
                self.x = self.pot_leaf_x + (self.pot_base_x - self.pot_leaf_x) * t
                self.y = self.pot_leaf_y + (self.pot_base_y - self.pot_leaf_y) * t
                self.crawl_angle = 62.0 if self.side < 0 else -62.0
            else:
                self.state = "fly_out"
                t = (self.frame - p5) / float(p6 - p5)
                dest_x = -30.0 if self.side < 0 else float(self.canvas_w + 30)
                self.x = self.pot_base_x + (dest_x - self.pot_base_x) * t
                self.y = float(self.canvas_h - 6)
                self.crawl_angle = 0.0
                if self.frame >= self.total_frames:
                    self.alive = False
            return

        # 3. Rain Cloud Drifting
        if self.v_type == "rain_cloud":
            t = self.frame / float(self.total_frames)
            self.x = -35.0 + t * (self.canvas_w + 70.0)
            self.y = 18.0 + math.sin(t * math.pi * 2) * 2.0
            if self.frame >= self.total_frames:
                self.alive = False
            return

        # 4. Fireflies Swarming
        if self.v_type == "firefly":
            if self.frame >= self.total_frames:
                self.alive = False
            return

        # 5. Flying Visitors (Bee, Bird, Butterfly, Ladybug, Cat Paw)
        in_frames = 55
        out_start = self.total_frames - 55

        if self.frame < in_frames:
            self.state = "fly_in"
            t = self.frame / float(in_frames)
            t_ease = math.sin(t * math.pi / 2.0)
            self.x = self.start_x + (self.target_x - self.start_x) * t_ease
            sine_wave = math.sin(t * math.pi * 3) * (7.0 if self.v_type not in ["ladybug", "cat_paw"] else 1.2)
            self.y = self.start_y + (self.target_y - self.start_y) * t_ease + sine_wave
        elif self.frame < out_start:
            self.state = "landed"
            hover_amp = 1.4 if self.v_type not in ["ladybug", "bird", "cat_paw"] else 0.3
            self.x = self.target_x + math.sin(self.wing_phase * 0.3) * hover_amp
            self.y = self.target_y + math.cos(self.wing_phase * 0.4) * hover_amp
        elif self.frame < self.total_frames:
            self.state = "fly_out"
            t = (self.frame - out_start) / 55.0
            t_ease = t * t
            dest_x = -40.0 if self.target_x < self.canvas_w // 2 else float(self.canvas_w + 40)
            dest_y = -35.0 if self.v_type != "cat_paw" else -20.0
            if self.v_type == "cat_paw":
                dest_x = float(self.canvas_w + 25)
            self.x = self.target_x + (dest_x - self.target_x) * t_ease
            sine_wave = math.sin(t * math.pi * 3) * 5.0
            self.y = self.target_y + (dest_y - self.target_y) * t_ease + sine_wave
        else:
            self.alive = False

    def hit_test(self, pos) -> bool:
        px = pos.x() if hasattr(pos, "x") else pos[0]
        py = pos.y() if hasattr(pos, "y") else pos[1]
        dist = math.hypot(px - self.x, py - self.y)
        hit_radius = 28.0 if self.v_type in ["rain_cloud", "bird", "cat_paw"] else 22.0
        return dist <= hit_radius

    def flee(self):
        self.is_fleeing = True


class PlantCharacterWidget(QWidget):
    clicked = Signal()
    bug_cleared = Signal()
    visitor_greeted = Signal(str)      # "bee", "butterfly"
    eco_visitor_arrived = Signal(str)  # "bee", "bug", "butterfly"

    def __init__(self, parent=None, scale_pct: int = 100):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scale_pct = max(60, min(160, scale_pct))
        sz = int(120 * (self.scale_pct / 100.0))
        self.setFixedSize(sz, sz)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.current_stage = 1
        self.current_species = "classic"
        self.pixmaps = {}
        self.particle_pixmaps = {}
        self.particles = []

        # Eco-Visitor (Bee 🐝, Bug 🐛, Butterfly 🦋, etc.)
        self.eco_visitor: Optional[EcoVisitor] = None
        self.eco_timer = QTimer(self)
        self.eco_timer.timeout.connect(self._on_eco_tick)
        self.eco_spawn_timer = QTimer(self)
        self.eco_spawn_timer.setSingleShot(True)
        self.eco_spawn_timer.timeout.connect(self._spawn_random_eco_visitor)

        # Interactive Particle animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_particles)

        # Dynamic Facial Expression System (Blink, Yawn, Merong/Tongue, Wink)
        self.expr_timer = QTimer(self)
        self.expr_timer.timeout.connect(self._on_expr_tick)
        self.idle_trigger_timer = QTimer(self)
        self.idle_trigger_timer.setSingleShot(True)
        self.idle_trigger_timer.timeout.connect(self._trigger_random_expression)

        self.expr_type = "none"  # "blink", "yawn", "tongue", "wink", "happy"
        self.expr_frame = 0
        self.expr_total_frames = 35

        self.load_resources("classic")
        self._schedule_next_expression()
        self._schedule_next_eco_visitor()

    def set_scale(self, scale_pct: int):
        """Dynamically adjust flowerpot scale (100% = 120px)."""
        self.scale_pct = max(60, min(160, scale_pct))
        sz = int(120 * (self.scale_pct / 100.0))
        self.setFixedSize(sz, sz)
        self.load_resources(self.current_species)
        self.update()

    def load_resources(self, species: str = "classic"):
        """Load stage sprites and particle icons for specified species (stages 1~6)."""
        self.current_species = species
        scaled_sz = int(112 * (self.scale_pct / 100.0))
        for stg in range(1, 7):
            path = get_resource_path(os.path.join("assets", f"stage_{species}_{stg}.png"))
            if not os.path.exists(path):
                path = get_resource_path(os.path.join("assets", f"stage_{stg}.png"))
            
            if os.path.exists(path):
                pm = QPixmap(path).scaled(
                    scaled_sz, scaled_sz,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.pixmaps[stg] = pm
            else:
                self.pixmaps[stg] = QPixmap()

        # Load particles
        part_sz = max(18, int(22 * (self.scale_pct / 100.0)))
        for p_name in ["heart", "drop", "sun"]:
            path = get_resource_path(os.path.join("assets", f"{p_name}.png"))
            if os.path.exists(path):
                pm = QPixmap(path).scaled(
                    part_sz, part_sz,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.particle_pixmaps[p_name] = pm

    def set_species(self, species: str):
        if self.current_species != species:
            self.load_resources(species)
            self.update()

    def set_stage(self, stage: int):
        self.current_stage = max(1, min(6, stage))
        self.update()

    # --- Eco-Visitor (Bee, Bug, Ladybug, Bird, Cat Paw, Rain Cloud, Fireflies) System ---
    def _schedule_next_eco_visitor(self):
        """Schedule next eco visitor event after 25 ~ 50 seconds."""
        interval_ms = random.randint(25000, 50000)
        self.eco_spawn_timer.start(interval_ms)

    def _spawn_random_eco_visitor(self):
        """Spawns an animated eco visitor or magical environmental event around the flowerpot."""
        types = [
            "bee", "bee",
            "bug", "bug",
            "butterfly",
            "ladybug", "ladybug",
            "bird",
            "cat_paw",
            "rain_cloud",
            "firefly"
        ]
        chosen_type = random.choice(types)
        self.eco_visitor = EcoVisitor(chosen_type, self.width(), self.height())
        self.eco_timer.start(33)  # ~30 fps
        self.eco_visitor_arrived.emit(chosen_type)
        self.update()

    def _on_eco_tick(self):
        if self.eco_visitor:
            self.eco_visitor.update()
            if not self.eco_visitor.alive:
                self.eco_visitor = None
                self.eco_timer.stop()
                self._schedule_next_eco_visitor()
            self.update()

    # --- Cute Facial Expression Idle Animation System ---
    def _schedule_next_expression(self):
        """Schedule next expression after 3.5 ~ 6.5 seconds."""
        interval_ms = random.randint(3500, 6500)
        self.idle_trigger_timer.start(interval_ms)

    def _trigger_random_expression(self):
        """Picks a random facial expression (Blink, Yawn, Tongue out, Wink)."""
        choices = ["blink", "blink", "yawn", "tongue", "wink", "happy"]
        self.expr_type = random.choice(choices)
        self.expr_frame = 0

        if self.expr_type == "blink":
            self.expr_total_frames = 28
        elif self.expr_type == "yawn":
            self.expr_total_frames = 45
        elif self.expr_type == "tongue":
            self.expr_total_frames = 38
        elif self.expr_type == "wink":
            self.expr_total_frames = 32
        else:
            self.expr_total_frames = 30

        self.expr_timer.start(33)

    def _on_expr_tick(self):
        self.expr_frame += 1
        if self.expr_frame >= self.expr_total_frames:
            self.expr_type = "none"
            self.expr_frame = 0
            self.expr_timer.stop()
            self.update()
            self._schedule_next_expression()
            return
        self.update()

    # --- Interactive Reaction Particles ---
    def spawn_particle(self, particle_type: str = "heart"):
        """Spawn floating icon on interaction."""
        pm = self.particle_pixmaps.get(particle_type)
        if pm and not pm.isNull():
            center_pt = QPoint(self.width() // 2 - 14, self.height() // 2 - 20)
            self.particles.append(FloatingParticle(pm, center_pt))
            if not self.anim_timer.isActive():
                self.anim_timer.start(33)

    def update_particles(self):
        if not self.particles:
            self.anim_timer.stop()
            self.update()
            return
        
        alive_particles = []
        for p in self.particles:
            p.update()
            if p.alive:
                alive_particles.append(p)
        self.particles = alive_particles
        if not self.particles:
            self.anim_timer.stop()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 1. Interactive Eco-Visitor Hit Test (Click on Bee, Bug, Ladybug, Bird, Kitty Paw, etc.!)
            if self.eco_visitor and self.eco_visitor.alive and self.eco_visitor.hit_test(event.pos()):
                v_type = self.eco_visitor.v_type
                self.eco_visitor.flee()
                if v_type == "bug":
                    self.bug_cleared.emit()
                    self.spawn_particle("drop")
                    self.expr_type = "happy"
                    self.expr_frame = 0
                    self.expr_total_frames = 30
                    self.expr_timer.start(33)
                else:
                    self.visitor_greeted.emit(v_type)
                    if v_type in ["bird", "rain_cloud"]:
                        self.spawn_particle("sun")
                    else:
                        self.spawn_particle("heart")
                    self.expr_type = "wink" if v_type != "cat_paw" else "tongue"
                    self.expr_frame = 0
                    self.expr_total_frames = 30
                    self.expr_timer.start(33)
                event.accept()
                return

            # 2. Regular Plant Pet / Touch
            self.clicked.emit()
            self.spawn_particle("heart")
            self.expr_type = "happy"
            self.expr_frame = 0
            self.expr_total_frames = 25
            self.expr_timer.start(33)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Draw Plant Sprite (100% stationary flowerpot body resting on taskbar)
        pix = self.pixmaps.get(self.current_stage)
        if pix and not pix.isNull():
            px = (self.width() - pix.width()) // 2
            py = self.height() - pix.height()
            painter.drawPixmap(px, py, pix)

            # 2. Draw Dynamic Facial Expressions on the pot
            if self.expr_type != "none":
                self._draw_facial_expression(painter, px, py, pix.width())
        else:
            # Fallback drawing if PNG is missing
            painter.setPen(QColor(46, 125, 50))
            painter.setBrush(QColor(129, 199, 132))
            painter.drawEllipse(30, 30, 100, 100)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"🌱 {self.current_stage}단계")

        # 3. Draw Active Animated Eco-Visitor / Environmental Event
        if self.eco_visitor and self.eco_visitor.alive:
            self._draw_eco_visitor(painter, self.eco_visitor)

        # 4. Draw Active Floating Particles
        for p in self.particles:
            painter.setOpacity(p.alpha / 255.0)
            painter.drawPixmap(int(p.x), int(p.y), p.pixmap)
            painter.setOpacity(1.0)

    def _draw_eco_visitor(self, painter: QPainter, v: EcoVisitor):
        """Renders animated vector graphic of all 8 visiting creatures & magical events."""
        painter.save()
        painter.translate(v.x, v.y)

        if v.v_type == "bee":
            # 🐝 Cute Honeybee
            facing_left = (v.x < v.target_x) if v.state == "fly_in" else (v.x < v.canvas_w // 2)
            if facing_left:
                painter.scale(-1, 1)

            # Translucent flutter wings
            wing_angle = math.sin(v.wing_phase) * 35.0
            painter.setBrush(QColor(224, 242, 254, 200))
            painter.setPen(QPen(QColor(186, 230, 253), 1))
            
            painter.save()
            painter.translate(-2, -6)
            painter.rotate(-wing_angle)
            painter.drawEllipse(QRectF(-6, -10, 12, 10))
            painter.restore()

            painter.save()
            painter.translate(3, -6)
            painter.rotate(wing_angle)
            painter.drawEllipse(QRectF(-5, -9, 10, 9))
            painter.restore()

            # Bee body (Golden oval with dark stripes)
            painter.setPen(QPen(QColor("#78350F"), 1.2))
            painter.setBrush(QColor("#FBBF24"))
            painter.drawEllipse(QRectF(-10, -6, 20, 13))

            # Stripes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1F2937"))
            painter.drawRoundedRect(QRectF(-4, -6, 3.5, 13), 1, 1)
            painter.drawRoundedRect(QRectF(2, -5.5, 3.5, 12), 1, 1)

            # Head & Cute Eye
            painter.drawEllipse(QRectF(7, -4, 6, 8))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(9, -2, 2.5, 2.5))

            # Golden Pollen Sparkles when landed
            if v.state == "landed" and int(v.frame) % 12 < 6:
                painter.setBrush(QColor(254, 240, 138, 220))
                painter.drawEllipse(QPointF(0, 9), 2.5, 2.5)

        elif v.v_type == "bug":
            # 🐛 Floor-Crawling & Pot-Climbing Inchworm / Caterpillar (바닥에서 기어서 화분을 오르는 지렁이/애벌레)
            facing_dir = 1 if ((v.side < 0 and v.state != "fly_out") or (v.side > 0 and v.state == "fly_out")) else -1
            painter.scale(facing_dir, 1)
            painter.rotate(v.crawl_angle * facing_dir)

            # Inchworm arching & crawling accordion animation (자벌레 U자 등 굽힘과 신축)
            wiggle = math.sin(v.wing_phase * 0.9) * 2.2
            colors = ["#4D7C0F", "#65A30D", "#84CC16", "#A3E635"]
            
            for idx in range(4):
                # Arching back effect as it moves along the surface
                seg_x = -idx * 4.2 + (wiggle * 0.35 if idx in [1, 2] else 0)
                seg_y = (abs(wiggle) * -1.6) if idx in [1, 2] else 0.0
                painter.setPen(QPen(QColor("#365314"), 1))
                painter.setBrush(QColor(colors[idx]))
                painter.drawEllipse(QRectF(seg_x - 3.5, seg_y - 3.5, 7, 7))

            # Cute Head with feelers
            painter.setPen(QPen(QColor("#365314"), 1.2))
            painter.setBrush(QColor("#BEF264"))
            painter.drawEllipse(QRectF(2.5, -4.5, 8, 8))
            
            # Eye & Blush
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1F2937"))
            painter.drawEllipse(QRectF(6.5, -3, 2, 2))
            painter.setBrush(QColor("#F472B6"))
            painter.drawEllipse(QRectF(5, 0.5, 2, 1.5))

            # Nibbling crumbs when landed on leaf
            if v.state == "landed" and int(v.frame) % 16 < 8:
                painter.setBrush(QColor("#65A30D"))
                painter.drawEllipse(QPointF(11, 0), 1.8, 1.8)

        elif v.v_type == "ladybug":
            # 🐞 Cute Ladybug (칠성무당벌레)
            facing_left = (v.side > 0)
            if facing_left:
                painter.scale(-1, 1)

            # Tiny crawling legs
            leg_wiggle = math.sin(v.wing_phase * 0.8) * 2.0
            painter.setPen(QPen(QColor("#1F2937"), 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for leg_i in [-4, 0, 4]:
                painter.drawLine(leg_i, 5, leg_i + int(leg_wiggle), 9)
                painter.drawLine(leg_i, -5, leg_i - int(leg_wiggle), -9)

            # Red glossy dome shell
            painter.setPen(QPen(QColor("#991B1B"), 1))
            grad_shell = QLinearGradient(-6, -6, 6, 6)
            grad_shell.setColorAt(0.0, QColor("#EF4444"))
            grad_shell.setColorAt(1.0, QColor("#B91C1C"))
            painter.setBrush(QBrush(grad_shell))
            painter.drawEllipse(QRectF(-7, -7, 14, 14))

            # Black center division line
            painter.setPen(QPen(QColor("#111827"), 1.2))
            painter.drawLine(-7, 0, 7, 0)

            # 7 Black Spots
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(QPointF(-3, -3), 1.3, 1.3)
            painter.drawEllipse(QPointF(2, -3.5), 1.4, 1.4)
            painter.drawEllipse(QPointF(-3, 3), 1.3, 1.3)
            painter.drawEllipse(QPointF(2, 3.5), 1.4, 1.4)
            painter.drawEllipse(QPointF(-5, 0), 1.2, 1.2)
            painter.drawEllipse(QPointF(4, 0), 1.2, 1.2)

            # Head & Antennae
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(QRectF(5, -3.5, 5, 7))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(7, -2, 1.5, 1.5))
            painter.drawEllipse(QRectF(7, 1, 1.5, 1.5))
            painter.setPen(QPen(QColor("#111827"), 1))
            painter.drawLine(9, -2, 12, -4)
            painter.drawLine(9, 2, 12, 4)

        elif v.v_type == "bird":
            # 🐦 Cute Little Bluebird (아기 파랑새)
            facing_left = (v.x < v.target_x) if v.state == "fly_in" else (v.x < v.canvas_w // 2)
            if facing_left:
                painter.scale(-1, 1)

            # Tail feathers
            painter.setPen(QPen(QColor("#0284C7"), 1))
            painter.setBrush(QColor("#0369A1"))
            painter.drawPolygon([QPointF(-10, 0), QPointF(-17, -4), QPointF(-17, 3)])

            # Round Sky-Blue Body
            grad_bird = QLinearGradient(-8, -8, 8, 8)
            grad_bird.setColorAt(0.0, QColor("#38BDF8"))
            grad_bird.setColorAt(1.0, QColor("#0284C7"))
            painter.setPen(QPen(QColor("#0369A1"), 1.2))
            painter.setBrush(QBrush(grad_bird))
            painter.drawEllipse(QRectF(-8, -8, 17, 15))

            # White/Cream Tummy
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#E0F2FE"))
            painter.drawEllipse(QRectF(-4, 0, 10, 6.5))

            # Flapping Wing
            wing_ang = math.sin(v.wing_phase) * 30.0 if v.state != "landed" else 0.0
            painter.save()
            painter.translate(-1, -2)
            painter.rotate(-wing_ang)
            painter.setPen(QPen(QColor("#0369A1"), 1))
            painter.setBrush(QColor("#0284C7"))
            painter.drawEllipse(QRectF(-5, -3, 10, 6.5))
            painter.restore()

            # Head & Beak
            head_bob = math.sin(v.wing_phase * 0.5) * 1.5 if v.state == "landed" else 0.0
            painter.setPen(QPen(QColor("#0369A1"), 1))
            painter.setBrush(QColor("#38BDF8"))
            painter.drawEllipse(QRectF(4, -9 + head_bob, 9, 9))

            painter.setPen(QPen(QColor("#D97706"), 1))
            painter.setBrush(QColor("#F59E0B"))
            painter.drawPolygon([QPointF(12, -5 + head_bob), QPointF(16, -3.5 + head_bob), QPointF(12, -2 + head_bob)])

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(QRectF(7, -7 + head_bob, 2.5, 2.5))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(8, -6.5 + head_bob, 1, 1))

        elif v.v_type == "cat_paw":
            # 🐾 Curious Kitty Paw (길고양이 젤리 발)
            painter.setPen(QPen(QColor("#E2E8F0"), 1.2))
            grad_paw = QLinearGradient(0, 0, 25, -25)
            grad_paw.setColorAt(0.0, QColor("#FFFFFF"))
            grad_paw.setColorAt(1.0, QColor("#F8FAFC"))
            painter.setBrush(QBrush(grad_paw))

            arm_path = QPainterPath()
            arm_path.moveTo(-10, -5)
            arm_path.lineTo(25, -30)
            arm_path.lineTo(35, -20)
            arm_path.lineTo(5, 5)
            arm_path.closeSubpath()
            painter.drawPath(arm_path)

            painter.drawEllipse(QRectF(-12, -8, 18, 16))

            # Pink Main Bean Pad
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F472B6"))
            painter.drawEllipse(QRectF(-7, -4, 9, 8))

            # 4 Pink Squishy Toe Beans
            painter.drawEllipse(QRectF(-11, -9, 3.5, 4))
            painter.drawEllipse(QRectF(-7, -12, 3.8, 4.2))
            painter.drawEllipse(QRectF(-2, -12, 3.8, 4.2))
            painter.drawEllipse(QRectF(2, -9, 3.5, 4))

        elif v.v_type == "rain_cloud":
            # 🌧️ Rain Cloud & 🌈 Mini Rainbow
            painter.setPen(QPen(QColor("#CBD5E1"), 1.2))
            grad_cloud = QLinearGradient(-15, -10, 15, 10)
            grad_cloud.setColorAt(0.0, QColor(255, 255, 255, 240))
            grad_cloud.setColorAt(1.0, QColor(226, 232, 240, 240))
            painter.setBrush(QBrush(grad_cloud))

            painter.drawEllipse(QRectF(-18, -6, 16, 13))
            painter.drawEllipse(QRectF(-8, -12, 18, 17))
            painter.drawEllipse(QRectF(4, -7, 16, 14))

            # Falling Raindrops
            painter.setPen(QPen(QColor("#38BDF8"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for i, drop_x in enumerate([-12, -4, 4, 12]):
                rain_y = 6 + (int(v.frame * 2 + i * 8) % 24)
                painter.drawLine(drop_x, rain_y, drop_x - 1, rain_y + 4)

            # Mini Rainbow Arc
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rb_colors = ["#F87171", "#FBBF24", "#34D399", "#60A5FA", "#A78BFA"]
            for r_idx, c_hex in enumerate(rb_colors):
                r_pen = QPen(QColor(c_hex), 1.5)
                painter.setPen(r_pen)
                painter.drawArc(-14 + r_idx, -18 + r_idx, 28 - r_idx * 2, 24 - r_idx * 2, 20 * 16, 140 * 16)

        elif v.v_type == "firefly":
            # ✨ Swarm of 3 Glowing Fireflies
            for i in range(3):
                phase = v.wing_phase * 0.6 + (i * 2.094)
                ff_x = math.sin(phase) * 28.0 + math.cos(phase * 0.5) * 6.0
                ff_y = math.cos(phase * 0.8) * 18.0 + math.sin(phase * 0.3) * 6.0

                glow_r = 6.0 + math.sin(v.wing_phase + i) * 2.0
                grad_glow = QRadialGradient(ff_x, ff_y, glow_r)
                grad_glow.setColorAt(0.0, QColor(253, 224, 71, 190))
                grad_glow.setColorAt(1.0, QColor(250, 204, 21, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(grad_glow))
                painter.drawEllipse(QPointF(ff_x, ff_y), glow_r, glow_r)

                painter.setBrush(QColor("#FEF08A"))
                painter.drawEllipse(QPointF(ff_x, ff_y), 2.0, 2.0)

        else:  # butterfly
            # 🦋 Delicate Fluttering Butterfly
            wing_scale = abs(math.cos(v.wing_phase * 0.6))
            painter.save()
            painter.scale(max(0.2, wing_scale), 1)
            
            grad_l = QLinearGradient(-15, -15, 0, 15)
            grad_l.setColorAt(0.0, QColor("#A78BFA"))
            grad_l.setColorAt(1.0, QColor("#F472B6"))

            painter.setPen(QPen(QColor("#7C3AED"), 1))
            painter.setBrush(QBrush(grad_l))

            painter.drawEllipse(QRectF(-14, -12, 13, 15))
            painter.drawEllipse(QRectF(-11, 1, 10, 11))
            painter.drawEllipse(QRectF(1, -12, 13, 15))
            painter.drawEllipse(QRectF(1, 1, 10, 11))
            painter.restore()

            painter.setPen(QPen(QColor("#1E1B4B"), 1.5))
            painter.drawLine(0, -7, 0, 8)
            painter.drawLine(0, -7, -3, -11)
            painter.drawLine(0, -7, 3, -11)

        painter.restore()

    def _draw_facial_expression(self, painter: QPainter, px: int, py: int, sprite_w: int):
        """Draws animated eyes/mouth overlay on the flowerpot face without moving the pot."""
        try:
            if sprite_w <= 0 or self.expr_total_frames <= 0:
                return
            scale = max(0.1, sprite_w / 200.0)
            progress = max(0.0, min(1.0, self.expr_frame / float(self.expr_total_frames)))

            # Precise Face anchor coordinates (derived from sprite pixel map)
            lx = px + int(89 * scale)   # Left eye center X
            rx = px + int(111 * scale)  # Right eye center X
            ey = py + int(162 * scale)  # Eye vertical center Y
            mx = px + int(100 * scale)  # Mouth center X
            my = py + int(171 * scale)  # Mouth center Y (Actual PNG smile center is y=171.5)

            eye_radius = max(2, int(5 * scale))
            pen_dark = QPen(QColor("#3E2723"), max(2.0, 2.4 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            brush_dark = QBrush(QColor("#3E2723"))
            brush_pot = QBrush(QColor("#D27D46"))  # Exact Pot surface color to 100% mask default face

            # 1. Mask default eyes & red smiling mouth so no ghost/duplicate mouth is visible
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush_pot)
            painter.drawEllipse(QPointF(lx, ey), 8.0 * scale, 8.0 * scale)
            painter.drawEllipse(QPointF(rx, ey), 8.0 * scale, 8.0 * scale)
            # Generous mouth mask covering full red smile area (x: 87..113, y: 164..179)
            mouth_mask_rect = QRectF(mx - 13.5 * scale, my - 7.5 * scale, 27.0 * scale, 15.0 * scale)
            painter.drawRoundedRect(mouth_mask_rect, 6.0 * scale, 6.0 * scale)

            # --- A. BLINK (눈 깜빡임) ---
            if self.expr_type == "blink":
                # Natural double-blink timing curve
                is_closed = (4 <= self.expr_frame <= 12) or (18 <= self.expr_frame <= 24)
                if is_closed:
                    # Closed happy curve eyes: ⌒  ⌒
                    painter.setPen(pen_dark)
                    arc_w = max(4, int(10 * scale))
                    arc_h = max(3, int(6 * scale))
                    painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                    painter.drawArc(rx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                else:
                    # Open round eyes with white reflection dot
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(brush_dark)
                    painter.drawEllipse(QPoint(lx, ey), eye_radius, eye_radius)
                    painter.drawEllipse(QPoint(rx, ey), eye_radius, eye_radius)
                    # White eye highlights
                    painter.setBrush(QBrush(QColor("#FFFFFF")))
                    painter.drawEllipse(QPoint(lx - max(1, int(1.5*scale)), ey - max(1, int(1.5*scale))), max(1, int(1.8*scale)), max(1, int(1.8*scale)))
                    painter.drawEllipse(QPoint(rx - max(1, int(1.5*scale)), ey - max(1, int(1.5*scale))), max(1, int(1.8*scale)), max(1, int(1.8*scale)))

                # Sweet smile mouth
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(7*scale), my - int(4*scale), max(8, int(14*scale)), max(5, int(8*scale)), 0, -180*16)

            # --- B. YAWN (하품 & 졸림) ---
            elif self.expr_type == "yawn":
                # Sleepy eyes
                painter.setPen(pen_dark)
                arc_w = max(4, int(10 * scale))
                arc_h = max(3, int(7 * scale))
                painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                painter.drawArc(rx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)

                # Mouth opens wide then closes
                sine_open = math.sin(progress * math.pi)
                mouth_w = max(4, int((8 + 4 * sine_open) * scale))
                mouth_h = max(3, int((6 + 8 * sine_open) * scale))

                painter.setPen(QPen(QColor("#2C1810"), max(1.5, 2.0 * scale)))
                painter.setBrush(QBrush(QColor("#3E2723")))
                painter.drawEllipse(QPointF(mx, my), mouth_w / 2.0, mouth_h / 2.0)

                # Little pink tongue inside yawn mouth
                if sine_open > 0.4:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor("#FF8A80")))
                    painter.drawEllipse(QPointF(mx, my + (mouth_h * 0.2)), max(2, int(mouth_w * 0.35)), max(2, int(mouth_h * 0.25)))

                # Floating sleepy "zZZ" indicator
                if progress > 0.25:
                    painter.setFont(QFont("Malgun Gothic", max(8, int(9 * scale)), QFont.Weight.Bold))
                    painter.setPen(QColor(100, 116, 139, int(220 * sine_open)))
                    float_y = my - int((18 + 15 * progress) * scale)
                    painter.drawText(mx + int(14 * scale), float_y, "zZZ")

            # --- C. TONGUE OUT (메롱 😋) ---
            elif self.expr_type == "tongue":
                # Left eye wink (⌒), Right eye sparkle open (⊙)
                painter.setPen(pen_dark)
                arc_w = max(4, int(10 * scale))
                arc_h = max(3, int(6 * scale))
                painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)

                # Right eye open with sparkle
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_dark)
                painter.drawEllipse(QPoint(rx, ey), eye_radius, eye_radius)
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.drawEllipse(QPoint(rx - max(1, int(1.5*scale)), ey - max(1, int(1.5*scale))), max(1, int(2*scale)), max(1, int(2*scale)))

                # Cute wide smile mouth
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(9*scale), my - int(4*scale), max(10, int(18*scale)), max(5, int(9*scale)), 0, -180*16)

                # Cute pink tongue sticking out downwards (메롱)
                tongue_len = max(2.0, 7.5 * scale * min(1.0, progress * 3.0))
                tongue_w = max(3.0, 7.5 * scale)
                tongue_rect = QRectF(mx - tongue_w / 2.0, my - 1.0 * scale, tongue_w, tongue_len)
                painter.setPen(QPen(QColor("#D32F2F"), max(1.0, 1.2 * scale)))
                painter.setBrush(QBrush(QColor("#FF5252")))
                painter.drawRoundedRect(tongue_rect, tongue_w / 2.0, tongue_w / 2.0)

                # Rosy blushing cheeks
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 138, 128, 180))
                painter.drawEllipse(QPoint(px + int(76*scale), py + int(165*scale)), max(2, int(5*scale)), max(2, int(3.5*scale)))
                painter.drawEllipse(QPoint(px + int(124*scale), py + int(165*scale)), max(2, int(5*scale)), max(2, int(3.5*scale)))

            # --- D. WINK & BLUSH (윙크 & 방긋) ---
            elif self.expr_type == "wink":
                # Left eye wink (⌒), Right eye open (●)
                painter.setPen(pen_dark)
                arc_w = max(4, int(10 * scale))
                arc_h = max(3, int(6 * scale))
                painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_dark)
                painter.drawEllipse(QPoint(rx, ey), eye_radius, eye_radius)
                painter.setBrush(QBrush(QColor("#FFFFFF")))
                painter.drawEllipse(QPoint(rx - max(1, int(1.5*scale)), ey - max(1, int(1.5*scale))), max(1, int(2*scale)), max(1, int(2*scale)))

                # Happy open smile
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(8*scale), my - int(4*scale), max(8, int(16*scale)), max(5, int(9*scale)), 0, -180*16)

                # Blushing rosy glow
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 138, 128, 200))
                painter.drawEllipse(QPoint(px + int(76*scale), py + int(165*scale)), max(2, int(5.5*scale)), max(2, int(4*scale)))
                painter.drawEllipse(QPoint(px + int(124*scale), py + int(165*scale)), max(2, int(5.5*scale)), max(2, int(4*scale)))

            # --- E. HAPPY / SQUEE (방긋방긋) ---
            else:
                # Both eyes happy curves ⌒  ⌒
                painter.setPen(pen_dark)
                arc_w = max(4, int(10 * scale))
                arc_h = max(3, int(7 * scale))
                painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                painter.drawArc(rx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)

                # Wide joyful smile
                painter.drawArc(mx - int(9*scale), my - int(4*scale), max(10, int(18*scale)), max(6, int(11*scale)), 0, -180*16)

                # Rosy cheeks
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 138, 128, 190))
                painter.drawEllipse(QPoint(px + int(76*scale), py + int(165*scale)), max(2, int(5*scale)), max(2, int(3.5*scale)))
                painter.drawEllipse(QPoint(px + int(124*scale), py + int(165*scale)), max(2, int(5*scale)), max(2, int(3.5*scale)))
        except Exception as e:
            pass
