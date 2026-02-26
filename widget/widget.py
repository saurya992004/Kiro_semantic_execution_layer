"""
Floating Bot Widget — "Lumi"
A super cute, expressive, interactive bot that lives on your screen.
Character: "Lumi" — a glowing jelly-ghost with big emotions and wiggly animations.
"""

import sys
import math
import random
from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QRadialGradient, QPainterPath, QGuiApplication, QCursor,
)
from enum import Enum


# ─────────────────────────────────────────────
#  Palette & personality constants
# ─────────────────────────────────────────────
PALETTES = {
    "idle":      {"body": QColor("#7B61FF"), "shine": QColor("#BEB0FF"), "glow": QColor("#5A47CC"), "bg_glow": QColor(123, 97, 255, 45)},
    "happy":     {"body": QColor("#FF6B9D"), "shine": QColor("#FFB3CE"), "glow": QColor("#E0457B"), "bg_glow": QColor(255, 107, 157, 50)},
    "thinking":  {"body": QColor("#FFB347"), "shine": QColor("#FFD9A0"), "glow": QColor("#E08020"), "bg_glow": QColor(255, 179, 71, 45)},
    "listening": {"body": QColor("#4ECDC4"), "shine": QColor("#A8EFEB"), "glow": QColor("#2BADA5"), "bg_glow": QColor(78, 205, 196, 45)},
    "speaking":  {"body": QColor("#A8E063"), "shine": QColor("#D4F5A0"), "glow": QColor("#78C020"), "bg_glow": QColor(168, 224, 99, 50)},
    "sleeping":  {"body": QColor("#8899BB"), "shine": QColor("#BCCCE0"), "glow": QColor("#556688"), "bg_glow": QColor(136, 153, 187, 30)},
}

STATE_IDLE      = "idle"
STATE_HAPPY     = "happy"
STATE_THINKING  = "thinking"
STATE_LISTENING = "listening"
STATE_SPEAKING  = "speaking"
STATE_SLEEPING  = "sleeping"


# ─────────────────────────────────────────────
#  Animation state enum
# ─────────────────────────────────────────────
class BotAnimationState(Enum):
    IDLE      = STATE_IDLE
    HAPPY     = STATE_HAPPY
    THINKING  = STATE_THINKING
    LISTENING = STATE_LISTENING
    SPEAKING  = STATE_SPEAKING
    SLEEPING  = STATE_SLEEPING


# ─────────────────────────────────────────────
#  Particle system
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, cx, cy, color: QColor):
        angle  = random.uniform(0, math.tau)
        speed  = random.uniform(1.2, 3.5)
        self.x  = cx + random.uniform(-8, 8)
        self.y  = cy + random.uniform(-8, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 1.0
        self.life  = random.uniform(0.7, 1.0)
        self.decay = random.uniform(0.03, 0.07)
        self.size  = random.uniform(4, 10)
        self.color = QColor(color)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.12
        self.vx *= 0.95
        self.life -= self.decay
        self.size *= 0.97
        return self.life > 0

    def draw(self, painter: QPainter):
        alpha = max(0, int(self.life * 220))
        c = QColor(self.color)
        c.setAlpha(alpha)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(c))
        r = max(1, int(self.size / 2))
        painter.drawEllipse(int(self.x - r), int(self.y - r), r * 2, r * 2)


