"""
Plant Character Widget
Renders stage-based plant sprite, handles hover/click petting interaction,
and animates floating reaction icons (heart, water, sun).
"""
import os
import random
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
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

        # Particle update timer (active on demand)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_particles)

        self.load_resources("classic")

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
            # Try species specific sprite first
            path = get_resource_path(os.path.join("assets", f"stage_{species}_{stg}.png"))
            if not os.path.exists(path):
                path = get_resource_path(os.path.join("assets", f"stage_{stg}.png"))
            
            if os.path.exists(path):
                pm = QPixmap(path).scaled(scaled_sz, scaled_sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.pixmaps[stg] = pm
            else:
                self.pixmaps[stg] = QPixmap()

        # Load particles
        for p_name in ["heart", "drop", "sun"]:
            path = get_resource_path(os.path.join("assets", f"{p_name}.png"))
            if os.path.exists(path):
                pm = QPixmap(path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.particle_pixmaps[p_name] = pm

    def set_species(self, species: str):
        if self.current_species != species:
            self.load_resources(species)
            self.update()

    def set_stage(self, stage: int):
        self.current_stage = max(1, min(6, stage))
        self.update()

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
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw Plant Sprite (Bottom-aligned so the pot rests directly on the taskbar/dock)
        pix = self.pixmaps.get(self.current_stage)
        if pix and not pix.isNull():
            px = (self.width() - pix.width()) // 2
            py = self.height() - pix.height()
            painter.drawPixmap(px, py, pix)
        else:
            # Fallback drawing if PNG is missing
            painter.setPen(QColor(46, 125, 50))
            painter.setBrush(QColor(129, 199, 132))
            painter.drawEllipse(30, 30, 100, 100)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"🌱 {self.current_stage}단계")

        # Draw Active Floating Particles
        for p in self.particles:
            painter.setOpacity(p.alpha / 255.0)
            painter.drawPixmap(int(p.x), int(p.y), p.pixmap)
            painter.setOpacity(1.0)
