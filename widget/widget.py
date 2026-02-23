"""
Floating Bot Widget
Implements the animated floating bot icon that stays on top of all windows.
"""

import sys
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QPoint, QEvent, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QPixmap,
    QIcon,
    QLinearGradient,
    QRadialGradient,
    QGuiApplication,
    QCursor,
)
from PyQt5.QtSvg import QSvgWidget
import math

class BotAnimationState:
    """Manages bot animation states"""
    IDLE = 0
    HAPPY = 1
    THINKING = 2
    LISTENING = 3
    SPEAKING = 4
    
    @staticmethod
    def get_frame(state, frame_number):
        """Get SVG representation of bot in given state and frame"""
        state_frames = {
            BotAnimationState.IDLE: BotAnimationState._idle_frames(),
            BotAnimationState.HAPPY: BotAnimationState._happy_frames(),
            BotAnimationState.THINKING: BotAnimationState._thinking_frames(),
            BotAnimationState.LISTENING: BotAnimationState._listening_frames(),
            BotAnimationState.SPEAKING: BotAnimationState._speaking_frames(),
        }
        
        frames = state_frames.get(state, BotAnimationState._idle_frames())
        return frames[frame_number % len(frames)]
    
    @staticmethod
    def _idle_frames():
        """Idle/neutral state frames"""
        return [
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00D4FF"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <path d="M 80 60 m -2 0 a 2 2 0 1 0 4 0 a 2 2 0 1 0 -4 0" fill="#00D4FF"/>
                <path d="M 120 60 m -2 0 a 2 2 0 1 0 4 0 a 2 2 0 1 0 -4 0" fill="#00D4FF"/>
                <path d="M 100 95 Q 95 100 100 105" stroke="#0f0f1e" stroke-width="2" fill="none"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00D4FF"/>
            </svg>''',
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00E6FF"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <path d="M 80 60 m -2 0 a 2 2 0 1 0 4 0 a 2 2 0 1 0 -4 0" fill="#00E6FF"/>
                <path d="M 120 60 m -2 0 a 2 2 0 1 0 4 0 a 2 2 0 1 0 -4 0" fill="#00E6FF"/>
                <path d="M 100 95 Q 95 100 100 105" stroke="#0f0f1e" stroke-width="2" fill="none"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00E6FF"/>
            </svg>'''
        ]
    
    @staticmethod
    def _happy_frames():
        """Happy/smiling state frames"""
        return [
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00FF88"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="4" fill="#00FF88"/>
                <circle cx="120" cy="60" r="4" fill="#00FF88"/>
                <path d="M 85 75 Q 100 85 115 75" stroke="#0f0f1e" stroke-width="3" fill="none" stroke-linecap="round"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00FF88"/>
            </svg>''',
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00FF99"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="4" fill="#00FF99"/>
                <circle cx="120" cy="60" r="4" fill="#00FF99"/>
                <path d="M 80 75 Q 100 88 120 75" stroke="#0f0f1e" stroke-width="3" fill="none" stroke-linecap="round"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00FF99"/>
            </svg>'''
        ]
    
    @staticmethod
    def _thinking_frames():
        """Thinking state frames (question mark effect)"""
        return [
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#FFB703"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <path d="M 80 58 L 80 62" stroke="#FFB703" stroke-width="2"/>
                <path d="M 120 58 L 120 62" stroke="#FFB703" stroke-width="2"/>
                <path d="M 90 65 Q 100 80 110 70" stroke="#0f0f1e" stroke-width="2" fill="none"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#FFB703"/>
                <text x="100" y="85" font-size="30" font-weight="bold" fill="#0f0f1e" text-anchor="middle">?</text>
            </svg>''',
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#FFC107"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <path d="M 80 58 L 80 62" stroke="#FFC107" stroke-width="2"/>
                <path d="M 120 58 L 120 62" stroke="#FFC107" stroke-width="2"/>
                <path d="M 95 70 L 105 70" stroke="#0f0f1e" stroke-width="2"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#FFC107"/>
                <text x="100" y="85" font-size="30" font-weight="bold" fill="#0f0f1e" text-anchor="middle">?</text>
            </svg>'''
        ]
    
    @staticmethod
    def _listening_frames():
        """Listening state frames (with sound waves)"""
        return [
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#BB86FC"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="5" fill="#BB86FC"/>
                <circle cx="120" cy="60" r="5" fill="#BB86FC"/>
                <path d="M 85 75 Q 100 82 115 75" stroke="#0f0f1e" stroke-width="2" fill="none"/>
                <path d="M 30 50 Q 40 40 45 30" stroke="#BB86FC" stroke-width="2" fill="none" stroke-linecap="round"/>
                <path d="M 170 50 Q 160 40 155 30" stroke="#BB86FC" stroke-width="2" fill="none" stroke-linecap="round"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#BB86FC"/>
            </svg>''',
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#CE93FC"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="5" fill="#CE93FC"/>
                <circle cx="120" cy="60" r="5" fill="#CE93FC"/>
                <path d="M 85 75 Q 100 82 115 75" stroke="#0f0f1e" stroke-width="2" fill="none"/>
                <path d="M 25 50 Q 35 35 40 20" stroke="#CE93FC" stroke-width="2" fill="none" stroke-linecap="round"/>
                <path d="M 175 50 Q 165 35 160 20" stroke="#CE93FC" stroke-width="2" fill="none" stroke-linecap="round"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#CE93FC"/>
            </svg>'''
        ]
    
    @staticmethod
    def _speaking_frames():
        """Speaking state frames"""
        return [
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00D4FF"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="4" fill="#00D4FF"/>
                <circle cx="120" cy="60" r="4" fill="#00D4FF"/>
                <ellipse cx="100" cy="85" rx="8" ry="12" fill="#0f0f1e"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00D4FF"/>
            </svg>''',
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00D4FF"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="4" fill="#00D4FF"/>
                <circle cx="120" cy="60" r="4" fill="#00D4FF"/>
                <ellipse cx="100" cy="85" rx="10" ry="14" fill="#0f0f1e"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00D4FF"/>
            </svg>''',
            '''<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
                <path d="M 60 20 Q 100 10 140 20 L 140 80 Q 100 90 60 80 Z" fill="#00D4FF"/>
                <circle cx="80" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="120" cy="60" r="12" fill="#0f0f1e"/>
                <circle cx="80" cy="60" r="4" fill="#00D4FF"/>
                <circle cx="120" cy="60" r="4" fill="#00D4FF"/>
                <ellipse cx="100" cy="85" rx="12" ry="10" fill="#0f0f1e"/>
                <ellipse cx="100" cy="150" rx="50" ry="70" fill="#00D4FF"/>
            </svg>'''
        ]


