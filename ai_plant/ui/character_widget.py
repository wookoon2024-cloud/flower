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
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QPainterPath
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

class PlantCharacterWidget(QWidget):
    clicked = Signal()

    def __init__(self, parent=None, scale_pct: int = 100):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scale_pct = max(70, min(160, scale_pct))
        sz = int(160 * (self.scale_pct / 100.0))
        self.setFixedSize(sz, sz)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.current_stage = 1
        self.current_species = "classic"
        self.pixmaps = {}
        self.particle_pixmaps = {}
        self.particles = []

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

    def set_scale(self, scale_pct: int):
        """Dynamically adjust flowerpot scale."""
        self.scale_pct = max(70, min(160, scale_pct))
        sz = int(160 * (self.scale_pct / 100.0))
        self.setFixedSize(sz, sz)
        self.load_resources(self.current_species)
        self.update()

    def load_resources(self, species: str = "classic"):
        """Load stage sprites and particle icons for specified species (stages 1~6)."""
        self.current_species = species
        scaled_sz = int(150 * (self.scale_pct / 100.0))
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
        for p_name in ["heart", "drop", "sun"]:
            path = get_resource_path(os.path.join("assets", f"{p_name}.png"))
            if os.path.exists(path):
                pm = QPixmap(path).scaled(
                    28, 28,
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

    # --- Cute Facial Expression Idle Animation System ---
    def _schedule_next_expression(self):
        """Schedule next expression after 3.5 ~ 6.5 seconds."""
        interval_ms = random.randint(3500, 6500)
        self.idle_trigger_timer.start(interval_ms)

    def _trigger_random_expression(self):
        """Picks a random facial expression (Blink, Yawn, Tongue out, Wink)."""
        # Weighted choices: Blink is most common, followed by Yawn, Tongue (메롱), Wink
        choices = ["blink", "blink", "yawn", "tongue", "wink", "happy"]
        self.expr_type = random.choice(choices)
        self.expr_frame = 0

        if self.expr_type == "blink":
            self.expr_total_frames = 28  # ~0.9s
        elif self.expr_type == "yawn":
            self.expr_total_frames = 45  # ~1.5s
        elif self.expr_type == "tongue":
            self.expr_total_frames = 38  # ~1.2s
        elif self.expr_type == "wink":
            self.expr_total_frames = 32  # ~1.0s
        else:
            self.expr_total_frames = 30  # ~1.0s

        self.expr_timer.start(33)  # ~30 fps

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
            self.clicked.emit()
            self.spawn_particle("heart")
            # Trigger happy expression on touch!
            self.expr_type = "happy"
            self.expr_frame = 0
            self.expr_total_frames = 25
            self.expr_timer.start(33)
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

        # 3. Draw Active Floating Particles
        for p in self.particles:
            painter.setOpacity(p.alpha / 255.0)
            painter.drawPixmap(int(p.x), int(p.y), p.pixmap)
            painter.setOpacity(1.0)

    def _draw_facial_expression(self, painter: QPainter, px: int, py: int, sprite_w: int):
        """Draws animated eyes/mouth overlay on the flowerpot face without moving the pot."""
        try:
            if sprite_w <= 0 or self.expr_total_frames <= 0:
                return
            scale = max(0.1, sprite_w / 200.0)
            progress = max(0.0, min(1.0, self.expr_frame / float(self.expr_total_frames)))

            # Face anchor coordinates
            lx = px + int(89 * scale)   # Left eye center
            rx = px + int(111 * scale)  # Right eye center
            ey = py + int(162 * scale)  # Eye vertical center
            mx = px + int(100 * scale)  # Mouth center X
            my = py + int(166 * scale)  # Mouth center Y

            eye_radius = max(2, int(5 * scale))
            pen_dark = QPen(QColor("#3E2723"), max(2.0, 2.4 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            brush_dark = QBrush(QColor("#3E2723"))
            brush_pot = QBrush(QColor("#D27D46"))  # Pot surface color to mask default face

            # Mask default eye & mouth positions
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(brush_pot)
            painter.drawEllipse(QPoint(lx, ey), eye_radius + 2, eye_radius + 2)
            painter.drawEllipse(QPoint(rx, ey), eye_radius + 2, eye_radius + 2)
            painter.drawEllipse(QPoint(mx, my + int(2*scale)), max(4, int(11 * scale)), max(3, int(8 * scale)))

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
                painter.drawArc(mx - int(6*scale), my - int(4*scale), max(6, int(12*scale)), max(4, int(8*scale)), 0, -180*16)

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
                painter.drawEllipse(QPoint(mx, my + int(3*scale)), mouth_w // 2, mouth_h // 2)

                # Little pink tongue inside yawn mouth
                if sine_open > 0.4:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor("#FF8A80")))
                    painter.drawEllipse(QPoint(mx, my + int((3 + mouth_h*0.25)*scale)), max(2, int(mouth_w*0.35)), max(2, int(mouth_h*0.25)))

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
                painter.drawArc(mx - int(8*scale), my - int(4*scale), max(6, int(16*scale)), max(4, int(9*scale)), 0, -180*16)

                # Cute pink tongue sticking out downwards (메롱)
                tongue_len = max(2.0, 7.0 * scale * min(1.0, progress * 3.0))
                tongue_w = max(3.0, 7.0 * scale)
                tongue_rect = QRectF(mx - tongue_w / 2.0, my + 1.0 * scale, tongue_w, tongue_len)
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
                painter.drawArc(mx - int(7*scale), my - int(4*scale), max(6, int(14*scale)), max(4, int(8*scale)), 0, -180*16)

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
                painter.drawArc(mx - int(8*scale), my - int(4*scale), max(6, int(16*scale)), max(4, int(10*scale)), 0, -180*16)

                # Rosy cheeks
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 138, 128, 190))
                painter.drawEllipse(QPoint(px + int(76*scale), py + int(165*scale)), max(2, int(5*scale)), max(2, int(3.5*scale)))
                painter.drawEllipse(QPoint(px + int(124*scale), py + int(165*scale)), max(2, int(5*scale)), max(2, int(3.5*scale)))
        except Exception as e:
            pass
