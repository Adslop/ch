"""
Floating overlay app implementation for chess analysis
"""
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import ObjectProperty, BooleanProperty

import os
import threading
import time

from chess_analyzer import ChessAnalyzer
from board_detector import ChessBoardDetector
from stockfish_engine import StockfishEngine
from tts_service import TTSService

class ChessOverlayWidget(FloatLayout):
    """Main widget for the chess overlay app"""
    
    def __init__(self, **kwargs):
        super(ChessOverlayWidget, self).__init__(**kwargs)
        
        # Set up components
        self.analyzer = ChessAnalyzer()
        self.board_detector = ChessBoardDetector()
        self.stockfish = StockfishEngine()
        self.tts = TTSService()
        
        # UI elements
        self.layout = BoxLayout(orientation='vertical', 
                               size_hint=(None, None),
                               size=(300, 400),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5})
                               
        # Schedule automatic analysis when app starts
        Clock.schedule_once(lambda dt: self.start_analysis(None), 1)
        
        # App icon that triggers analysis
        self.icon_button = Button(
            text="Chess Analyzer",
            background_normal='',
            background_color=(0.2, 0.6, 0.8, 0.9),
            size_hint=(None, None),
            size=(120, 60),
            border=(0, 0, 0, 0)
        )
        self.icon_button.bind(on_press=self.start_analysis)
        
        # Status label
        self.status_label = Label(
            text="Scanning for chess board...",
            size_hint=(1, None),
            height=40,
            color=(1, 1, 1, 1)
        )
        
        # Setup automatic periodic analysis
        Clock.schedule_interval(lambda dt: self.start_analysis(None), 10)  # Auto-analyze every 10 seconds
        
        # Board representation
        self.board_view = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1)
        )
        
        # Add widgets to layout
        self.layout.add_widget(self.icon_button)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.board_view)
        
        self.add_widget(self.layout)
        
        # Set up touch events for dragging
        self._touch_offset_x = 0
        self._touch_offset_y = 0
        self.analyzing = False
        
        # Best move arrow data
        self.best_move_start = None
        self.best_move_end = None
        
        # Draw best move arrow when available
        Clock.schedule_interval(self.update_display, 0.5)
    
    def on_touch_down(self, touch):
        """Handle touch down event for dragging"""
        if self.layout.collide_point(touch.x, touch.y):
            self._touch_offset_x = touch.x - self.layout.x
            self._touch_offset_y = touch.y - self.layout.y
            return True
        return super(ChessOverlayWidget, self).on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """Handle touch move event for dragging"""
        if hasattr(self, '_touch_offset_x'):
            self.layout.pos = (touch.x - self._touch_offset_x, 
                              touch.y - self._touch_offset_y)
            return True
        return super(ChessOverlayWidget, self).on_touch_move(touch)
    
    def start_analysis(self, instance):
        """Start chess position analysis"""
        if self.analyzing:
            return
        
        self.analyzing = True
        self.status_label.text = "Taking screenshot..."
        
        # Run analysis in a separate thread to avoid blocking UI
        threading.Thread(target=self.analyze_position, daemon=True).start()
    
    def analyze_position(self):
        """Analyze the chess position from a screenshot"""
        try:
            # Take screenshot
            screenshot = self.take_screenshot()
            
            # Update status
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                  "Detecting board..."), 0)
            
            # Detect chess board in screenshot
            board_image = self.board_detector.detect_board(screenshot)
            if board_image is None:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                     "Could not detect chess board"), 0)
                self.analyzing = False
                return
            
            # Update status
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                  "Recognizing position..."), 0)
            
            # Recognize board position
            fen = self.board_detector.get_position_fen(board_image)
            if not fen:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                     "Could not recognize position"), 0)
                self.analyzing = False
                return
            
            # Update status
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                  "Analyzing with Stockfish..."), 0)
            
            # Analyze with Stockfish
            result = self.analyzer.analyze_position(fen)
            
            # Get best move information
            best_move = result.get('best_move')
            score = result.get('score', 0)
            
            # Convert move to chess notation with piece names
            move_text = self.analyzer.format_move_with_pieces(fen, best_move)
            
            # Update the UI with the analysis results
            Clock.schedule_once(lambda dt: self.update_analysis_results(
                best_move, move_text, score), 0)
            
            # Speak the move
            self.tts.speak(f"Best move: {move_text}")
            
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                 f"Error: {str(e)}"), 0)
        finally:
            self.analyzing = False
    
    def update_analysis_results(self, best_move, move_text, score):
        """Update UI with analysis results"""
        self.status_label.text = f"Best move: {move_text}\nScore: {score}"
        
        # Store the move coordinates for drawing the arrow
        self.best_move_start = best_move[:2]  # e.g., "e2"
        self.best_move_end = best_move[2:4]   # e.g., "e4"
    
    def update_display(self, dt):
        """Update the display with arrows for best moves"""
        # This method is called periodically to redraw arrows
        if hasattr(self, 'best_move_start') and self.best_move_start:
            # Ensure we have a canvas to draw on
            self.board_view.canvas.clear()
            with self.board_view.canvas:
                # Draw the arrow for the best move
                Color(0, 1, 0, 0.8)  # Green, semi-transparent
                # Calculate positions based on algebraic notation
                # This is a simplified version, actual implementation
                # would need to map chess coordinates to screen positions
                start_x, start_y = self.algebraic_to_coords(self.best_move_start)
                end_x, end_y = self.algebraic_to_coords(self.best_move_end)
                
                # Draw arrow line
                Line(points=[start_x, start_y, end_x, end_y], width=2)
                
                # Draw arrowhead
                # Simple triangle for the arrowhead
                # This is simplified and would need to be adjusted for actual coordinates
                dx, dy = end_x - start_x, end_y - start_y
                length = (dx**2 + dy**2)**0.5
                if length > 0:
                    dx, dy = dx / length, dy / length
                    x1, y1 = end_x - dx*10 - dy*5, end_y - dy*10 + dx*5
                    x2, y2 = end_x - dx*10 + dy*5, end_y - dy*10 - dx*5
                    Line(points=[end_x, end_y, x1, y1, x2, y2, end_x, end_y], width=2)
    
    def algebraic_to_coords(self, algebraic):
        """Convert algebraic chess notation (e.g., 'e4') to screen coordinates"""
        # This is a placeholder implementation
        # In a real app, you would map the algebraic notation to the actual
        # coordinates on the detected chess board
        
        # For simplicity, we'll just map to a grid in our display area
        file_idx = ord(algebraic[0]) - ord('a')  # 0-7 for a-h
        rank_idx = int(algebraic[1]) - 1         # 0-7 for 1-8
        
        # Calculate coordinates within our board view
        square_size = min(self.board_view.width, self.board_view.height) / 8
        
        x = self.board_view.x + (file_idx + 0.5) * square_size
        y = self.board_view.y + (rank_idx + 0.5) * square_size
        
        return x, y
    
    def take_screenshot(self):
        """Take a screenshot of the device screen"""
        if platform == 'android':
            # Android-specific screenshot code
            from android.permissions import request_permissions, Permission
            from jnius import autoclass
            
            # Request storage permissions if needed
            request_permissions([Permission.READ_EXTERNAL_STORAGE, 
                                Permission.WRITE_EXTERNAL_STORAGE])
            
            # Android classes for screenshot
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # Create a virtual display to get a screenshot
            View = autoclass('android.view.View')
            activity.getWindow().getDecorView().setDrawingCacheEnabled(True)
            bitmap = activity.getWindow().getDecorView().getDrawingCache()
            
            # Convert bitmap to a format OpenCV can use
            ByteBuffer = autoclass('java.nio.ByteBuffer')
            Bitmap = autoclass('android.graphics.Bitmap')
            Config = autoclass('android.graphics.Bitmap.Config')
            
            width, height = bitmap.getWidth(), bitmap.getHeight()
            conf = Config.ARGB_8888
            bitmap2 = Bitmap.createBitmap(width, height, conf)
            Canvas = autoclass('android.graphics.Canvas')
            canvas = Canvas(bitmap2)
            canvas.drawBitmap(bitmap, 0, 0, None)
            
            # Get the pixel data
            buffer = ByteBuffer.allocate(width * height * 4)
            bitmap2.copyPixelsToBuffer(buffer)
            buffer.rewind()
            
            # Convert to a numpy array for OpenCV
            import numpy as np
            binaryData = buffer.array()
            np_data = np.array(list(binaryData)).reshape((height, width, 4))
            screenshot = np_data[:, :, 0:3]  # Remove alpha channel
            
            # Clean up
            activity.getWindow().getDecorView().setDrawingCacheEnabled(False)
            
            return screenshot
        else:
            # For non-Android platforms, use a different method
            # This is just a placeholder - would need a different implementation
            import numpy as np
            
            # Create a dummy screenshot for testing
            return np.zeros((800, 600, 3), dtype=np.uint8)


class ChessOverlayApp(App):
    """Main Application class"""
    
    def build(self):
        """Build the application"""
        # Set up window properties for overlay
        if platform == 'android':
            self.setup_android_overlay()
        else:
            Window.borderless = True
            Window.size = (300, 400)
            Window.clearcolor = (0, 0, 0, 0)
        
        return ChessOverlayWidget()
    
    def setup_android_overlay(self):
        """Set up overlay features for Android"""
        try:
            from jnius import autoclass
            
            # Android classes
            WindowManager = autoclass('android.view.WindowManager$LayoutParams')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # Set window flags for overlay
            window = activity.getWindow()
            window.addFlags(WindowManager.FLAG_NOT_FOCUSABLE)
            window.addFlags(WindowManager.FLAG_LAYOUT_NO_LIMITS)
            window.addFlags(WindowManager.FLAG_NOT_TOUCH_MODAL)
            window.addFlags(WindowManager.FLAG_WATCH_OUTSIDE_TOUCH)
            
        except Exception as e:
            print(f"Error setting up Android overlay: {e}")