class FloatingBotWidget(QWidget):
    """Floating animated bot widget that can be dragged around the screen"""
    
    # Signals
    clicked = pyqtSignal()
    
    def __init__(self, on_click_callback=None, parent=None):
        super().__init__(parent)
        self.on_click_callback = on_click_callback
        
        # Window settings
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Size and position
        self.size = 110
        self.setFixedSize(self.size, self.size)
        
        # Track drags
        self.drag_position = None
        self.is_dragging = False
        self.double_click_timer = None

        # Place widget at bottom-right of primary screen with a margin
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                rect = screen.availableGeometry()
                margin = 20
                x = rect.x() + rect.width() - self.size - margin
                y = rect.y() + rect.height() - self.size - margin
                self.move(x, y)
        except Exception:
            # fallback to default geometry
            self.setGeometry(QRect(100, 100, self.size, self.size))
        
        # Drag support
        self.drag_position = None
        self.is_dragging = False
        # Mouse tracking for hover & pupil follow
        self.setMouseTracking(True)
        self.last_cursor_pos = None
        
        # Animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_frame = 0
        self.current_state = BotAnimationState.IDLE
        self.animation_timer.start(150)  # Update frequently for expressive animation
        
        # Focus on click
        self.setCursor(Qt.OpenHandCursor)
        
    def set_animation_state(self, state):
        """Change the animation state"""
        self.current_state = state
        self.animation_frame = 0
        
    def update_animation(self):
        """Update animation frame"""
        self.animation_frame += 1
        # Poll global cursor position at timer (avoid doing this inside paintEvent)
        try:
            self.last_cursor_pos = self.mapFromGlobal(QCursor.pos())
        except Exception:
            pass
        self.update()
        
    def paintEvent(self, event):
        """Draw the bot icon with current animation frame"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Get current animation state frame (SVG as string)
        svg_str = BotAnimationState.get_frame(self.current_state, self.animation_frame)
        
        # For now, draw a simple avatar instead of rendering SVG
        # (SVG rendering in PyQt5 requires additional setup)
        self.draw_bot_avatar(painter)
        
    def draw_bot_avatar(self, painter):
        """Draw a simple bot avatar"""
        # Create a more robotic, expressive avatar
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        # Base colors per state
        state_colors = {
            BotAnimationState.IDLE: QColor("#00D4FF"),
            BotAnimationState.HAPPY: QColor("#00FF88"),
            BotAnimationState.THINKING: QColor("#FFB703"),
            BotAnimationState.LISTENING: QColor("#BB86FC"),
            BotAnimationState.SPEAKING: QColor("#00D4FF"),
        }
        base = state_colors.get(self.current_state, QColor("#00D4FF"))
        dark = QColor(15, 15, 30)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Outer shell - rounded robot head with subtle gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, base.lighter(120))
        grad.setColorAt(1.0, base.darker(120))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(base.darker(150), 2))
        # Face plate metrics (compute before drawing so background can extend up to antenna)
        face_w = w * 0.8
        face_h = h * 0.54
        face_x = (w - face_w) / 2
        face_y = cy - face_h * 0.1

        # Background box behind face (brighter and extends up toward antenna)
        box_margin_x = 6
        box_margin_top = 12
        box_x = int(face_x - box_margin_x)
        box_y = int(face_y - box_margin_top)
        box_w = int(face_w + box_margin_x * 2)
        box_h = int(face_h + box_margin_top)
        bg_color = base.lighter(140)
        bg_color.setAlpha(110)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(box_x, box_y, box_w, box_h, 14, 14)

        # Antenna: restore original placement (gap above head), drawn at top coordinates
        painter.setPen(QPen(base.darker(200), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(int(cx), 8, int(cx), 24)
        painter.setBrush(QBrush(base))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - 6), int(8 - 6), 12, 12)

        # Face plate (darker inset)
        painter.setBrush(QBrush(dark))
        painter.setPen(QPen(base.darker(220), 1))
        painter.drawRoundedRect(int(face_x), int(face_y), int(face_w), int(face_h), 12, 12)

        # Eyes - larger and expressive; pupils follow cursor
        eye_offset_x = 0.26 * w
        eye_y = face_y + face_h * 0.34
        # pupil animation: oscillate base size
        pupil_wave = (1 + 0.25 * math.sin(self.animation_frame * 0.35))
        eye_outer_w = 36
        eye_outer_h = 30
        eye_radius = max(4, int(8 * pupil_wave))
        # compute cursor pos: use last polled cursor position (set by timer or mouse events)
        cursor_pt = self.last_cursor_pos

        def pupil_offset(eye_cx, eye_cy):
            if not cursor_pt:
                return 0, 0
            dx = cursor_pt.x() - int(eye_cx)
            dy = cursor_pt.y() - int(eye_cy)
            # normalize and limit offset
            max_off = 6
            dist = math.hypot(dx, dy)
            if dist == 0:
                return 0, 0
            scale = min(max_off / dist, 1.0)
            return int(dx * scale), int(dy * scale)

        # Left eye
        lx = cx - eye_offset_x
        ry = int(eye_y)
        painter.setBrush(QBrush(QColor(20, 20, 30)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(lx - eye_outer_w / 2), int(ry - eye_outer_h / 2), int(eye_outer_w), int(eye_outer_h))
        # pupil follows cursor
        offx, offy = pupil_offset(lx, ry)
        pupil_cx = int(lx) + offx
        pupil_cy = int(ry) + offy
        painter.setBrush(QBrush(base))
        painter.drawEllipse(int(pupil_cx - eye_radius / 2), int(pupil_cy - eye_radius / 2), int(eye_radius), int(eye_radius))

        # Right eye
        rx = cx + eye_offset_x
        painter.setBrush(QBrush(QColor(20, 20, 30)))
        painter.drawEllipse(int(rx - eye_outer_w / 2), int(ry - eye_outer_h / 2), int(eye_outer_w), int(eye_outer_h))
        offx_r, offy_r = pupil_offset(rx, ry)
        pupil_cx_r = int(rx) + offx_r
        pupil_cy_r = int(ry) + offy_r
        painter.setBrush(QBrush(base))
        painter.drawEllipse(int(pupil_cx_r - eye_radius / 2), int(pupil_cy_r - eye_radius / 2), int(eye_radius), int(eye_radius))

        # Mouth / expression
        painter.setPen(QPen(base.lighter(160), 3, Qt.SolidLine, Qt.RoundCap))
        mouth_y = int(face_y + face_h * 0.68)
        mouth_w = int(face_w * 0.46)
        if self.current_state == BotAnimationState.HAPPY:
            # bold smiling arc (thicker)
            painter.setPen(QPen(QColor(245,245,245), 5, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(int(cx - mouth_w/2), mouth_y - 8, mouth_w, 20, 210 * 16, 120 * 16)
            # small cheek highlights
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(base.lighter(140)))
            painter.drawEllipse(int(cx - mouth_w/2 - 6), mouth_y - 2, 8, 6)
            painter.drawEllipse(int(cx + mouth_w/2 - 2), mouth_y - 2, 8, 6)
        elif self.current_state == BotAnimationState.THINKING:
            painter.setPen(QPen(base.lighter(120), 2))
            painter.setFont(QFont("Arial", 20, QFont.Bold))
            painter.setPen(QPen(QColor(200,200,200), 1))
            painter.drawText(int(cx - 8), mouth_y + 4, "?")
        elif self.current_state == BotAnimationState.LISTENING:
            # neutral with small waveform dots
            painter.setPen(QPen(base.lighter(120), 2))
            painter.drawLine(int(cx - mouth_w/2), mouth_y, int(cx + mouth_w/2), mouth_y)
            # small waves
            for i in range(-2,3):
                hwave = 2 + abs(i)
                painter.drawEllipse(int(cx + i*10 - 1), mouth_y - hwave, 3, 3)
        elif self.current_state == BotAnimationState.SPEAKING:
            # animated open mouth
            mouth_h = 6 + int(4 * abs(math.sin(self.animation_frame * 0.6)))
            painter.setBrush(QBrush(QColor(10,10,10)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(cx - mouth_w/2), mouth_y - 4, mouth_w, mouth_h)
        else:
            # idle neutral line
            painter.setPen(QPen(base.lighter(120), 2))
            painter.drawLine(int(cx - mouth_w/2), mouth_y, int(cx + mouth_w/2), mouth_y)

        # subtle glow around the robot
        glow = QRadialGradient(QPointF(cx, cy), w/1.8)
        glow.setColorAt(0.0, QColor(base.red(), base.green(), base.blue(), 40))
        glow.setColorAt(1.0, QColor(0,0,0,0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx - w/2), int(cy - h/2), int(w), int(h))
            
    def mousePressEvent(self, event):
        """Handle mouse press - start drag or click"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self._press_global_pos = event.globalPos()
            self.is_dragging = False
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseDoubleClickEvent(self, event):
        """Double-click is treated the same as single-click (handled in mouseReleaseEvent)"""
        pass

    def mouseMoveEvent(self, event):
        """Handle mouse move - drag the widget"""
        if self.drag_position:
            delta = event.globalPos() - self._press_global_pos
            if not self.is_dragging and (abs(delta.x()) > 5 or abs(delta.y()) > 5):
                self.is_dragging = True
            if self.is_dragging:
                self.move(event.globalPos() - self.drag_position)
        # update cursor-following behavior regardless
        try:
            self.last_cursor_pos = event.pos()
            self.update()
        except Exception:
            pass
            
    def enterEvent(self, event):
        """Hover start - make bot smile"""
        self.set_animation_state(BotAnimationState.HAPPY)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hover end - return to idle"""
        self.set_animation_state(BotAnimationState.IDLE)
        super().leaveEvent(event)
    
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release - fire click if we didn't drag"""
        if event.button() == Qt.LeftButton:
            if not self.is_dragging:
                # It was a real click (not a drag) — open the chat card
                print("🎯 Widget clicked!")
                self.clicked.emit()
                if self.on_click_callback:
                    self.on_click_callback()
            self.is_dragging = False
            self.drag_position = None
            self.setCursor(Qt.OpenHandCursor)
                    
    def closeEvent(self, event):
        """Handle widget close - prevent accidental closure"""
        try:
            self.animation_timer.stop()
        except:
            pass
        # Don't close - ignore the close event to keep the bot running
        # Users must explicitly quit the app via the chat window or closing it
        event.ignore()