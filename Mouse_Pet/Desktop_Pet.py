import sys
import math
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, QColorDialog
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QTime
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QCursor

# Initialize Pygame Audio Engine
import pygame
pygame.mixer.init()

# Dedicated sound channels
ACTIVE_CHANNEL = pygame.mixer.Channel(1)
SNORE_CHANNEL = pygame.mixer.Channel(2)


class DesktopPet(QWidget):
    def __init__(self, master_controller=None, is_clone=False):
        super().__init__()
        self.master_controller = master_controller
        self.is_clone = is_clone
        
        # Transparent & Frameless Window Flags
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.SubWindow | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Pet Configuration Defaults
        self.pet_type = "Dog"
        self.speed = 5
        self.pet_color = QColor(210, 140, 70)
        self.sound_volume = 1.0  # 10% to 100% (0.1 to 1.0)
        
        # Initial Window Size (Base scale 100x100)
        self.pet_scale = 1.0
        self.update_window_size()
        
        # Position & Animation State
        self.position = QPoint(500, 500)
        self.move(self.position)
        self.frame = 0
        self.facing_right = True
        self.is_moving = False
        
        # States
        self.state = "FOLLOWING"
        self.explosion_frame = 0
        
        # Clone / Multi-Target Game Mechanics
        self.is_real_target = True
        
        # Modes
        self.is_resizing_mode = False
        
        # Game & Score Mechanics
        self.score = 0
        self.flee_target = QPoint(300, 300)
        self.flee_timer_counter = 0
        
        self.hover_time = 0.0
        self.untouched_time = 0.0
        
        # Mouse Hold Timer State (3 seconds to activate Flee Mode)
        self.is_mouse_held = False
        self.hold_progress = 0.0
        
        # Right-Click Long Press Detection Timer (> 2 seconds for Animal Change Menu)
        self.right_press_time = QTime()
        self.right_click_timer = QTimer(self)
        self.right_click_timer.setSingleShot(True)
        self.right_click_timer.timeout.connect(self.handle_long_right_click)
        self.long_click_triggered = False
        
        # Main Loop (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_behavior)
        self.timer.start(33)
        
        self.hold_timer = QTimer(self)
        self.hold_timer.timeout.connect(self.check_hold_duration)
        
        if not self.is_clone:
            self.reset_random_sound_timer()
            self.clones = []

        self.show()

    def update_window_size(self):
        base_size = int(100 * self.pet_scale)
        self.resize(base_size, base_size)

    def reset_random_sound_timer(self):
        if self.is_clone:
            return
        random_delay = random.randint(500, 3000)
        QTimer.singleShot(random_delay, self.trigger_random_annoying_sound)

    def trigger_random_annoying_sound(self):
        if self.state in ["FOLLOWING", "FLEEING"]:
            self.play_sound("active")
        self.reset_random_sound_timer()

    # =========================================================================
    # AUDIO PLAYBACK & VOLUME CONTROL
    # =========================================================================
    def play_sound(self, sound_type):
        if self.is_clone and self.master_controller:
            self.master_controller.play_sound(sound_type)
            return

        pet = self.pet_type.lower().replace(" ", "_")
        file_path = None

        if sound_type == "snore":
            file_path = r"Mouse_Pet\snore.mp3"
        elif sound_type == "explode":
            file_path = r"Mouse_Pet\boom.mp3"
        elif sound_type == "regenerate":
            file_path = r"Mouse_Pet\regen.mp3"
        elif sound_type == "active":
            sound_files = {
                "dog": r"Mouse_Pet\dwog.mp3",
                "cat": r"Mouse_Pet\cat.mp3",
                "duck": r"Mouse_Pet\dack.mp3",
                "perry_the_platypus": r"Mouse_Pet\perry_the_platypus.mp3",
            }
            file_path = sound_files.get(pet)

        if file_path and os.path.exists(file_path):
            try:
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(self.sound_volume)
                if sound_type == "snore":
                    SNORE_CHANNEL.play(sound)
                else:
                    ACTIVE_CHANNEL.play(sound)
            except Exception as e:
                print(f"Error playing audio file '{file_path}': {e}")

    def stop_snore(self):
        SNORE_CHANNEL.stop()

    def stop_all_sounds(self):
        ACTIVE_CHANNEL.stop()
        SNORE_CHANNEL.stop()

    def set_volume(self, percent):
        self.sound_volume = percent / 100.0

    # =========================================================================
    # MOUSE & CONTEXT MENU HANDLERS
    # =========================================================================
    def wheelEvent(self, event):
        if self.is_resizing_mode:
            delta = event.angleDelta().y()
            if delta > 0:
                self.pet_scale = min(2.5, self.pet_scale + 0.1)
            else:
                self.pet_scale = max(0.5, self.pet_scale - 0.1)
            self.update_window_size()
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_resizing_mode = not self.is_resizing_mode
            self.update()
            return

        if event.button() == Qt.RightButton:
            # Start timer to check if right-click is held for > 2 seconds (Animal Change Menu)
            self.long_click_triggered = False
            self.right_click_timer.start(2000)
            return

        if event.button() == Qt.LeftButton and not self.is_resizing_mode:
            if self.state in ["SLEEPING", "FLEE_SLEEPING"]:
                self.play_sound("snore")
            elif self.state == "FOLLOWING":
                self.play_sound("active")
            
            if self.state != "EXPLODING":
                self.is_mouse_held = True
                self.hold_progress = 0.0
                self.hold_timer.start(100)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.right_click_timer.isActive():
                # Released before 2 seconds -> Open unified Settings Menu (Speed, Color, Sound Level, Close)
                self.right_click_timer.stop()
                if not self.long_click_triggered:
                    self.show_main_right_click_menu(event.globalPos())
            return

        if event.button() == Qt.LeftButton:
            self.is_mouse_held = False
            self.hold_timer.stop()
            
            if self.hold_progress >= 3.0 and not self.is_clone:
                self.start_flee_mode()
                
            self.hold_progress = 0.0
            self.update()

    def handle_long_right_click(self):
        """Triggered if right-click is held for > 2 seconds -> Opens Animal Selection Menu"""
        self.long_click_triggered = True
        self.show_animal_selection_menu(QCursor.pos())

    def show_main_right_click_menu(self, global_pos):
        """Unified clean menu for Speed, Color, Sound Level, and Close"""
        menu = QMenu(self)
        
        # Speed Submenu
        speed_menu = menu.addMenu("Speed")
        for s in range(1, 16):
            action = speed_menu.addAction(f"{s} px")
            action.triggered.connect(lambda checked, val=s: self.set_speed(val))
        
        # Color Picker Action
        color_action = menu.addAction("Color")
        color_action.triggered.connect(self.open_color_dialog)
        
        # Sound Level Submenu (10% to 100%)
        sound_menu = menu.addMenu("Sound Level")
        for pct in range(10, 101, 10):
            action = sound_menu.addAction(f"{pct}%")
            action.triggered.connect(lambda checked, p=pct: self.set_volume(p))
            
        menu.addSeparator()
        
        # Close Pet Action
        close_action = menu.addAction("Close Pet")
        close_action.triggered.connect(self.close_application)
        
        menu.exec_(global_pos)

    def close_application(self):
        if not self.is_clone:
            for c in self.clones:
                c.close()
        self.close()
        QApplication.quit()

    def show_animal_selection_menu(self, global_pos):
        menu = QMenu(self)
        animals = ["Dog", "Cat", "Duck", "Perry the Platypus"]
        for animal in animals:
            action = menu.addAction(animal)
            action.triggered.connect(lambda checked, a=animal: self.change_pet(a))
        menu.exec_(global_pos)

    def set_speed(self, value):
        self.speed = value
        if not self.is_clone:
            for c in self.clones:
                c.speed = value

    def open_color_dialog(self):
        color = QColorDialog.getColor(self.pet_color, self, "Select Pet Color")
        if color.isValid():
            self.pet_color = color
            if not self.is_clone:
                for c in self.clones:
                    c.pet_color = color

    def change_pet(self, new_pet):
        self.stop_all_sounds()
        self.pet_type = new_pet
        defaults = {
            "Dog": QColor(210, 140, 70),
            "Cat": QColor(230, 120, 50),
            "Duck": QColor(255, 220, 50),
            "Perry the Platypus": QColor(0, 160, 160)
        }
        if new_pet in defaults:
            self.pet_color = defaults[new_pet]
        if not self.is_clone:
            for c in self.clones:
                c.pet_type = new_pet
                c.pet_color = self.pet_color

    def check_hold_duration(self):
        if self.is_mouse_held:
            self.hold_progress += 0.1
            self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_resizing_mode and not self.is_clone:
            if self.state in ["FOLLOWING", "WALKING_TO_BED"]:
                self.state = "WALKING_TO_BED"
            elif self.state == "SLEEPING":
                self.state = "FOLLOWING"
                self.stop_snore()
                self.play_sound("active")

    def start_flee_mode(self):
        self.state = "FLEEING"
        self.untouched_time = 0.0
        self.hover_time = 0.0
        self.pick_random_flee_target()

    def start_merge_mode(self):
        self.state = "MERGING"
        for c in self.clones:
            c.state = "MERGING"
        self.stop_snore()

    def pick_random_flee_target(self):
        screen_geo = QApplication.desktop().availableGeometry()
        rx = random.randint(50, max(100, screen_geo.width() - int(150 * self.pet_scale)))
        ry = random.randint(50, max(100, screen_geo.height() - int(150 * self.pet_scale)))
        self.flee_target = QPoint(rx, ry)

    def trigger_explosion_and_respawn(self):
        if self.is_clone:
            if self.is_real_target:
                if self.master_controller:
                    self.master_controller.score += 1
                    self.master_controller.play_sound("explode")
                    self.master_controller.spawn_clones_phase()
                self.close()
            else:
                self.close()
        else:
            self.score += 1
            self.state = "EXPLODING"
            self.explosion_frame = 0
            self.hover_time = 0.0
            self.untouched_time = 0.0
            self.stop_snore()
            self.play_sound("explode")

    def spawn_clones_phase(self):
        screen_geo = QApplication.desktop().availableGeometry()
        for c in self.clones:
            c.close()
        self.clones.clear()
        
        real_target_index = random.randint(0, 4)
        
        for i in range(5):
            rx = random.randint(50, max(100, screen_geo.width() - 150))
            ry = random.randint(50, max(100, screen_geo.height() - 150))
            
            clone = DesktopPet(master_controller=self, is_clone=True)
            clone.pet_type = self.pet_type
            clone.pet_color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            clone.speed = self.speed
            clone.pet_scale = self.pet_scale
            clone.position = QPoint(rx, ry)
            clone.move(clone.position)
            clone.state = "FLEEING"
            clone.is_real_target = (i == real_target_index)
            
            self.clones.append(clone)
            clone.show()
        
        self.hide()

    def finish_respawn(self):
        screen_geo = QApplication.desktop().availableGeometry()
        rx = random.randint(50, max(100, screen_geo.width() - int(150 * self.pet_scale)))
        ry = random.randint(50, max(100, screen_geo.height() - int(150 * self.pet_scale)))
        
        self.position = QPoint(rx, ry)
        self.move(self.position)
        
        self.pet_color = QColor(
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )
        
        if self.score >= 5 and not self.is_clone and len(self.clones) == 0:
            self.spawn_clones_phase()
            return

        self.play_sound("regenerate")
        self.state = "FLEEING"
        self.pick_random_flee_target()

    # =========================================================================
    # BEHAVIOR & MOVEMENT TICK
    # =========================================================================
    def update_behavior(self):
        screen_geo = QApplication.desktop().availableGeometry()
        cursor_pos = QApplication.desktop().cursor().pos()
        
        base_speed = self.speed
        speed = base_speed

        if self.state == "EXPLODING":
            self.explosion_frame += 1
            if self.explosion_frame > 15:
                self.finish_respawn()
            self.update()
            return

        current_size = int(100 * self.pet_scale)
        half_size = current_size // 2

        if self.state == "MERGING":
            if not self.is_clone:
                target_x = cursor_pos.x() - half_size
                target_y = cursor_pos.y() - half_size
                dx = target_x - self.position.x()
                dy = target_y - self.position.y()
                if math.hypot(dx, dy) < 15:
                    self.state = "FOLLOWING"
                    self.score = 0
                    for c in self.clones:
                        c.close()
                    self.clones.clear()
                    self.show()
                else:
                    angle = math.atan2(dy, dx)
                    self.position += QPoint(int(12 * math.cos(angle)), int(12 * math.sin(angle)))
                    self.move(self.position)
            else:
                if self.master_controller:
                    target_x = self.master_controller.position.x()
                    target_y = self.master_controller.position.y()
                    dx = target_x - self.position.x()
                    dy = target_y - self.position.y()
                    if math.hypot(dx, dy) < 15:
                        self.close()
                    else:
                        angle = math.atan2(dy, dx)
                        self.position += QPoint(int(14 * math.cos(angle)), int(14 * math.sin(angle)))
                        self.move(self.position)
            self.update()
            return

        if not self.is_clone and len(self.clones) > 0 and self.state in ["FLEEING", "FLEE_SLEEPING"]:
            all_sleeping = all(c.state == "FLEE_SLEEPING" for c in self.clones)
            if all_sleeping:
                self.stop_snore()
                for c in self.clones:
                    c.stop_snore()
                self.start_merge_mode()
                return

        if self.state == "FOLLOWING":
            target_x = cursor_pos.x() - half_size
            target_y = cursor_pos.y() - half_size

        elif self.state in ["WALKING_TO_BED", "SLEEPING"]:
            target_x = 20
            target_y = screen_geo.height() - current_size - 10

        elif self.state in ["FLEEING", "FLEE_SLEEPING"]:
            pet_center_x = self.position.x() + half_size
            pet_center_y = self.position.y() + half_size
            dist_to_cursor = math.hypot(cursor_pos.x() - pet_center_x, cursor_pos.y() - pet_center_y)
            
            if dist_to_cursor < half_size * 0.7:
                self.hover_time += 0.033
                if self.hover_time >= 1.0:
                    self.trigger_explosion_and_respawn()
                    return
            else:
                self.hover_time = 0.0

            if self.state == "FLEE_SLEEPING":
                if dist_to_cursor <= 50:
                    self.state = "FLEEING"
                    self.untouched_time = 0.0
                    if not self.is_clone:
                        self.stop_snore()
                else:
                    self.is_moving = False
                    self.frame = (self.frame + 1) % 40
                    self.update()
                    return

            if dist_to_cursor > 50:
                self.untouched_time += 0.033
                if self.untouched_time >= 5.0:
                    self.state = "FLEE_SLEEPING"
                    if not self.is_clone:
                        self.play_sound("snore")
                    self.update()
                    return
            else:
                self.untouched_time = 0.0

            if dist_to_cursor < 180:
                speed = base_speed + 8
                escape_dx = pet_center_x - cursor_pos.x()
                escape_dy = pet_center_y - cursor_pos.y()
                
                target_x = int(self.position.x() + escape_dx * 2)
                target_y = int(self.position.y() + escape_dy * 2)
                
                target_x = max(20, min(screen_geo.width() - current_size, target_x))
                target_y = max(20, min(screen_geo.height() - current_size, target_y))
            else:
                target_x = self.flee_target.x()
                target_y = self.flee_target.y()
                
                self.flee_timer_counter += 1
                if self.flee_timer_counter > 40:
                    self.flee_timer_counter = 0
                    self.pick_random_flee_target()

        dx = target_x - self.position.x()
        dy = target_y - self.position.y()
        distance = math.hypot(dx, dy)

        if self.state in ["FOLLOWING", "WALKING_TO_BED", "FLEEING", "MERGING"]:
            if distance > 10:
                self.is_moving = True
                angle = math.atan2(dy, dx)
                
                step_x = int(speed * math.cos(angle))
                step_y = int(speed * math.sin(angle))
                
                self.position += QPoint(step_x, step_y)
                self.move(self.position)
                
                self.facing_right = dx > 0
                self.frame = (self.frame + 1) % 20
            else:
                self.is_moving = False
                self.frame = 0
                if self.state == "WALKING_TO_BED":
                    self.state = "SLEEPING"
                    self.play_sound("snore")
                elif self.state == "FLEEING":
                    self.pick_random_flee_target()
        else:
            self.is_moving = False
            self.frame = (self.frame + 1) % 40

        self.update()

    # =========================================================================
    # PAINTING & RENDERING
    # =========================================================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.scale(self.pet_scale, self.pet_scale)
        
        if self.state == "EXPLODING":
            radius = self.explosion_frame * 4
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 100, 0, max(0, 255 - self.explosion_frame * 15)))
            painter.drawEllipse(50 - radius, 50 - radius, radius * 2, radius * 2)
            core_r = max(1, radius // 2)
            painter.setBrush(QColor(255, 230, 0, max(0, 255 - self.explosion_frame * 12)))
            painter.drawEllipse(50 - core_r, 50 - core_r, core_r * 2, core_r * 2)
            return

        if self.is_resizing_mode:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 150, 255, 200))
            painter.drawRoundedRect(20, 0, 60, 16, 4, 4)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.drawText(20, 0, 60, 16, Qt.AlignCenter, "RESIZING")

        if self.state in ["FLEEING", "FLEE_SLEEPING"] and not self.is_clone:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.drawRoundedRect(25, 0, 50, 18, 4, 4)
            
            painter.setPen(QColor(255, 80, 80))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            display_score = self.master_controller.score if self.is_clone else self.score
            painter.drawText(25, 0, 50, 18, Qt.AlignCenter, f"💀 {display_score}")

        if self.is_mouse_held and self.hold_progress > 0 and not self.is_clone:
            remaining = max(0.0, 3.0 - self.hold_progress)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 160))
            painter.drawEllipse(35, 0, 30, 18)
            
            painter.setPen(QColor(255, 220, 0))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(35, 0, 30, 18, Qt.AlignCenter, f"{remaining:.1f}s")

        if not self.facing_right:
            painter.translate(100, 0)
            painter.scale(-1, 1)

        primary = self.pet_color
        dark = primary.darker(130)
        black = QColor(20, 20, 20)
        is_sleeping = self.state in ["SLEEPING", "FLEE_SLEEPING"]
        
        leg_offset = math.sin(self.frame * 0.6) * 6 if self.is_moving else 0
        wave = math.sin(self.frame * 0.8) * 8 if self.is_moving else 0

        # --- DRAW SELECTED PET ---
        if self.pet_type == "Dog":
            painter.setBrush(dark)
            painter.setPen(Qt.NoPen)
            painter.drawRect(12, int(35 + wave), 14, 6)
            painter.setBrush(primary)
            painter.drawEllipse(20, 30, 45, 30)
            painter.setBrush(dark)
            painter.drawRect(25, int(52 + leg_offset), 8, 16)
            painter.drawRect(52, int(52 - leg_offset), 8, 16)
            painter.setBrush(primary)
            painter.drawRect(32, int(54 - leg_offset), 8, 16)
            painter.drawRect(45, int(54 + leg_offset), 8, 16)
            painter.drawEllipse(50, 15, 30, 30)
            painter.setBrush(dark)
            painter.drawEllipse(48, 20, 12, 22)
            painter.setBrush(primary)
            painter.drawEllipse(68, 28, 16, 14)
            painter.setBrush(black)
            painter.drawEllipse(80, 30, 6, 6)
            
            if is_sleeping:
                painter.setPen(QPen(black, 2))
                painter.drawArc(64, 22, 8, 6, 0, 180 * 16)
                painter.setPen(Qt.NoPen)
            else:
                painter.drawEllipse(66, 23, 5, 5)

        elif self.pet_type == "Cat":
            painter.setBrush(primary)
            painter.setPen(Qt.NoPen)
            painter.drawRect(10, int(25 + wave), 8, 25)
            painter.drawEllipse(20, 32, 42, 26)
            painter.setBrush(dark)
            painter.drawRect(25, int(50 + leg_offset), 6, 16)
            painter.drawRect(50, int(50 - leg_offset), 6, 16)
            painter.setBrush(primary)
            painter.drawRect(32, int(52 - leg_offset), 6, 16)
            painter.drawRect(43, int(52 + leg_offset), 6, 16)
            painter.drawEllipse(48, 18, 28, 26)
            painter.drawPolygon(QPoint(50, 20), QPoint(56, 6), QPoint(62, 18))
            painter.drawPolygon(QPoint(62, 18), QPoint(68, 6), QPoint(74, 20))
            painter.setBrush(black)
            painter.drawEllipse(74, 28, 4, 3)
            
            if is_sleeping:
                painter.setPen(QPen(black, 2))
                painter.drawArc(62, 24, 7, 5, 0, 180 * 16)
                painter.setPen(Qt.NoPen)
            else:
                painter.drawEllipse(65, 26, 4, 4)

        elif self.pet_type == "Duck":
            orange = QColor(245, 140, 20)
            painter.setBrush(primary)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(QPoint(15, 35), QPoint(25, 30), QPoint(22, 42))
            painter.drawEllipse(20, 30, 40, 26)
            painter.setBrush(orange)
            painter.drawEllipse(30, int(52 + leg_offset), 12, 6)
            painter.drawEllipse(42, int(52 - leg_offset), 12, 6)
            painter.setBrush(primary)
            painter.drawEllipse(45, 16, 24, 24)
            painter.setBrush(orange)
            painter.drawRoundedRect(62, 24, 18, 9, 3, 3)
            
            if is_sleeping:
                painter.setPen(QPen(black, 2))
                painter.drawArc(56, 20, 6, 5, 0, 180 * 16)
                painter.setPen(Qt.NoPen)
            else:
                painter.setBrush(black)
                painter.drawEllipse(58, 21, 4, 4)

        elif self.pet_type == "Perry the Platypus":
            orange_bill = QColor(245, 130, 30)
            brown_hat = QColor(100, 60, 20)
            black_band = QColor(20, 20, 20)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(180, 110, 40))
            painter.drawRoundedRect(5, 42, 22, 12, 4, 4)
            painter.setBrush(primary)
            painter.drawRoundedRect(20, 32, 48, 24, 8, 8)
            painter.setBrush(orange_bill)
            painter.drawEllipse(26, int(52 + leg_offset), 10, 6)
            painter.drawEllipse(52, int(52 - leg_offset), 10, 6)
            
            painter.setBrush(primary)
            painter.drawRoundedRect(50, 22, 26, 24, 6, 6)
            painter.setBrush(orange_bill)
            painter.drawRoundedRect(64, 32, 22, 8, 3, 3)
            
            painter.setBrush(brown_hat)
            painter.drawRect(42, 20, 38, 4)
            painter.drawRect(50, 8, 22, 12)
            painter.setBrush(black_band)
            painter.drawRect(50, 16, 22, 4)
            
            if is_sleeping:
                painter.setPen(QPen(black, 2))
                painter.drawArc(58, 24, 8, 6, 0, 180 * 16)
                painter.setPen(Qt.NoPen)
            else:
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(58, 24, 8, 8)
                painter.setBrush(black)
                painter.drawEllipse(62, 26, 4, 4)

        if is_sleeping:
            painter.setPen(QColor(100, 100, 255))
            font = painter.font()
            font.setBold(True)
            z_offset = (self.frame % 20)
            font.setPixelSize(12 + z_offset // 2)
            painter.setFont(font)
            painter.drawText(60 + z_offset, 25 - z_offset, "Z")
            painter.drawText(70 + z_offset, 10 - z_offset, "z")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec_())