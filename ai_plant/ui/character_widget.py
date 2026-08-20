"""
Plant Character Widget
Renders stage-based plant sprite with rich animated facial expressions on the flowerpot:
- 10 Dynamic Face Expressions: Blink, Yawn, Blep/Tongue, Wink, Sparkle Joy, Cool Sunglasses, Curious Tilt, Singing Melody, Cheer Up, Relieved/Sweat
- 20 Environmental Eco-Visitors (Pests with escape penalty & friendly creatures)
- 10 Emotion Particle Effects
"""
import os
import math
import random
from typing import Optional, Dict, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QPointF, QRectF
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPen, QBrush,
    QPainterPath, QLinearGradient, QRadialGradient, QPolygonF
)
from ..config import get_resource_path
from ..shop_data import SAUCER_CATALOG, PET_CATALOG

PEST_TYPES = {"bug", "aphid", "snail", "locust"}
ALL_VISITOR_TYPES = [
    "bee", "bug", "aphid", "snail", "locust",
    "butterfly", "ladybug", "bird", "cat_paw", "rain_cloud",
    "firefly", "ant", "frog", "squirrel", "shooting_star",
    "forest_fairy", "puppy_nose", "dandelion", "coffee", "heart_balloon"
]


class FloatingParticle:
    def __init__(self, pixmap: QPixmap, start_pos: QPoint):
        self.pixmap = pixmap
        self.x = float(start_pos.x() + random.randint(-14, 14))
        self.y = float(start_pos.y())
        self.vy = -2.2 - random.random() * 1.2
        self.alpha = 255.0
        self.fade_rate = 8.0
        self.alive = True

    def update(self):
        self.y += self.vy
        self.alpha -= self.fade_rate
        if self.alpha <= 0:
            self.alive = False