# ─────────────────────────────────────────────
#  Floating speech bubble
# ─────────────────────────────────────────────
class SpeechBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.message  = ""
        self.opacity  = 0.0
        self._fading_out = False

        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._tick_fade)
        self._hide_timer = QTimer()
        self._hide_timer.timeout.connect(self._start_fade_out)

    def show_message(self, text: str, duration_ms: int = 2800):
        self.message = text
        self._fading_out = False
        self._hide_timer.stop()
        self._fade_timer.stop()
        self.opacity = 0.0
        font = QFont("Georgia", 11, QFont.Normal, True)
        fm   = QFontMetrics(font)
        bw   = min(fm.horizontalAdvance(text) + 32, 220)
        bh   = fm.height() * max(1, math.ceil(fm.horizontalAdvance(text) / (bw - 32))) + 28
        self.setFixedSize(int(bw), int(bh) + 14)
        self.show()
        self._fade_timer.start(16)
        self._hide_timer.start(duration_ms)

    def _tick_fade(self):
        if self._fading_out:
            self.opacity = max(0.0, self.opacity - 0.06)
            if self.opacity <= 0:
                self._fade_timer.stop()
                self.hide()
        else:
            self.opacity = min(1.0, self.opacity + 0.07)
            if self.opacity >= 1.0:
                self._fade_timer.stop()
        self.update()

    def _start_fade_out(self):
        self._hide_timer.stop()
        self._fading_out = True
        self._fade_timer.start(16)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self.opacity)

        w, h = self.width(), self.height()
        bh = h - 14

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, bh, 12, 12)
        tail = QPainterPath()
        tail.moveTo(w // 2 - 8, bh - 1)
        tail.lineTo(w // 2 + 8, bh - 1)
        tail.lineTo(w // 2, h)
        path.addPath(tail)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.drawPath(path)
        painter.setPen(QPen(QColor(200, 180, 255, 180), 1.5))
        painter.drawPath(path)

        painter.setFont(QFont("Georgia", 11, QFont.Normal, True))
        painter.setPen(QColor(60, 40, 90))
        painter.drawText(QRect(14, 10, w - 28, bh - 20),
                         Qt.AlignCenter | Qt.TextWordWrap, self.message)


# ─────────────────────────────────────────────
#  Main Bot Widget
# ─────────────────────────────────────────────
class FloatingBotWidget(QWidget):
    """
    'Lumi' — a wiggly jelly-ghost bot with big expressive eyes,
    squish-bounce physics, particle bursts, and mood-based glow.

    Public API (unchanged from old widget):
        clicked (pyqtSignal)      — emitted on single click → opens chat card
        on_click_callback         — optional Python callable, same effect
        set_state(state: str)     — change animation state
        set_animation_state(s)    — accepts BotAnimationState enum or str
    """

    # ── signal used by app.py to open the chat card ──
    clicked = pyqtSignal()

    MESSAGES = {
        STATE_IDLE:      ["psst… click me!", "I'm right here ✨", "boo! just kidding 👀", "floating through space…"],
        STATE_HAPPY:     ["yay!!  (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", "this makes me so happy!", "wheeeee~"],
        STATE_THINKING:  ["hmm… 🤔", "let me think…", "calculating…"],
        STATE_LISTENING: ["I'm all ears!", "tell me everything~", "...yes?"],
        STATE_SPEAKING:  ["blah blah blah ✨", "I have so much to say!", "did you know…"],
        STATE_SLEEPING:  ["zzZZz…", "shh… napping", "wake me up gently~"],
    }

    def __init__(self, on_click_callback=None, parent=None):
        super().__init__(parent)
        self.on_click_callback = on_click_callback

        # window chrome
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # dimensions
        self.W = 130
        self.setFixedSize(self.W, self.W)

        # placement
        self._place_initial()

        # state
        self.state       = STATE_IDLE
        self._prev_state = STATE_IDLE

        # animation tick (~60 fps)
        self.tick = 0
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(16)

        # idle wander
        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._idle_action)
        self._idle_timer.start(4500)

        # squish physics
        self.squish_x  = 1.0
        self.squish_y  = 1.0
        self.squish_vx = 0.0
        self.squish_vy = 0.0

        self.bob_phase = 0.0
        self.wobble    = 0.0
        self.wobble_v  = 0.0

        # particles
        self.particles: list = []

        # drag tracking
        self._drag_pos    = None
        self._is_dragging = False
        self._press_pos   = None

        # ── Pupil tracking (per-eye, in widget-local space) ──
        # Separate smooth target for each eye so they can track precisely
        self.pupil_x = 0.0   # shared smooth x (direction is same for both eyes)
        self.pupil_y = 0.0   # shared smooth y
        self.pupil_tx = 0.0
        self.pupil_ty = 0.0

        # blink
        self.blink_t     = 0.0
        self.blink_dir   = 0
        self._next_blink = self._rand_blink()

        # speech bubble
        self._bubble = SpeechBubble()

        self.setCursor(Qt.OpenHandCursor)

    # ────────────────────────────────────────
    #  Public API
    # ────────────────────────────────────────
    def set_state(self, state: str):
        if state not in PALETTES:
            return
        self._prev_state = self.state
        self.state = state
        self._burst_particles()

    def set_animation_state(self, state):
        """Accept BotAnimationState enum or raw string."""
        if isinstance(state, BotAnimationState):
            state = state.value
        self.set_state(state)

    # ────────────────────────────────────────
    #  Internal helpers
    # ────────────────────────────────────────
    def _rand_blink(self):
        return random.uniform(90, 240)

    def _burst_particles(self, n=14):
        cx  = self.W / 2
        cy  = self.W / 2
        col = PALETTES[self.state]["shine"]
        for _ in range(n):
            self.particles.append(Particle(cx, cy, col))

    def _squish(self, sx, sy, vx=0.0, vy=0.0):
        self.squish_x  = sx
        self.squish_y  = sy
        self.squish_vx = vx
        self.squish_vy = vy

    def _idle_action(self):
        if self.state != STATE_IDLE:
            return
        r = random.random()
        if r < 0.35:
            self._show_bubble()
        elif r < 0.6:
            self.wobble_v += random.uniform(-0.15, 0.15)
        else:
            self._squish(0.88, 1.14)

    def _show_bubble(self, text: str = None):
        if text is None:
            text = random.choice(self.MESSAGES.get(self.state, ["hi!"]))
        gpos = self.mapToGlobal(QPoint(0, 0))
        bw   = 200
        bx   = gpos.x() + self.W // 2 - bw // 2
        by   = gpos.y() - 65
        self._bubble.move(bx, max(10, by))
        self._bubble.show_message(text)

    # ────────────────────────────────────────
    #  Animation tick
    # ────────────────────────────────────────
    def _anim_tick(self):
        self.tick += 1

        # bobbing
        self.bob_phase += 0.04

        # wobble physics
        self.wobble   += self.wobble_v
        self.wobble   *= 0.88
        self.wobble_v *= 0.88
        if abs(self.wobble) > math.pi / 6:
            self.wobble = math.copysign(math.pi / 6, self.wobble)

        # squish spring
        kx = (1.0 - self.squish_x) * 0.18
        ky = (1.0 - self.squish_y) * 0.18
        self.squish_vx = (self.squish_vx + kx) * 0.82
        self.squish_vy = (self.squish_vy + ky) * 0.82
        self.squish_x += self.squish_vx
        self.squish_y += self.squish_vy

        # ── Pupil tracking ────────────────────────────────────────────────────
        # Store a NORMALISED direction vector in [-1, 1] x [-1, 1].
        # _draw_eyes will scale it to whatever fits inside the sclera ellipse.
        cx, cy = self.W / 2, self.W / 2
        bob_offset = math.sin(self.bob_phase) * 4.0
        body_center_local = QPointF(cx, cy + bob_offset)

        cursor_global = QCursor.pos()
        local = self.mapFromGlobal(cursor_global)
        local_f = QPointF(local.x(), local.y())

        dx = local_f.x() - body_center_local.x()
        dy = local_f.y() - body_center_local.y()
        dist = math.hypot(dx, dy)

        # Normalised target: range roughly [-1, 1] on each axis.
        # Use a soft-clamp so nearby cursor gives full deflection quickly.
        DEAD_ZONE = 8.0      # pixels from center before pupils start moving
        FULL_ZONE = 60.0     # pixels at which pupils are fully deflected
        if dist > DEAD_ZONE:
            t = min((dist - DEAD_ZONE) / (FULL_ZONE - DEAD_ZONE), 1.0)
            nx = (dx / dist) * t
            ny = (dy / dist) * t
        else:
            nx, ny = 0.0, 0.0

        self.pupil_tx = nx
        self.pupil_ty = ny

        # Smooth interpolation (slightly faster = more responsive)
        self.pupil_x += (self.pupil_tx - self.pupil_x) * 0.20
        self.pupil_y += (self.pupil_ty - self.pupil_y) * 0.20
        # ─────────────────────────────────────────────────────────────────────

        # blink
        self._next_blink -= 1
        if self._next_blink <= 0 and self.blink_dir == 0:
            self.blink_dir = 1
        if self.blink_dir == 1:
            self.blink_t += 0.18
            if self.blink_t >= 1.0:
                self.blink_t = 1.0
                self.blink_dir = -1
        elif self.blink_dir == -1:
            self.blink_t -= 0.14
            if self.blink_t <= 0.0:
                self.blink_t   = 0.0
                self.blink_dir = 0
                self._next_blink = self._rand_blink()

        # particles
        self.particles = [p for p in self.particles if p.update()]

        self.update()

    # ────────────────────────────────────────
    #  Paint
    # ────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        W  = self.W
        cx, cy = W / 2, W / 2
        pal = PALETTES[self.state]

        # ── Layered ambient glow (two-pass, softer) ──────────────────────────
        # Outer soft halo
        outer_glow = QRadialGradient(QPointF(cx, cy + 8), W * 0.70)
        gc = pal["bg_glow"]
        outer_col = QColor(gc)
        outer_col.setAlpha(gc.alpha() // 2)
        outer_glow.setColorAt(0.0, outer_col)
        outer_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(outer_glow))
        painter.drawEllipse(int(cx - W * 0.70), int(cy + 8 - W * 0.70),
                            int(W * 1.40), int(W * 1.40))
        # Inner tighter glow
        inner_glow = QRadialGradient(QPointF(cx, cy + 4), W * 0.46)
        inner_glow.setColorAt(0.0, gc)
        inner_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(inner_glow))
        painter.drawEllipse(int(cx - W * 0.46), int(cy + 4 - W * 0.46),
                            int(W * 0.92), int(W * 0.92))
        # ─────────────────────────────────────────────────────────────────────

        # body transform
        bob_offset = math.sin(self.bob_phase) * 4.0
        painter.save()
        painter.translate(cx, cy + bob_offset)
        painter.rotate(math.degrees(self.wobble * 0.5))
        painter.scale(self.squish_x, self.squish_y)

        # body shape
        body_r    = W * 0.36
        body_path = self._build_body_path(body_r)

        body_grad = QLinearGradient(QPointF(-body_r * 0.3, -body_r),
                                    QPointF( body_r * 0.3,  body_r))
        body_grad.setColorAt(0.0, pal["shine"])
        body_grad.setColorAt(0.45, pal["body"])
        body_grad.setColorAt(1.0, pal["glow"])
        painter.setBrush(QBrush(body_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(body_path)

        # ── Subtle rim-light on body edge ─────────────────────────────────────
        rim_pen = QPen(QColor(255, 255, 255, 40), 2.0)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(body_path)
        painter.setPen(Qt.NoPen)
        # ─────────────────────────────────────────────────────────────────────

        # inner shine blob (larger, softer)
        shine_grad = QRadialGradient(QPointF(-body_r * 0.22, -body_r * 0.38), body_r * 0.52)
        shine_grad.setColorAt(0.0, QColor(255, 255, 255, 140))
        shine_grad.setColorAt(0.6, QColor(255, 255, 255, 40))
        shine_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(shine_grad))
        painter.drawEllipse(QPointF(-body_r * 0.22, -body_r * 0.38),
                            body_r * 0.52, body_r * 0.40)

        # eyes
        self._draw_eyes(painter, body_r, pal)

        # mouth
        self._draw_mouth(painter, body_r, pal)

        # cheeks
        if self.state in (STATE_HAPPY, STATE_LISTENING):
            blush = (QColor(255, 180, 180, 80) if self.state == STATE_HAPPY
                     else QColor(180, 230, 255, 80))
            painter.setBrush(QBrush(blush))
            painter.setPen(Qt.NoPen)
            r = body_r * 0.25
            painter.drawEllipse(QPointF(-body_r * 0.52, body_r * 0.04), r, r * 0.6)
            painter.drawEllipse(QPointF( body_r * 0.52, body_r * 0.04), r, r * 0.6)

        if self.state == STATE_SLEEPING:
            self._draw_zs(painter, body_r)
        if self.state == STATE_THINKING:
            self._draw_thought_dots(painter, body_r)

        painter.restore()

        # particles (widget-space)
        for p in self.particles:
            p.draw(painter)

    # ────────────────────────────────────────
    #  Shape builders
    # ────────────────────────────────────────
    def _build_body_path(self, r: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(-r, 0)
        path.arcTo(QPointF(-r, -r).x(), QPointF(-r, -r).y(), r * 2, r * 2, 180, -180)
        path.lineTo(r, r * 0.5)
        bump = r * 0.40
        path.cubicTo(r, r * 0.9, r * 0.65, r * 1.12, r * 0.5, r + bump * 0.5)
        path.cubicTo(r * 0.35, r + bump, r * 0.17, r * 0.85, 0, r * 0.9)
        path.cubicTo(-r * 0.17, r * 0.85, -r * 0.35, r + bump, -r * 0.5, r + bump * 0.5)
        path.cubicTo(-r * 0.65, r * 1.12, -r, r * 0.9, -r, r * 0.5)
        path.closeSubpath()
        return path

    # ────────────────────────────────────────
    #  Eye drawing — pupils always inside sclera
    # ────────────────────────────────────────
    def _draw_eyes(self, painter: QPainter, body_r: float, pal: dict):
        eye_sep_x = body_r * 0.38
        eye_y     = -body_r * 0.20
        # Sclera radii (half-widths of the white oval)
        sew = body_r * 0.19   # half-width  of sclera
        seh = body_r * 0.22   # half-height of sclera
        # Pupil radius
        pr  = body_r * 0.11

        blink_sy = 1.0 - self.blink_t * 0.96

        # ── Convert normalised direction → pixel offset inside sclera ─────────
        # Maximum travel: sclera half-extent minus pupil radius, with a tiny margin.
        max_tx = max(sew - pr - 1.5, 0.0)
        max_ty = max(seh - pr - 1.5, 0.0)
        # Scale the unit direction to pixel travel
        raw_px = self.pupil_x * max_tx
        raw_py = self.pupil_y * max_ty
        # Belt-and-suspenders: ellipse clamp so the pupil *centre* stays in sclera
        denom_x = max_tx if max_tx > 0 else 1.0
        denom_y = max_ty if max_ty > 0 else 1.0
        ellipse_dist = math.hypot(raw_px / denom_x, raw_py / denom_y)
        if ellipse_dist > 1.0:
            raw_px /= ellipse_dist
            raw_py /= ellipse_dist
        # ─────────────────────────────────────────────────────────────────────

        for side in (-1, 1):
            ex = side * eye_sep_x
            painter.save()
            painter.translate(ex, eye_y)
            painter.scale(1.0, blink_sy)

            # ── Sclera (white oval) ──────────────────────────────────────────
            sclera_path = QPainterPath()
            sclera_path.addEllipse(QPointF(0, 0), sew, seh)

            sclera_grad = QRadialGradient(QPointF(-sew * 0.15, -seh * 0.20), sew * 0.90)
            sclera_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
            sclera_grad.setColorAt(0.7, QColor(245, 245, 255, 245))
            sclera_grad.setColorAt(1.0, QColor(220, 220, 240, 230))
            painter.setBrush(QBrush(sclera_grad))
            painter.setPen(Qt.NoPen)
            painter.drawPath(sclera_path)

            # ── Clip everything below to the sclera shape ────────────────────
            # This makes it physically impossible for any inner drawing to escape.
            painter.setClipPath(sclera_path)

            px = raw_px
            py = raw_py

            # Iris (coloured ring behind pupil)
            iris_r = pr * 1.55
            iris_grad = QRadialGradient(QPointF(px, py), iris_r)
            iris_col_inner = QColor(pal["body"])
            iris_col_inner.setAlpha(200)
            iris_col_outer = QColor(pal["glow"])
            iris_col_outer.setAlpha(230)
            iris_grad.setColorAt(0.0, iris_col_inner)
            iris_grad.setColorAt(1.0, iris_col_outer)
            painter.setBrush(QBrush(iris_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), iris_r, iris_r)

            # Pupil (dark centre of iris)
            pupil_grad = QRadialGradient(QPointF(px - pr * 0.20, py - pr * 0.20), pr * 1.1)
            pupil_grad.setColorAt(0.0, QColor(15,  8, 30))
            pupil_grad.setColorAt(1.0, QColor(30, 18, 55))
            painter.setBrush(QBrush(pupil_grad))
            painter.drawEllipse(QPointF(px, py), pr, pr)

            # Primary catchlight — large bright dot (upper-right of pupil)
            painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
            painter.drawEllipse(QPointF(px + pr * 0.32, py - pr * 0.36), pr * 0.34, pr * 0.34)
            # Secondary catchlight — tiny soft dot (lower-left)
            painter.setBrush(QBrush(QColor(255, 255, 255, 120)))
            painter.drawEllipse(QPointF(px - pr * 0.26, py + pr * 0.24), pr * 0.17, pr * 0.17)

            # ── Remove clip before sclera shadow/edge ───────────────────────
            painter.setClipping(False)

            # Subtle shadow around sclera edge (depth)
            rim = QPen(QColor(160, 140, 200, 60), 1.2)
            painter.setPen(rim)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), sew, seh)

            painter.restore()

    # ────────────────────────────────────────
    #  Mouth drawing
    # ────────────────────────────────────────
    def _draw_mouth(self, painter: QPainter, body_r: float, pal: dict):
        my = body_r * 0.28
        mw = body_r * 0.50
        painter.setPen(QPen(QColor(50, 30, 70, 200), 2.5, Qt.SolidLine, Qt.RoundCap))

        if self.state == STATE_HAPPY:
            path = QPainterPath()
            path.moveTo(-mw / 2, my)
            path.cubicTo(-mw / 4, my + body_r * 0.28, mw / 4, my + body_r * 0.28, mw / 2, my)
            painter.setPen(QPen(QColor(50, 30, 70, 200), 3.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawPath(path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.drawRoundedRect(int(-mw / 2 + 4), int(my + 1),
                                    int(mw - 8), int(body_r * 0.14), 4, 4)

        elif self.state == STATE_THINKING:
            path = QPainterPath()
            path.moveTo(-mw / 2, my)
            path.cubicTo(-mw / 6, my - 5, mw / 6, my + 5, mw / 2, my)
            painter.drawPath(path)

        elif self.state == STATE_SPEAKING:
            phase = abs(math.sin(self.tick * 0.12))
            mh    = body_r * 0.10 + body_r * 0.18 * phase
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(50, 30, 70, 200)))
            painter.drawEllipse(QPointF(0, my + mh / 2), mw / 3, mh / 2 + 2)

        elif self.state == STATE_SLEEPING:
            painter.setPen(QPen(QColor(130, 110, 160, 180), 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(-mw / 4, my), QPointF(mw / 4, my))

        elif self.state == STATE_LISTENING:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(50, 30, 70, 180)))
            painter.drawEllipse(QPointF(0, my + 3), mw * 0.20, body_r * 0.14)

        else:  # idle
            path = QPainterPath()
            path.moveTo(-mw / 2, my)
            path.cubicTo(-mw / 4, my + body_r * 0.12, mw / 4, my + body_r * 0.12, mw / 2, my)
            painter.drawPath(path)

    # ────────────────────────────────────────
    #  Sleeping Zs
    # ────────────────────────────────────────
    def _draw_zs(self, painter: QPainter, body_r: float):
        base_alpha = int(180 * abs(math.sin(self.tick * 0.04)))
        for i, (ox, oy, scale) in enumerate([
            (body_r * 0.6,  -body_r * 0.5,  1.0),
            (body_r * 0.85, -body_r * 0.75, 0.7),
            (body_r * 1.1,  -body_r * 1.0,  0.45),
        ]):
            phase = self.tick * 0.04 + i * 0.9
            alpha = int(base_alpha * (0.5 + 0.5 * math.sin(phase)))
            painter.setFont(QFont("Georgia", max(6, int(18 * scale)), QFont.Bold))
            painter.setPen(QColor(200, 220, 255, alpha))
            painter.drawText(QPointF(ox, oy), "Z")

    # ────────────────────────────────────────
    #  Thought dots
    # ────────────────────────────────────────
    def _draw_thought_dots(self, painter: QPainter, body_r: float):
        for i in range(3):
            phase = self.tick * 0.08 + i * 0.7
            alpha = int(180 + 75 * math.sin(phase))
            r     = 4 + 2 * math.sin(phase)
            ox    = body_r * 0.6 + i * (r * 2 + 4)
            oy    = -body_r * 0.8
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 200, 100, alpha)))
            painter.drawEllipse(QPointF(ox, oy), r, r)

    # ────────────────────────────────────────
    #  Placement helpers
    # ────────────────────────────────────────
    def _place_initial(self):
        screens = QGuiApplication.screens()
        if not screens:
            return
        prim   = QGuiApplication.primaryScreen()
        rect   = prim.availableGeometry() if prim else screens[0].availableGeometry()
        margin = 24
        self.move(rect.x() + rect.width()  - self.W - margin,
                  rect.y() + rect.height() - self.W - margin)
        self.ensure_on_screen()

    def ensure_on_screen(self):
        union_rect = QRect()
        for s in QGuiApplication.screens():
            union_rect = union_rect.united(s.availableGeometry())
        if not union_rect.contains(self.geometry()):
            prim = QGuiApplication.primaryScreen()
            if prim:
                rect = prim.availableGeometry()
                self.move(rect.x() + (rect.width()  - self.W) // 2,
                          rect.y() + (rect.height() - self.W) // 2)

    def showEvent(self, event):
        super().showEvent(event)
        self.ensure_on_screen()
        self.raise_()
        self.activateWindow()

    # ────────────────────────────────────────
    #  Mouse events
    # ────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos    = event.globalPos() - self.frameGeometry().topLeft()
            self._press_pos   = event.globalPos()
            self._is_dragging = True
            self.setCursor(Qt.ClosedHandCursor)
            self._squish(1.18, 0.84)

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            self.wobble_v += 0.04

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.OpenHandCursor)
            self._squish(0.85, 1.18)
            if self._press_pos:
                diff = event.globalPos() - self._press_pos
                if abs(diff.x()) < 6 and abs(diff.y()) < 6:
                    self._on_clicked()

    def mouseDoubleClickEvent(self, event):
        self._on_clicked()

    def _on_clicked(self):
        """Handle a confirmed click — plays reaction then opens the chat card."""
        self.set_state(STATE_HAPPY)
        self._show_bubble()
        self._burst_particles(22)
        self.wobble_v = 0.20

        # ── open the chat card (same as the old widget) ──
        self.clicked.emit()                       # → app.py show_chat_card()
        if self.on_click_callback:
            self.on_click_callback()

        # return to idle after the happy flash
        QTimer.singleShot(1800, lambda: self.set_state(STATE_IDLE))

    def enterEvent(self, event):
        self.set_state(STATE_HAPPY)
        self._squish(1.08, 0.93)
        super().enterEvent(event)

    def leaveEvent(self, event):
        QTimer.singleShot(600, lambda: self.set_state(STATE_IDLE))
        super().leaveEvent(event)

    def closeEvent(self, event):
        """Ignore close — only the main app can quit."""
        try:
            self._anim_timer.stop()
            self._idle_timer.stop()
        except Exception:
            pass
        event.ignore()


# ─────────────────────────────────────────────
#  Standalone demo runner
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Lumi Bot")

    bot = FloatingBotWidget(on_click_callback=lambda: print("Bot clicked!"))
    bot.show()

    states = [STATE_IDLE, STATE_HAPPY, STATE_THINKING,
              STATE_LISTENING, STATE_SPEAKING, STATE_SLEEPING]
    idx = [0]
    def next_state():
        idx[0] = (idx[0] + 1) % len(states)
        bot.set_state(states[idx[0]])
    demo_timer = QTimer()
    demo_timer.timeout.connect(next_state)
    demo_timer.start(3000)

    sys.exit(app.exec_())