class EcoVisitor:
    """
    20 Animated Environmental Creatures & Magical Eco-Events:
    - Pests: 🐛 Bug (애벌레), 🌱 Aphid (진딧물), 🐌 Snail (달팽이), 🦗 Locust (메뚜기)
    - Friendly: 🐝 Bee, 🦋 Butterfly, 🐞 Ladybug, 🐦 Bluebird, 🐾 Cat Paw, 🌧️ Rain Cloud,
                ✨ Fireflies, 🐜 Ant, 🐸 Frog, 🐿️ Squirrel, 🌠 Shooting Star, 🧚 Fairy,
                🐕 Puppy Nose, 🌾 Dandelion, ☕ Coffee, 🎈 Heart Balloon
    """
    def __init__(self, v_type: str, canvas_w: int, canvas_h: int):
        self.v_type = v_type if v_type in ALL_VISITOR_TYPES else "bee"
        self.is_pest = self.v_type in PEST_TYPES
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.alive = True
        self.frame = 0
        self.total_frames = random.randint(220, 290)
        self.wing_phase = 0.0
        self.crawl_angle = 0.0
        self.state = "fly_in"  # "fly_in", "landed", "fly_out", "fleeing"
        self.is_fleeing = False
        self.has_escaped_reported = False

        self.side = random.choice([-1, 1])

        # Initial coordinates based on visitor type
        if self.v_type in ["bug", "snail", "aphid", "locust"]:
            # Pests crawl or hop up the pot from bottom
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
        elif self.v_type in ["ant", "frog", "squirrel"]:
            # Ground creatures walking beside the pot
            self.start_x = -18.0 if self.side < 0 else float(canvas_w + 18)
            self.start_y = float(canvas_h - 10)
            self.target_x = float(canvas_w // 2 + self.side * 28)
            self.target_y = float(canvas_h - 10)
            self.x, self.y = self.start_x, self.start_y
        elif self.v_type in ["cat_paw", "puppy_nose"]:
            # Reaching down from top or side
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
        elif self.v_type in ["shooting_star", "dandelion", "heart_balloon", "coffee"]:
            # Floating / drifting items
            self.start_x = -20.0 if self.side < 0 else float(canvas_w + 20)
            self.start_y = float(random.randint(10, 30))
            self.target_x = float(canvas_w // 2 + random.randint(-20, 20))
            self.target_y = float(canvas_h // 2 - random.randint(10, 30))
            self.x, self.y = self.start_x, self.start_y
        else:
            # Flying creatures (bee, butterfly, ladybug, bird, firefly, forest_fairy)
            from_left = (self.side < 0)
            self.start_x = -25.0 if from_left else float(canvas_w + 25)
            self.start_y = float(random.randint(10, 40))
            self.target_x = float(canvas_w // 2 + random.randint(-22, 22))
            self.target_y = float(canvas_h // 2 - random.randint(12, 32))
            self.x, self.y = self.start_x, self.start_y

    def update(self):
        self.frame += 1
        self.wing_phase += 0.45

        # 1. Fleeing / Scared Behavior
        if self.is_fleeing:
            if self.is_pest:
                # Drop to taskbar and run away rapidly
                self.y = min(float(self.canvas_h - 6), self.y + 4.0)
                self.x += (-5.5 if self.side < 0 else 5.5)
                self.crawl_angle = 0.0
                if self.x < -35 or self.x > self.canvas_w + 35:
                    self.alive = False
                return
            else:
                self.y -= 4.5
                self.x += (3.5 if self.x > self.canvas_w // 2 else -3.5)
                if self.y < -40 or self.x < -50 or self.x > self.canvas_w + 50:
                    self.alive = False
                return

        # 2. Ground & Pot-climbing Pests State Machine (bug, aphid, snail, locust)
        if self.is_pest:
            p1 = 45                               # Crawl to pot base
            p2 = 85                               # Climb up pot wall
            p3 = 110                              # Reach leaf
            p4 = self.total_frames - 70           # Nibble on leaf
            p5 = self.total_frames - 35           # Climb down
            p6 = self.total_frames                # Crawl away

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
                dest_x = -35.0 if self.side < 0 else float(self.canvas_w + 35)
                self.x = self.pot_base_x + (dest_x - self.pot_base_x) * t
                self.y = float(self.canvas_h - 6)
                self.crawl_angle = 0.0
                if self.frame >= self.total_frames:
                    self.alive = False
            return

        # 3. Ground / Floating Simple Drifters
        if self.v_type == "rain_cloud":
            t = self.frame / float(self.total_frames)
            self.x = -35.0 + t * (self.canvas_w + 70.0)
            self.y = 18.0 + math.sin(t * math.pi * 2) * 2.0
            if self.frame >= self.total_frames:
                self.alive = False
            return

        if self.v_type in ["ant", "frog", "squirrel"]:
            in_frames = 60
            out_start = self.total_frames - 50
            if self.frame < in_frames:
                t = self.frame / float(in_frames)
                self.x = self.start_x + (self.target_x - self.start_x) * math.sin(t * math.pi / 2.0)
                self.y = float(self.canvas_h - 10) + math.sin(t * math.pi * 4) * (2.0 if self.v_type == "frog" else 0.5)
            elif self.frame < out_start:
                self.state = "landed"
                self.x = self.target_x
                self.y = float(self.canvas_h - 10)
            else:
                t = (self.frame - out_start) / 50.0
                dest_x = -30.0 if self.side < 0 else float(self.canvas_w + 30)
                self.x = self.target_x + (dest_x - self.target_x) * (t * t)
                if self.frame >= self.total_frames:
                    self.alive = False
            return

        # 4. Standard Flying & Floating Visitors
        in_frames = 55
        out_start = self.total_frames - 55

        if self.frame < in_frames:
            self.state = "fly_in"
            t = self.frame / float(in_frames)
            t_ease = math.sin(t * math.pi / 2.0)
            self.x = self.start_x + (self.target_x - self.start_x) * t_ease
            sine_wave = math.sin(t * math.pi * 3) * 6.0
            self.y = self.start_y + (self.target_y - self.start_y) * t_ease + sine_wave
        elif self.frame < out_start:
            self.state = "landed"
            hover_amp = 1.4 if self.v_type not in ["bird", "cat_paw", "puppy_nose"] else 0.4
            self.x = self.target_x + math.sin(self.wing_phase * 0.3) * hover_amp
            self.y = self.target_y + math.cos(self.wing_phase * 0.4) * hover_amp
        elif self.frame < self.total_frames:
            self.state = "fly_out"
            t = (self.frame - out_start) / 55.0
            dest_x = -40.0 if self.target_x < self.canvas_w // 2 else float(self.canvas_w + 40)
            dest_y = -35.0
            self.x = self.target_x + (dest_x - self.target_x) * (t * t)
            sine_wave = math.sin(t * math.pi * 3) * 4.0
            self.y = self.target_y + (dest_y - self.target_y) * (t * t) + sine_wave
        else:
            self.alive = False

    def hit_test(self, pos) -> bool:
        px = pos.x() if hasattr(pos, "x") else pos[0]
        py = pos.y() if hasattr(pos, "y") else pos[1]
        dist = math.hypot(px - self.x, py - self.y)
        hit_radius = 28.0 if self.v_type in ["rain_cloud", "bird", "cat_paw", "puppy_nose", "frog", "squirrel"] else 22.0
        return dist <= hit_radius

    def flee(self):
        self.is_fleeing = True


class PlantCharacterWidget(QWidget):
    clicked = Signal()
    bug_cleared = Signal(str)         # pest_type ("bug", "aphid", "snail", "locust")
    pest_escaped = Signal(str)        # pest_type
    visitor_greeted = Signal(str)     # friendly visitor type
    eco_visitor_arrived = Signal(str) # visitor type
    pet_clicked = Signal(str)         # pet_id ("cat_calico", "dog_shiba", etc.)

    def __init__(self, parent=None, scale_pct: int = 100, width: int = 240, height: int = 135):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scale_pct = max(60, min(160, scale_pct))
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.current_stage = 1
        self.current_species = "classic"
        self.pixmaps = {}
        self.particle_pixmaps = {}
        self.particles: List[FloatingParticle] = []

        # Shop Equipment: Saucers & Pet Companions
        self.equipped_saucer: str = "basic"
        self.equipped_pet: str = "none"
        self.pet_state: str = "sitting" # "walking", "sitting", "sleeping", "wandering", "greeting"
        self.pet_x: float = 36.0
        self.pet_target_x: float = 36.0
        self.pet_dir: int = 1
        self.pet_frame: int = 0
        self.pet_state_timer: int = 0

        # Eco-Visitor System (20 types)
        self.eco_visitor: Optional[EcoVisitor] = None
        self.eco_spawn_timer = QTimer(self)
        self.eco_spawn_timer.setSingleShot(True)
        self.eco_spawn_timer.timeout.connect(self._spawn_random_eco_visitor)

        # Dynamic 10-Facial Expression System
        self.idle_trigger_timer = QTimer(self)
        self.idle_trigger_timer.setSingleShot(True)
        self.idle_trigger_timer.timeout.connect(self._trigger_random_expression)

        # Master Animation Loop (30 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_master_anim_tick)

        self.expr_type = "none"
        self.expr_frame = 0
        self.expr_total_frames = 35

        self.load_resources("classic")
        self._schedule_next_expression()
        self._schedule_next_eco_visitor()

    def set_equipped_saucer(self, saucer_id: str):
        """Set active pot saucer underneath the flowerpot."""
        self.equipped_saucer = saucer_id
        self.update()

    def set_equipped_pet(self, pet_id: str):
        """Set active pet companion roaming around the flowerpot."""
        self.equipped_pet = pet_id
        self.pet_state = "sitting"
        self.pet_x = 36.0
        self.pet_target_x = 36.0
        self.pet_state_timer = 0
        self._ensure_master_anim_running()
        self.update()

    def set_scale(self, scale_pct: int):
        self.scale_pct = max(60, min(160, scale_pct))
        s = self.scale_pct / 100.0
        w = max(240, int(240 * s))
        h = max(135, int(135 * s))
        self.setFixedSize(w, h)
        self.load_resources(self.current_species)
        self.update()

    def set_scale_and_size(self, scale_pct: int, w: int, h: int):
        self.scale_pct = max(60, min(160, scale_pct))
        self.setFixedSize(w, h)
        self.load_resources(self.current_species)
        if self.pet_x < 18.0 or self.pet_x > self.width() - 18:
            self.pet_x = 36.0
        self.update()

    def load_resources(self, species: str = "classic"):
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

        # Load all 10 reaction particles
        part_sz = max(18, int(22 * (self.scale_pct / 100.0)))
        all_particles = ["heart", "drop", "sun", "star", "note", "clover", "petal", "sweat", "sparkle", "coffee"]
        for p_name in all_particles:
            path = get_resource_path(os.path.join("assets", f"{p_name}.png"))
            if os.path.exists(path):
                pm = QPixmap(path).scaled(
                    part_sz, part_sz,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.particle_pixmaps[p_name] = pm

    def set_stage(self, stage: int):
        self.current_stage = max(1, min(6, stage))
        self.update()

    def set_species(self, species: str):
        self.load_resources(species)
        self.update()

    def spawn_particle(self, p_type: str = "heart"):
        pix = self.particle_pixmaps.get(p_type) or self.particle_pixmaps.get("heart")
        if pix and not pix.isNull():
            start_x = self.width() // 2 - pix.width() // 2
            start_y = max(10, self.height() // 2 - 25)
            self.particles.append(FloatingParticle(pix, QPoint(start_x, start_y)))
            self._ensure_master_anim_running()

    def _schedule_next_expression(self):
        next_sec = random.randint(7, 18)
        self.idle_trigger_timer.start(next_sec * 1000)

    def _trigger_random_expression(self):
        expressions = ["blink", "yawn", "tongue", "wink", "sparkle", "sunglasses", "curious", "melody", "cheer", "sweat_pout"]
        self.expr_type = random.choice(expressions)
        self.expr_frame = 0
        if self.expr_type == "sunglasses":
            self.expr_total_frames = 65
        elif self.expr_type in ["yawn", "cheer"]:
            self.expr_total_frames = 45
        elif self.expr_type in ["blink", "wink"]:
            self.expr_total_frames = 25
        else:
            self.expr_total_frames = 38
        self._ensure_master_anim_running()

    def trigger_interaction_face(self, face_type: str):
        self.idle_trigger_timer.stop()
        self.expr_type = face_type
        self.expr_frame = 0
        self.expr_total_frames = 40
        self._ensure_master_anim_running()

    def _schedule_next_eco_visitor(self):
        next_sec = random.randint(25, 75)
        self.eco_spawn_timer.start(next_sec * 1000)

    def _spawn_random_eco_visitor(self):
        v_type = random.choice(ALL_VISITOR_TYPES)
        self.eco_visitor = EcoVisitor(v_type, self.width(), self.height())
        self.eco_visitor_arrived.emit(v_type)
        self._ensure_master_anim_running()

    def _ensure_master_anim_running(self):
        if not self.anim_timer.isActive():
            self.anim_timer.start(33)

    def _on_master_anim_tick(self):
        try:
            has_active_anim = False

            # 1. Particles
            if self.particles:
                alive_particles = []
                for p in self.particles:
                    p.update()
                    if p.alive:
                        alive_particles.append(p)
                self.particles = alive_particles
                if self.particles:
                    has_active_anim = True

            # 2. Facial Expression
            if self.expr_type != "none":
                self.expr_frame += 1
                if self.expr_frame >= self.expr_total_frames:
                    self.expr_type = "none"
                    self.expr_frame = 0
                    self._schedule_next_expression()
                else:
                    has_active_anim = True

            # 3. Eco-Visitor & Pest Escaped Penalty Trigger
            if self.eco_visitor:
                self.eco_visitor.update()
                if self.eco_visitor.is_pest and not self.eco_visitor.is_fleeing and self.eco_visitor.frame >= self.eco_visitor.total_frames and not self.eco_visitor.has_escaped_reported:
                    self.eco_visitor.has_escaped_reported = True
                    self.pest_escaped.emit(self.eco_visitor.v_type)

                if not self.eco_visitor.alive:
                    self.eco_visitor = None
                    self._schedule_next_eco_visitor()
                else:
                    has_active_anim = True

            # 4. Pet Companion Behavior State Machine
            if self.equipped_pet != "none":
                has_active_anim = True
                self.pet_frame += 1
                self.pet_state_timer += 1

                if self.pet_state == "sitting":
                    if self.pet_state_timer > random.randint(140, 240):
                        r = random.random()
                        if r < 0.55:
                            self.pet_state = "walking"
                            target_left = random.randint(20, 52)
                            target_right = random.randint(max(60, self.width() - 52), max(65, self.width() - 20))
                            self.pet_target_x = float(random.choice([target_left, target_right]))
                            self.pet_dir = 1 if self.pet_target_x > self.pet_x else -1
                        elif r < 0.85:
                            self.pet_state = "sleeping"
                        else:
                            self.pet_state = "wandering"
                            self.pet_target_x = float(-25 if random.random() < 0.5 else self.width() + 25)
                            self.pet_dir = 1 if self.pet_target_x > self.pet_x else -1
                        self.pet_state_timer = 0

                elif self.pet_state == "walking":
                    dx = self.pet_target_x - self.pet_x
                    if abs(dx) < 1.0:
                        self.pet_state = "sitting"
                        self.pet_state_timer = 0
                    else:
                        self.pet_x += 0.7 * (1 if dx > 0 else -1)

                elif self.pet_state == "sleeping":
                    if self.pet_state_timer > random.randint(200, 360):
                        self.pet_state = "sitting"
                        self.pet_state_timer = 0

                elif self.pet_state == "wandering":
                    dx = self.pet_target_x - self.pet_x
                    if abs(dx) < 1.0:
                        if self.pet_state_timer > 90:
                            self.pet_state = "walking"
                            target_left = random.randint(20, 52)
                            target_right = random.randint(max(60, self.width() - 52), max(65, self.width() - 20))
                            self.pet_target_x = float(random.choice([target_left, target_right]))
                            self.pet_dir = 1 if self.pet_target_x > self.pet_x else -1
                            self.pet_state_timer = 0
                            self.spawn_particle("heart")
                    else:
                        self.pet_x += 0.8 * (1 if dx > 0 else -1)

                elif self.pet_state == "greeting":
                    if self.pet_state_timer > 35:
                        self.pet_state = "sitting"
                        self.pet_state_timer = 0

            if has_active_anim:
                self.update()
            else:
                self.anim_timer.stop()
                self.update()
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check click on active Pet Companion (on the floor)
            if self.equipped_pet != "none":
                pet_center_y = self.height() - 14
                dist_pet = math.hypot(event.pos().x() - self.pet_x, event.pos().y() - pet_center_y)
                if dist_pet <= 24.0:
                    self.pet_state = "greeting"
                    self.pet_state_timer = 0
                    self.spawn_particle("heart")
                    self.pet_clicked.emit(self.equipped_pet)
                    self._ensure_master_anim_running()
                    event.accept()
                    return

            # Check click on active Eco-Visitor
            if self.eco_visitor and self.eco_visitor.alive and self.eco_visitor.hit_test(event.pos()):
                v_type = self.eco_visitor.v_type
                if self.eco_visitor.is_pest:
                    self.eco_visitor.flee()
                    self.bug_cleared.emit(v_type)
                    self.spawn_particle("sparkle")
                    self.expr_type = "sparkle"
                    self.expr_frame = 0
                    self.expr_total_frames = 28
                else:
                    self.eco_visitor.flee()
                    self.visitor_greeted.emit(v_type)
                    self.spawn_particle("heart")
                    self.expr_type = "wink"
                    self.expr_frame = 0
                    self.expr_total_frames = 28

                self._ensure_master_anim_running()
                event.accept()
                return

            if self.parent():
                self.parent().mousePressEvent(event)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent():
                self.parent().mouseReleaseEvent(event)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Draw Plant Sprite & Saucer
        pix = self.pixmaps.get(self.current_stage)
        if pix and not pix.isNull():
            px = (self.width() - pix.width()) // 2
            # Leave 6px margin at bottom so saucer tray sits cleanly underneath the pot
            py = self.height() - pix.height() - 6

            # Underneath: Draw Saucer
            self._draw_saucer(painter, px, py, pix.width(), pix.height())

            painter.drawPixmap(px, py, pix)

            # 2. Draw 10-Facial Expression Overlay
            if self.expr_type != "none":
                self._draw_facial_expression(painter, px, py, pix.width())
        else:
            painter.setPen(QColor(46, 125, 50))
            painter.setBrush(QColor(129, 199, 132))
            painter.drawEllipse(30, 30, 100, 100)

        # 3. Draw Animated Pet Companion (고양이/강아지/토끼)
        if self.equipped_pet != "none":
            self._draw_pet_companion(painter)

        # 4. Draw 20 Eco-Visitors
        if self.eco_visitor and self.eco_visitor.alive:
            self._draw_eco_visitor(painter, self.eco_visitor)

        # 5. Draw Floating Particles
        for p in self.particles:
            painter.setOpacity(p.alpha / 255.0)
            painter.drawPixmap(int(p.x), int(p.y), p.pixmap)
            painter.setOpacity(1.0)

    def _draw_eco_visitor(self, painter: QPainter, v: EcoVisitor):
        painter.save()
        painter.translate(v.x, v.y)

        # 1. 🐝 Bee
        if v.v_type == "bee":
            wing_angle = math.sin(v.wing_phase) * 35.0
            painter.setBrush(QColor(224, 242, 254, 200))
            painter.setPen(QPen(QColor(186, 230, 253), 1))
            painter.drawEllipse(QRectF(-8, -10 + wing_angle * 0.1, 8, 10))
            painter.drawEllipse(QRectF(0, -10 - wing_angle * 0.1, 8, 10))
            painter.setPen(QPen(QColor("#78350F"), 1.2))
            painter.setBrush(QColor("#FBBF24"))
            painter.drawEllipse(QRectF(-10, -6, 20, 13))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1F2937"))
            painter.drawRoundedRect(QRectF(-4, -6, 3.5, 13), 1, 1)
            painter.drawRoundedRect(QRectF(2, -5.5, 3.5, 12), 1, 1)
            painter.drawEllipse(QRectF(7, -4, 5, 8))

        # 2. 🐛 Caterpillar / Bug (Pest)
        elif v.v_type == "bug":
            facing = 1 if ((v.side < 0 and v.state != "fly_out") or (v.side > 0 and v.state == "fly_out")) else -1
            painter.scale(facing, 1)
            painter.rotate(v.crawl_angle * facing)
            wiggle = math.sin(v.wing_phase * 0.9) * 2.0
            colors = ["#4D7C0F", "#65A30D", "#84CC16", "#A3E635"]
            for idx in range(4):
                seg_x = -idx * 4.2 + (wiggle * 0.3 if idx in [1, 2] else 0)
                seg_y = (abs(wiggle) * -1.5) if idx in [1, 2] else 0.0
                painter.setPen(QPen(QColor("#365314"), 1))
                painter.setBrush(QColor(colors[idx]))
                painter.drawEllipse(QRectF(seg_x - 3.5, seg_y - 3.5, 7, 7))
            painter.setBrush(QColor("#BEF264"))
            painter.drawEllipse(QRectF(2.5, -4.5, 8, 8))
            painter.setBrush(QColor("#1F2937"))
            painter.drawEllipse(QRectF(6.5, -3, 2, 2))

        # 3. 🌱 Aphids (Pest)
        elif v.v_type == "aphid":
            wiggle = math.sin(v.wing_phase * 0.8) * 1.5
            painter.setPen(QPen(QColor("#15803D"), 1))
            for i, (ax, ay) in enumerate([(-6, 2), (0, -2), (6, 3), (3, 7)]):
                painter.setBrush(QColor("#86EFAC" if i % 2 == 0 else "#4ADE80"))
                painter.drawEllipse(QRectF(ax + wiggle * 0.2, ay, 6, 7))
                painter.setBrush(QColor("#14532D"))
                painter.drawEllipse(QRectF(ax + 3, ay + 1, 1.5, 1.5))

        # 4. 🐌 Snail (Pest)
        elif v.v_type == "snail":
            painter.setPen(QPen(QColor("#78350F"), 1.2))
            painter.setBrush(QColor("#FDE68A"))
            painter.drawRoundedRect(QRectF(-12, 0, 22, 6), 3, 3)
            # Spiral shell
            painter.setBrush(QColor("#D97706"))
            painter.drawEllipse(QRectF(-8, -10, 14, 14))
            painter.setPen(QPen(QColor("#78350F"), 1.5))
            painter.drawArc(-5, -7, 8, 8, 0, 270 * 16)
            # Tentacles
            painter.drawLine(8, 0, 11, -5)
            painter.drawLine(6, 0, 8, -5)

        # 5. 🦗 Locust (Pest)
        elif v.v_type == "locust":
            painter.setPen(QPen(QColor("#166534"), 1.2))
            painter.setBrush(QColor("#22C55E"))
            painter.drawEllipse(QRectF(-10, -4, 18, 8))
            # Long bent legs
            painter.drawLine(-4, 0, -8, -8)
            painter.drawLine(-8, -8, -12, 4)
            painter.setBrush(QColor("#15803D"))
            painter.drawEllipse(QRectF(6, -5, 6, 7))

        # 6. 🦋 Butterfly
        elif v.v_type == "butterfly":
            wing_scale = abs(math.cos(v.wing_phase * 0.6))
            painter.save()
            painter.scale(max(0.2, wing_scale), 1)
            grad_l = QLinearGradient(-15, -15, 0, 15)
            grad_l.setColorAt(0.0, QColor("#A78BFA"))
            grad_l.setColorAt(1.0, QColor("#F472B6"))
            painter.setPen(QPen(QColor("#7C3AED"), 1))
            painter.setBrush(QBrush(grad_l))
            painter.drawEllipse(QRectF(-14, -12, 13, 15))
            painter.drawEllipse(QRectF(1, -12, 13, 15))
            painter.restore()
            painter.setPen(QPen(QColor("#1E1B4B"), 1.5))
            painter.drawLine(0, -7, 0, 8)

        # 7. 🐞 Ladybug
        elif v.v_type == "ladybug":
            painter.setPen(QPen(QColor("#991B1B"), 1))
            painter.setBrush(QColor("#EF4444"))
            painter.drawEllipse(QRectF(-7, -7, 14, 14))
            painter.setPen(QPen(QColor("#111827"), 1.2))
            painter.drawLine(-7, 0, 7, 0)
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(QPointF(-3, -3), 1.3, 1.3)
            painter.drawEllipse(QPointF(2, -3.5), 1.4, 1.4)
            painter.drawEllipse(QPointF(-3, 3), 1.3, 1.3)
            painter.drawEllipse(QPointF(2, 3.5), 1.4, 1.4)

        # 8. 🐦 Bluebird
        elif v.v_type == "bird":
            painter.setPen(QPen(QColor("#0369A1"), 1.2))
            painter.setBrush(QColor("#38BDF8"))
            painter.drawEllipse(QRectF(-8, -8, 17, 15))
            painter.setBrush(QColor("#F59E0B"))
            painter.drawPolygon([QPointF(10, -3), QPointF(15, -1), QPointF(10, 1)])
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(QRectF(6, -5, 2.5, 2.5))

        # 9. 🐾 Cat Paw
        elif v.v_type == "cat_paw":
            painter.setPen(QPen(QColor("#E2E8F0"), 1.2))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QRectF(-12, -8, 18, 16))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F472B6"))
            painter.drawEllipse(QRectF(-7, -4, 9, 8))
            for tx in [-10, -6, -2, 2]:
                painter.drawEllipse(QRectF(tx, -11, 3.5, 4))

        # 10. 🌧️ Rain Cloud
        elif v.v_type == "rain_cloud":
            painter.setPen(QPen(QColor("#CBD5E1"), 1.2))
            painter.setBrush(QColor(255, 255, 255, 240))
            painter.drawEllipse(QRectF(-16, -6, 15, 12))
            painter.drawEllipse(QRectF(-7, -12, 17, 16))
            painter.drawEllipse(QRectF(5, -7, 15, 13))
            painter.setPen(QPen(QColor("#38BDF8"), 1.5))
            for i, drop_x in enumerate([-10, -2, 6, 12]):
                rain_y = 6 + (int(v.frame * 2 + i * 8) % 20)
                painter.drawLine(drop_x, rain_y, drop_x - 1, rain_y + 4)

        # 11. ✨ Fireflies
        elif v.v_type == "firefly":
            for i in range(3):
                phase = v.wing_phase * 0.6 + (i * 2.094)
                ff_x = math.sin(phase) * 22.0
                ff_y = math.cos(phase * 0.8) * 14.0
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(253, 224, 71, 200))
                painter.drawEllipse(QPointF(ff_x, ff_y), 3.5, 3.5)

        # 12. 🐜 Ant
        elif v.v_type == "ant":
            painter.setPen(QPen(QColor("#1E293B"), 1))
            painter.setBrush(QColor("#334155"))
            painter.drawEllipse(QRectF(-9, -3, 6, 6))
            painter.drawEllipse(QRectF(-4, -2, 4, 4))
            painter.drawEllipse(QRectF(0, -3, 5, 5))
            # Green leaf crumb carried
            painter.setBrush(QColor("#10B981"))
            painter.drawEllipse(QRectF(2, -7, 6, 4))

        # 13. 🐸 Frog
        elif v.v_type == "frog":
            painter.setPen(QPen(QColor("#15803D"), 1.2))
            painter.setBrush(QColor("#22C55E"))
            painter.drawEllipse(QRectF(-10, -6, 20, 14))
            painter.drawEllipse(QRectF(-7, -11, 7, 7))
            painter.drawEllipse(QRectF(1, -11, 7, 7))
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(QRectF(-5, -9, 2.5, 2.5))
            painter.drawEllipse(QRectF(3, -9, 2.5, 2.5))

        # 14. 🐿️ Squirrel
        elif v.v_type == "squirrel":
            painter.setPen(QPen(QColor("#78350F"), 1.2))
            painter.setBrush(QColor("#B45309"))
            painter.drawEllipse(QRectF(-8, -6, 16, 14))
            # Bushy tail
            painter.drawEllipse(QRectF(-16, -14, 12, 16))
            # Acorn
            painter.setBrush(QColor("#D97706"))
            painter.drawEllipse(QRectF(4, -2, 6, 7))

        # 15. 🌠 Shooting Star
        elif v.v_type == "shooting_star":
            painter.setPen(QPen(QColor("#FBBF24"), 1.5))
            painter.drawLine(-18, -12, 6, 6)
            painter.setBrush(QColor("#FFD700"))
            painter.drawPolygon([QPointF(6, 2), QPointF(10, 6), QPointF(6, 10), QPointF(2, 6)])

        # 16. 🧚 Forest Fairy
        elif v.v_type == "forest_fairy":
            # Sparkling wings
            painter.setBrush(QColor(167, 243, 208, 180))
            painter.setPen(QPen(QColor(110, 231, 183), 1))
            painter.drawEllipse(QRectF(-12, -10, 10, 8))
            painter.drawEllipse(QRectF(2, -10, 10, 8))
            # Glowing body
            painter.setBrush(QColor("#FEF08A"))
            painter.drawEllipse(QRectF(-4, -6, 8, 11))

        # 17. 🐕 Puppy Nose
        elif v.v_type == "puppy_nose":
            painter.setPen(QPen(QColor("#78350F"), 1.2))
            painter.setBrush(QColor("#D97706"))
            painter.drawEllipse(QRectF(-12, -10, 24, 18))
            painter.setBrush(QColor("#1F2937"))
            painter.drawEllipse(QRectF(-5, -4, 10, 7))

        # 18. 🌾 Dandelion Fluff
        elif v.v_type == "dandelion":
            painter.setPen(QPen(QColor(255, 255, 255, 220), 1.2))
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                painter.drawLine(0, 0, int(8 * math.cos(rad)), int(8 * math.sin(rad)))
            painter.setBrush(QColor("#78350F"))
            painter.drawEllipse(QRectF(-1.5, 4, 3, 6))

        # 19. ☕ Coffee
        elif v.v_type == "coffee":
            painter.setPen(QPen(QColor("#78350F"), 1.2))
            painter.setBrush(QColor("#92400E"))
            painter.drawRoundedRect(QRectF(-8, -4, 16, 14), 3, 3)
            # Rising steam
            painter.setPen(QPen(QColor("#FBBF24"), 1.2))
            painter.drawArc(-5, -12, 6, 7, 0, 180 * 16)
            painter.drawArc(1, -12, 6, 7, 0, 180 * 16)

        # 20. 🎈 Heart Balloon
        else:
            painter.setPen(QPen(QColor("#DC2626"), 1))
            painter.setBrush(QColor("#F43F5E"))
            painter.drawEllipse(QRectF(-8, -12, 16, 15))
            painter.setPen(QPen(QColor("#CBD5E1"), 1))
            painter.drawLine(0, 3, math.sin(v.wing_phase * 0.5) * 3, 14)

        painter.restore()

    def _draw_facial_expression(self, painter: QPainter, px: int, py: int, sprite_w: int):
        """Draws 10 dynamic animated expressions overlay on the flowerpot."""
        try:
            if sprite_w <= 0 or self.expr_total_frames <= 0:
                return
            scale = max(0.1, sprite_w / 200.0)
            progress = max(0.0, min(1.0, self.expr_frame / float(self.expr_total_frames)))

            is_starlight = (self.species == "starlight_rose")

            if is_starlight:
                lx = px + int(88 * scale)
                rx = px + int(112 * scale)
                ey = py + int(174 * scale)
                mx = px + int(100 * scale)
                my = py + int(180 * scale)
                eye_radius = max(2, int(4.5 * scale))
                pen_dark = QPen(QColor("#FDE047"), max(1.8, 2.2 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                brush_dark = QBrush(QColor("#FEF08A"))
                brush_pot = QBrush(QColor("#4C1D95"))
                blush_brush = QBrush(QColor(232, 121, 249, 200))
                blush_lx = px + int(78 * scale)
                blush_rx = px + int(122 * scale)
                blush_y = py + int(176 * scale)
            else:
                lx = px + int(89 * scale)
                rx = px + int(111 * scale)
                ey = py + int(162 * scale)
                mx = px + int(100 * scale)
                my = py + int(171 * scale)
                eye_radius = max(2, int(5 * scale))
                pen_dark = QPen(QColor("#3E2723"), max(2.0, 2.4 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                brush_dark = QBrush(QColor("#3E2723"))
                brush_pot = QBrush(QColor("#D27D46"))
                blush_brush = QBrush(QColor(255, 138, 128, 200))
                blush_lx = px + int(76 * scale)
                blush_rx = px + int(124 * scale)
                blush_y = py + int(165 * scale)

            # 1. Mask default eyes & smile with accurate pot color
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush_pot)
            painter.drawEllipse(QPointF(lx, ey), 8.0 * scale, 8.0 * scale)
            painter.drawEllipse(QPointF(rx, ey), 8.0 * scale, 8.0 * scale)
            mouth_mask = QRectF(mx - 13.5 * scale, my - 7.5 * scale, 27.0 * scale, 15.0 * scale)
            painter.drawRoundedRect(mouth_mask, 6.0 * scale, 6.0 * scale)

            # 1. BLINK (눈 깜빡임)
            if self.expr_type == "blink":
                is_closed = (4 <= self.expr_frame <= 12) or (18 <= self.expr_frame <= 24)
                if is_closed:
                    painter.setPen(pen_dark)
                    arc_w = max(4, int(10 * scale))
                    arc_h = max(3, int(6 * scale))
                    painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                    painter.drawArc(rx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(brush_dark)
                    painter.drawEllipse(QPoint(lx, ey), eye_radius, eye_radius)
                    painter.drawEllipse(QPoint(rx, ey), eye_radius, eye_radius)
                    painter.setBrush(QColor("#FFFFFF") if not is_starlight else QColor("#1E1B4B"))
                    painter.drawEllipse(QPoint(lx - max(1, int(1.5*scale)), ey - max(1, int(1.5*scale))), max(1, int(1.8*scale)), max(1, int(1.8*scale)))
                    painter.drawEllipse(QPoint(rx - max(1, int(1.5*scale)), ey - max(1, int(1.5*scale))), max(1, int(1.8*scale)), max(1, int(1.8*scale)))
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(7*scale), my - int(4*scale), max(8, int(14*scale)), max(5, int(8*scale)), 0, -180*16)

            # 2. YAWN (하품 & zZZ)
            elif self.expr_type == "yawn":
                painter.setPen(pen_dark)
                arc_w = max(4, int(10 * scale))
                arc_h = max(3, int(7 * scale))
                painter.drawArc(lx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                painter.drawArc(rx - arc_w//2, ey - arc_h//2, arc_w, arc_h, 20 * 16, 140 * 16)
                sine_open = math.sin(progress * math.pi)
                mouth_w = max(4, int((8 + 4 * sine_open) * scale))
                mouth_h = max(3, int((6 + 8 * sine_open) * scale))
                painter.setBrush(brush_dark)
                painter.drawEllipse(QPointF(mx, my), mouth_w / 2.0, mouth_h / 2.0)
                if progress > 0.25:
                    painter.setFont(QFont("Malgun Gothic", max(8, int(9 * scale)), QFont.Weight.Bold))
                    painter.setPen(QColor(139, 92, 246, int(220 * sine_open)) if not is_starlight else QColor(253, 224, 71, int(220 * sine_open)))
                    painter.drawText(mx + int(14 * scale), my - int((18 + 15 * progress) * scale), "zZZ")

            # 3. TONGUE (메롱 😋)
            elif self.expr_type == "tongue":
                painter.setPen(pen_dark)
                painter.drawArc(lx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_dark)
                painter.drawEllipse(QPoint(rx, ey), eye_radius, eye_radius)
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(9*scale), my - int(4*scale), max(10, int(18*scale)), max(5, int(9*scale)), 0, -180*16)
                tongue_len = max(2.0, 7.5 * scale * min(1.0, progress * 3.0))
                tongue_w = max(3.0, 7.5 * scale)
                painter.setPen(QPen(QColor("#D32F2F"), 1))
                painter.setBrush(QColor("#FF5252"))
                painter.drawRoundedRect(QRectF(mx - tongue_w / 2.0, my - 1.0 * scale, tongue_w, tongue_len), tongue_w / 2.0, tongue_w / 2.0)

            # 4. WINK (윙크 & 볼홍조 💕)
            elif self.expr_type == "wink":
                painter.setPen(pen_dark)
                painter.drawArc(lx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_dark)
                painter.drawEllipse(QPoint(rx, ey), eye_radius, eye_radius)
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(8*scale), my - int(4*scale), max(8, int(16*scale)), max(5, int(9*scale)), 0, -180*16)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(blush_brush)
                painter.drawEllipse(QPoint(blush_lx, blush_y), max(2, int(5*scale)), max(2, int(3.5*scale)))
                painter.drawEllipse(QPoint(blush_rx, blush_y), max(2, int(5*scale)), max(2, int(3.5*scale)))

            # 5. SPARKLE JOY (초롱초롱 기쁨 ✨)
            elif self.expr_type == "sparkle":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#F59E0B") if not is_starlight else QColor("#FDE047"))
                for ex in [lx, rx]:
                    painter.drawPolygon([
                        QPointF(ex, ey - 5 * scale), QPointF(ex + 2 * scale, ey),
                        QPointF(ex + 5 * scale, ey), QPointF(ex + 2 * scale, ey + 2 * scale),
                        QPointF(ex, ey + 5 * scale), QPointF(ex - 2 * scale, ey + 2 * scale),
                        QPointF(ex - 5 * scale, ey), QPointF(ex - 2 * scale, ey)
                    ])
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(8*scale), my - int(5*scale), max(10, int(16*scale)), max(6, int(11*scale)), 0, -180*16)

            # 6. SUNGLASSES (멋쟁이 힙스터 😎)
            elif self.expr_type == "sunglasses":
                painter.setPen(QPen(QColor("#111827"), max(1.5, 2.0 * scale)))
                painter.setBrush(QColor("#1F2937"))
                painter.drawRoundedRect(QRectF(lx - 7 * scale, ey - 5 * scale, 14 * scale, 10 * scale), 2, 2)
                painter.drawRoundedRect(QRectF(rx - 7 * scale, ey - 5 * scale, 14 * scale, 10 * scale), 2, 2)
                painter.drawLine(lx + 7 * scale, ey - 1 * scale, rx - 7 * scale, ey - 1 * scale)
                painter.setPen(QPen(QColor("#FFFFFF"), 1))
                painter.drawLine(lx - 4 * scale, ey - 3 * scale, lx + 2 * scale, ey + 3 * scale)
                painter.drawLine(rx - 4 * scale, ey - 3 * scale, rx + 2 * scale, ey + 3 * scale)
                painter.setPen(pen_dark)
                painter.drawLine(mx - int(5*scale), my + int(1*scale), mx + int(6*scale), my - int(1*scale))

            # 7. CURIOUS (호기심 갸웃 🤔)
            elif self.expr_type == "curious":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(brush_dark)
                painter.drawEllipse(QPoint(lx, ey - int(2*scale)), int(eye_radius * 1.2), int(eye_radius * 1.2))
                painter.drawEllipse(QPoint(rx, ey + int(1*scale)), int(eye_radius * 0.7), int(eye_radius * 0.7))
                painter.drawEllipse(QPointF(mx, my), 2.5 * scale, 2.5 * scale)
                painter.setFont(QFont("Malgun Gothic", max(9, int(11 * scale)), QFont.Weight.Bold))
                painter.setPen(QColor("#2563EB") if not is_starlight else QColor("#A78BFA"))
                painter.drawText(mx + int(12 * scale), ey - int(8 * scale), "?")

            # 8. MELODY (노래 흥얼흥얼 🎵)
            elif self.expr_type == "melody":
                painter.setPen(pen_dark)
                painter.drawArc(lx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.drawArc(rx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.drawEllipse(QPointF(mx, my), 3.0 * scale, 3.0 * scale)
                painter.setFont(QFont("Malgun Gothic", max(8, int(10 * scale))))
                painter.setPen(QColor("#8B5CF6") if not is_starlight else QColor("#FDE047"))
                painter.drawText(mx + int(10 * scale), ey - int(10 * scale + progress * 6 * scale), "🎵")

            # 9. CHEER (불끈 파이팅 🔥)
            elif self.expr_type == "cheer":
                painter.setPen(pen_dark)
                painter.drawLine(lx - int(5*scale), ey - int(2*scale), lx + int(5*scale), ey + int(1*scale))
                painter.drawLine(rx - int(5*scale), ey + int(1*scale), rx + int(5*scale), ey - int(2*scale))
                painter.setPen(pen_dark)
                painter.drawArc(mx - int(7*scale), my - int(4*scale), int(14*scale), int(9*scale), 0, -180*16)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(239, 68, 68, 180) if not is_starlight else blush_brush)
                painter.drawEllipse(QPoint(blush_lx, blush_y), max(2, int(5*scale)), max(2, int(3.5*scale)))
                painter.drawEllipse(QPoint(blush_rx, blush_y), max(2, int(5*scale)), max(2, int(3.5*scale)))

            # 10. SWEAT POUT (안도/머쓱 😌)
            elif self.expr_type == "sweat_pout":
                painter.setPen(pen_dark)
                painter.drawArc(lx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.drawArc(rx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.drawArc(mx - int(6*scale), my - int(3*scale), int(12*scale), int(6*scale), 0, -180*16)
                painter.setPen(QPen(QColor("#0284C7"), 1))
                painter.setBrush(QColor("#38BDF8"))
                painter.drawEllipse(QRectF(rx + int(9*scale), ey - int(8*scale), 4*scale, 6*scale))
            # DEFAULT / HAPPY
            else:
                painter.setPen(pen_dark)
                painter.drawArc(lx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.drawArc(rx - int(5*scale), ey - int(3*scale), int(10*scale), int(6*scale), 20 * 16, 140 * 16)
                painter.drawArc(mx - int(8*scale), my - int(4*scale), max(10, int(16*scale)), max(6, int(10*scale)), 0, -180*16)
        except Exception:
            pass

    def _draw_saucer(self, painter: QPainter, px: int, py: int, pw: int, ph: int):
        """Draw equipped pot saucer (화분 받침대) directly underneath the pot base."""
        painter.save()
        base_cx = px + pw * 0.5
        pot_bottom_y = py + ph - 2.0
        s_id = self.equipped_saucer if self.equipped_saucer not in ["none", ""] else "basic"

        # Wide saucer plate supporting the pot base cleanly
        tray_w = max(74.0, pw * 0.74)
        tray_h = 7.8
        tray_rect = QRectF(base_cx - tray_w / 2, pot_bottom_y - 1.0, tray_w, tray_h)
        lip_rect = QRectF(base_cx - (tray_w + 6) / 2, pot_bottom_y - 2.2, tray_w + 6, 3.2)

        if s_id in ["basic", "none", ""]:
            # 1. Warm Terracotta Ceramic Saucer (포근한 기본 도자기 받침대)
            painter.setBrush(QColor(0, 0, 0, 45))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tray_rect.adjusted(2, 2, -2, 3), 4, 4)

            grad = QLinearGradient(tray_rect.topLeft(), tray_rect.bottomLeft())
            grad.setColorAt(0.0, QColor("#E08855"))
            grad.setColorAt(0.5, QColor("#C56834"))
            grad.setColorAt(1.0, QColor("#9E4516"))
            painter.setBrush(grad)
            painter.setPen(QPen(QColor("#7C2D12"), 1.0))
            painter.drawRoundedRect(tray_rect, 4.0, 4.0)

            painter.setBrush(QColor("#F97316"))
            painter.setPen(QPen(QColor("#C2410C"), 0.9))
            painter.drawRoundedRect(lip_rect, 2.0, 2.0)

            painter.setPen(QPen(QColor("#FED7AA"), 0.8))
            painter.drawLine(int(tray_rect.left() + 5), int(tray_rect.top() + 4), int(tray_rect.right() - 5), int(tray_rect.top() + 4))

        elif s_id == "wood":
            # 2. Warm Natural Walnut Wood Tray (내추럴 원목 받침대)
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tray_rect.adjusted(2, 2, -2, 4), 4, 4)

            grad = QLinearGradient(tray_rect.topLeft(), tray_rect.bottomLeft())
            grad.setColorAt(0.0, QColor("#D97706"))
            grad.setColorAt(0.4, QColor("#B45309"))
            grad.setColorAt(0.8, QColor("#92400E"))
            grad.setColorAt(1.0, QColor("#78350F"))
            painter.setBrush(grad)
            painter.setPen(QPen(QColor("#451A03"), 1.2))
            painter.drawRoundedRect(tray_rect, 4.5, 4.5)

            painter.setBrush(QColor("#F59E0B"))
            painter.setPen(QPen(QColor("#78350F"), 1.0))
            painter.drawRoundedRect(lip_rect, 2.5, 2.5)

            painter.setPen(QPen(QColor("#FDE68A"), 0.9))
            painter.drawLine(int(tray_rect.left() + 6), int(tray_rect.top() + 4), int(tray_rect.right() - 6), int(tray_rect.top() + 4))
            painter.setPen(QPen(QColor("#542207"), 0.8))
            painter.drawLine(int(tray_rect.left() + 12), int(tray_rect.bottom() - 2), int(tray_rect.right() - 12), int(tray_rect.bottom() - 2))

        elif s_id == "marble":
            # 3. Royal Pure White Marble Pedestal (로열 대리석 받침대)
            painter.setBrush(QColor(0, 0, 0, 45))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tray_rect.adjusted(2, 2, -2, 4), 5, 5)

            grad_base = QLinearGradient(tray_rect.topLeft(), tray_rect.bottomLeft())
            grad_base.setColorAt(0.0, QColor("#FFFFFF"))
            grad_base.setColorAt(0.5, QColor("#F1F5F9"))
            grad_base.setColorAt(1.0, QColor("#CBD5E1"))
            painter.setBrush(grad_base)
            painter.setPen(QPen(QColor("#94A3B8"), 1.2))
            painter.drawRoundedRect(tray_rect, 5, 5)

            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QPen(QColor("#CBD5E1"), 1.0))
            painter.drawRoundedRect(lip_rect, 3, 3)

            painter.setPen(QPen(QColor(148, 163, 184, 160), 1.1))
            painter.drawLine(int(tray_rect.left() + 10), int(tray_rect.top() + 2), int(tray_rect.left() + 32), int(tray_rect.bottom() - 2))
            painter.drawLine(int(tray_rect.right() - 28), int(tray_rect.top() + 2), int(tray_rect.right() - 10), int(tray_rect.bottom() - 2))

        elif s_id == "gold":
            # 4. Royal Golden Imperial Saucer (임페리얼 황금 받침대)
            painter.setBrush(QColor(234, 179, 8, 70))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tray_rect.adjusted(-4, -2, 4, 4), 6, 6)

            grad = QLinearGradient(tray_rect.topLeft(), tray_rect.bottomLeft())
            grad.setColorAt(0.0, QColor("#FEF08A"))
            grad.setColorAt(0.3, QColor("#FACC15"))
            grad.setColorAt(0.7, QColor("#CA8A04"))
            grad.setColorAt(1.0, QColor("#854D0E"))
            painter.setBrush(grad)
            painter.setPen(QPen(QColor("#A16207"), 1.3))
            painter.drawRoundedRect(tray_rect, 5, 5)

            painter.setBrush(QColor("#FEF08A"))
            painter.setPen(QPen(QColor("#CA8A04"), 1.0))
            painter.drawRoundedRect(lip_rect, 3, 3)

            # Gems on rim (Ruby, Sapphire, Emerald)
            painter.setBrush(QColor("#EF4444")) # Ruby
            painter.setPen(QPen(QColor("#991B1B"), 0.8))
            painter.drawEllipse(QPointF(tray_rect.left() + 7, tray_rect.top() + tray_rect.height() * 0.5), 2.5, 2.5)
            painter.setBrush(QColor("#3B82F6")) # Sapphire
            painter.setPen(QPen(QColor("#1E40AF"), 0.8))
            painter.drawEllipse(QPointF(tray_rect.right() - 7, tray_rect.top() + tray_rect.height() * 0.5), 2.5, 2.5)
            painter.setBrush(QColor("#10B981")) # Emerald
            painter.setPen(QPen(QColor("#065F46"), 0.8))
            painter.drawEllipse(QPointF(base_cx, tray_rect.top() + tray_rect.height() * 0.5), 2.2, 2.2)

        elif s_id == "amethyst":
            # 5. Mystic Amethyst Crystal Saucer (미스틱 자수정 크리스탈)
            painter.setBrush(QColor(168, 85, 247, 80))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tray_rect.adjusted(-4, -2, 4, 4), 6, 6)

            grad = QLinearGradient(tray_rect.topLeft(), tray_rect.bottomLeft())
            grad.setColorAt(0.0, QColor("#F3E8FF"))
            grad.setColorAt(0.3, QColor("#C084FC"))
            grad.setColorAt(0.7, QColor("#9333EA"))
            grad.setColorAt(1.0, QColor("#581C87"))
            painter.setBrush(grad)
            painter.setPen(QPen(QColor("#E9D5FF"), 1.3))
            painter.drawRoundedRect(tray_rect, 5.5, 5.5)

            painter.setBrush(QColor("#E879F9"))
            painter.drawRoundedRect(lip_rect, 3, 3)

            sparkle_phase = (self.expr_frame % 25) / 25.0
            sparkle_x = tray_rect.left() + 8 + (tray_rect.width() - 16) * sparkle_phase
            painter.setBrush(QColor(255, 255, 255, 240))
            painter.drawEllipse(QPointF(sparkle_x, tray_rect.top() + 4), 1.8, 1.8)

        elif s_id == "rainbow":
            # 6. Aurora Rainbow Magic Saucer (환상의 오로라 레인보우)
            painter.setBrush(QColor(236, 72, 153, 60))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tray_rect.adjusted(-4, -2, 4, 4), 6, 6)

            grad = QLinearGradient(tray_rect.topLeft(), tray_rect.topRight())
            grad.setColorAt(0.0, QColor("#EC4899"))
            grad.setColorAt(0.25, QColor("#8B5CF6"))
            grad.setColorAt(0.5, QColor("#3B82F6"))
            grad.setColorAt(0.75, QColor("#10B981"))
            grad.setColorAt(1.0, QColor("#F59E0B"))
            painter.setBrush(grad)
            painter.setPen(QPen(QColor("#FFFFFF"), 1.3))
            painter.drawRoundedRect(tray_rect, 6, 6)

            painter.setBrush(QColor(255, 255, 255, 180))
            painter.drawRoundedRect(lip_rect, 3, 3)

        painter.restore()

    def _draw_pet_companion(self, painter: QPainter):
        """Draw cute animated pet companion (고양이/강아지/토끼) on the floor beside the pot."""
        if self.equipped_pet == "none":
            return

        p_id = self.equipped_pet
        x = self.pet_x
        # Ground floor level: feet touch the bottom!
        floor_y = self.height() - 2
        state = self.pet_state
        frame = self.pet_frame

        painter.save()
        painter.translate(x, floor_y)
        if self.pet_dir < 0 and state != "sleeping":
            painter.scale(-1, 1)

        # 1. Cats (Calico & Black Tuxedo)
        if p_id in ["cat_calico", "cat_black"]:
            is_black = (p_id == "cat_black")
            body_color = QColor("#1E293B") if is_black else QColor("#FFFDF5")
            belly_color = QColor("#F8FAFC")
            ear_inner = QColor("#FDA4AF")
            tail_angle = math.sin(frame * 0.18) * 20.0

            if state == "sleeping":
                # Donut sleeping cat on the floor
                breath = math.sin(frame * 0.08) * 1.0
                painter.setBrush(body_color)
                painter.setPen(QPen(QColor("#0F172A") if is_black else QColor("#D97706"), 1.0))
                painter.drawEllipse(QRectF(-12, -12 - breath, 24, 12 + breath))
                if not is_black:
                    painter.setBrush(QColor("#EA580C"))
                    painter.drawEllipse(QRectF(-8, -10, 8, 6))
                painter.setPen(QPen(QColor("#475569") if is_black else QColor("#78350F"), 1.2))
                painter.drawArc(QRectF(2, -8, 6, 4), 0, 180 * 16)
                painter.setPen(QPen(body_color, 2.5))
                painter.drawArc(QRectF(-14, -7, 12, 8), 90 * 16, 180 * 16)
                if (frame // 25) % 2 == 0:
                    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    painter.setPen(QColor("#9333EA"))
                    painter.drawText(QPointF(4, -15 - (frame % 25) * 0.3), "zZZ")
            else:
                step_y = math.sin(frame * 0.3) * 1.5 if state == "walking" else 0.0
                # Tail
                painter.save()
                painter.translate(-7, -4)
                painter.rotate(tail_angle)
                painter.setPen(QPen(body_color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(0, 0, -7, -9)
                painter.restore()

                # Paws on floor
                painter.setBrush(belly_color if is_black else body_color)
                painter.setPen(QPen(QColor("#CBD5E1") if not is_black else QColor("#0F172A"), 0.8))
                painter.drawEllipse(QRectF(-7, -3 - step_y, 4, 3))
                painter.drawEllipse(QRectF(3, -3 - step_y, 4, 3))

                # Body
                painter.setBrush(body_color)
                painter.setPen(QPen(QColor("#0F172A") if is_black else QColor("#D97706"), 1.0))
                painter.drawEllipse(QRectF(-8, -14 - step_y, 16, 13))

                # Bib
                painter.setBrush(belly_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(-4, -11 - step_y, 8, 8))

                if not is_black:
                    painter.setBrush(QColor("#EA580C"))
                    painter.drawEllipse(QRectF(-6, -13 - step_y, 5, 5))

                # Head
                painter.setBrush(body_color)
                painter.setPen(QPen(QColor("#0F172A") if is_black else QColor("#D97706"), 1.0))
                painter.drawEllipse(QRectF(-7, -23 - step_y, 14, 12))

                # Ears
                painter.setBrush(body_color)
                painter.drawPolygon([QPointF(-6, -22 - step_y), QPointF(-8, -28 - step_y), QPointF(-2, -23 - step_y)])
                painter.drawPolygon([QPointF(2, -23 - step_y), QPointF(8, -28 - step_y), QPointF(6, -22 - step_y)])
                painter.setBrush(ear_inner)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon([QPointF(-5, -22 - step_y), QPointF(-7, -26 - step_y), QPointF(-3, -23 - step_y)])
                painter.drawPolygon([QPointF(3, -23 - step_y), QPointF(7, -26 - step_y), QPointF(5, -22 - step_y)])

                # Eyes & nose
                painter.setBrush(QColor("#0F172A") if not is_black else QColor("#FEF08A"))
                painter.drawEllipse(QRectF(-4, -19 - step_y, 2.5, 2.5))
                painter.drawEllipse(QRectF(1.5, -19 - step_y, 2.5, 2.5))
                painter.setBrush(QColor("#FDA4AF"))
                painter.drawPolygon([QPointF(-1, -16 - step_y), QPointF(1, -16 - step_y), QPointF(0, -15 - step_y)])

                # Whiskers
                painter.setPen(QPen(QColor("#CBD5E1") if is_black else QColor("#94A3B8"), 0.8))
                painter.drawLine(QPointF(-5, -16 - step_y), QPointF(-9, -17 - step_y))
                painter.drawLine(QPointF(5, -16 - step_y), QPointF(9, -17 - step_y))

        # 2. Dogs (Shiba & Golden Retriever)
        elif p_id in ["dog_shiba", "dog_retriever"]:
            is_retriever = (p_id == "dog_retriever")
            coat_color = QColor("#FDE047") if is_retriever else QColor("#D97706")
            chest_color = QColor("#FEF9C3") if is_retriever else QColor("#FFFDF5")
            tail_angle = math.sin(frame * 0.25) * 28.0

            if state == "sleeping":
                breath = math.sin(frame * 0.08) * 1.0
                painter.setBrush(coat_color)
                painter.setPen(QPen(QColor("#92400E"), 1.0))
                painter.drawEllipse(QRectF(-13, -12 - breath, 26, 12 + breath))
                painter.setBrush(chest_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(-4, -8 - breath, 12, 7))
                painter.setPen(QPen(QColor("#78350F"), 1.2))
                painter.drawArc(QRectF(3, -9, 6, 4), 0, 180 * 16)
                if (frame // 25) % 2 == 0:
                    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    painter.setPen(QColor("#2563EB"))
                    painter.drawText(QPointF(5, -15 - (frame % 25) * 0.3), "zZZ")
            else:
                step_y = math.sin(frame * 0.35) * 1.8 if state == "walking" else 0.0
                # Tail
                painter.save()
                painter.translate(-8, -5)
                painter.rotate(tail_angle)
                painter.setPen(QPen(coat_color, 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(0, 0, -8, -10 if not is_retriever else -6)
                painter.restore()

                # Paws on floor
                painter.setBrush(chest_color)
                painter.setPen(QPen(QColor("#B45309"), 0.8))
                painter.drawEllipse(QRectF(-7, -3 - step_y, 4.5, 3.5))
                painter.drawEllipse(QRectF(3, -3 - step_y, 4.5, 3.5))

                # Body
                painter.setBrush(coat_color)
                painter.setPen(QPen(QColor("#92400E"), 1.0))
                painter.drawEllipse(QRectF(-9, -15 - step_y, 18, 14))
                # Chest
                painter.setBrush(chest_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(-4, -11 - step_y, 8, 9))

                # Head
                painter.setBrush(coat_color)
                painter.setPen(QPen(QColor("#92400E"), 1.0))
                painter.drawEllipse(QRectF(-7, -24 - step_y, 15, 13))

                if is_retriever:
                    painter.setBrush(QColor("#CA8A04"))
                    painter.drawEllipse(QRectF(-9, -23 - step_y, 5, 8))
                    painter.drawEllipse(QRectF(5, -23 - step_y, 5, 8))
                else:
                    painter.drawPolygon([QPointF(-6, -23 - step_y), QPointF(-7, -29 - step_y), QPointF(-2, -24 - step_y)])
                    painter.drawPolygon([QPointF(3, -24 - step_y), QPointF(8, -29 - step_y), QPointF(7, -23 - step_y)])

                painter.setBrush(chest_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(-2, -18 - step_y, 8, 6))
                painter.setBrush(QColor("#1E293B"))
                painter.drawEllipse(QRectF(1, -17 - step_y, 3, 2.5))
                painter.drawEllipse(QRectF(-4, -20 - step_y, 2.5, 2.5))
                painter.drawEllipse(QRectF(2, -20 - step_y, 2.5, 2.5))

        # 3. Bunny (White Fluffy Bunny)
        elif p_id == "bunny_white":
            hop_y = abs(math.sin(frame * 0.35)) * 4.0 if state == "walking" else 0.0
            if state == "sleeping":
                painter.setBrush(QColor("#FFFFFF"))
                painter.setPen(QPen(QColor("#CBD5E1"), 1.0))
                painter.drawEllipse(QRectF(-10, -9, 20, 12))
                painter.setPen(QPen(QColor("#FDA4AF"), 1.2))
                painter.drawArc(QRectF(2, -6, 5, 3), 0, 180 * 16)
                if (frame // 25) % 2 == 0:
                    painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                    painter.setPen(QColor("#EC4899"))
                    painter.drawText(QPointF(3, -12 - (frame % 25) * 0.3), "zZZ")
            else:
                painter.setBrush(QColor("#FFFFFF"))
                painter.setPen(QPen(QColor("#CBD5E1"), 1.0))
                painter.drawEllipse(QRectF(-11, -3 - hop_y, 5, 5))
                painter.drawEllipse(QRectF(-8, -13 - hop_y, 16, 14))

                painter.drawEllipse(QRectF(-5, -21 - hop_y, 13, 11))

                ear_twitch = math.sin(frame * 0.2) * 2.0
                painter.drawEllipse(QRectF(-4 + ear_twitch, -31 - hop_y, 4.5, 12))
                painter.drawEllipse(QRectF(2 - ear_twitch, -31 - hop_y, 4.5, 12))
                painter.setBrush(QColor("#FCE7F3"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QRectF(-3 + ear_twitch, -29 - hop_y, 2.5, 9))
                painter.drawEllipse(QRectF(3 - ear_twitch, -29 - hop_y, 2.5, 9))

                painter.setBrush(QColor("#EC4899"))
                painter.drawEllipse(QRectF(-2, -17 - hop_y, 2.2, 2.2))
                painter.drawEllipse(QRectF(3, -17 - hop_y, 2.2, 2.2))
                painter.setBrush(QColor("#FDA4AF"))
                painter.drawEllipse(QRectF(1, -14 - hop_y, 2.0, 1.5))

        painter.restore()
