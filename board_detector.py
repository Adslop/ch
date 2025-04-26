"""
Chess board detector using OpenCV
"""
import os
import numpy as np
import cv2
import chess
from kivy.utils import platform

class ChessBoardDetector:
    """
    Detects chess boards in images and extracts position information
    """
    
    def __init__(self):
        """Initialize board detector with piece detection models"""
        # Initialize the piece detector
        # This would normally use a pre-trained neural network model
        # For simplicity, we'll use a basic approach with template matching
        
        # Load piece templates - these would be actual templates in a real implementation
        self.piece_templates = self._init_piece_templates()
        
        # Board detection parameters
        self.min_board_size = 200  # Minimum expected board size in pixels
        self.square_threshold = 0.7  # Threshold for square detection
    
    def _init_piece_templates(self):
        """Initialize piece templates for recognition"""
        # In a real implementation, we would load actual templates or models
        # This is a simple placeholder
        templates = {
            'white_pawn': None, 'white_knight': None, 'white_bishop': None,
            'white_rook': None, 'white_queen': None, 'white_king': None,
            'black_pawn': None, 'black_knight': None, 'black_bishop': None,
            'black_rook': None, 'black_queen': None, 'black_king': None
        }
        return templates
    
    def detect_board(self, image):
        """
        Detect chess board in an image
        
        Args:
            image: OpenCV image (numpy array)
            
        Returns:
            Cropped and perspective-corrected image of the chess board
        """
        # Convert to grayscale if it's a color image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply adaptive thresholding to get binary image
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size and shape
        for contour in contours:
            # Approximate contour as a polygon
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            
            # Check if the contour is roughly square (4 corners) and of sufficient size
            if len(approx) == 4 and cv2.contourArea(contour) > self.min_board_size * self.min_board_size:
                # Perspective transform to get a top-down view
                # Get corners in the right order
                corners = sorted(approx.reshape(-1, 2), key=lambda p: p[0] + p[1])
                top_left = corners[0]
                bottom_right = corners[3]
                
                # Sort the remaining corners
                remaining = [corners[1], corners[2]]
                remaining.sort(key=lambda p: p[1] - p[0])
                top_right = remaining[0]
                bottom_left = remaining[1]
                
                src_pts = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
                
                # Calculate the target size (making it square)
                width = max(
                    np.linalg.norm(top_right - top_left),
                    np.linalg.norm(bottom_right - bottom_left)
                )
                height = max(
                    np.linalg.norm(bottom_left - top_left),
                    np.linalg.norm(bottom_right - top_right)
                )
                square_size = max(int(width), int(height))
                
                dst_pts = np.array([
                    [0, 0],
                    [square_size - 1, 0],
                    [square_size - 1, square_size - 1],
                    [0, square_size - 1]
                ], dtype=np.float32)
                
                # Apply perspective transform
                M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped = cv2.warpPerspective(image, M, (square_size, square_size))
                
                return warped
        
        # No valid board found
        return None
    
    def get_position_fen(self, board_image):
        """
        Extract chess position from board image and return FEN string
        
        Args:
            board_image: Cropped and rectified image of a chess board
            
        Returns:
            FEN string representing the board position
        """
        # In a real implementation, this would use a trained model
        # For chess piece recognition. Here we'll return a default position
        # as a simplified placeholder.
        
        # Placeholder implementation:
        # 1. We would divide the board into 64 squares
        # 2. For each square, classify if it's empty or contains a piece
        # 3. Classify piece type and color
        # 4. Construct FEN string
        
        try:
            # Divide the board into squares
            height, width = board_image.shape[:2]
            square_size = height // 8
            
            # Initialize empty board representation
            board = [[' ' for _ in range(8)] for _ in range(8)]
            
            # For each square on the board
            for row in range(8):
                for col in range(8):
                    # Extract the square image
                    y1 = row * square_size
                    y2 = (row + 1) * square_size
                    x1 = col * square_size
                    x2 = (col + 1) * square_size
                    
                    square_img = board_image[y1:y2, x1:x2]
                    
                    # In a real implementation, here we would:
                    # 1. Determine if the square is empty
                    # 2. If not empty, classify the piece (type and color)
                    
                    # For demo, we'll use a placeholder function
                    piece = self._detect_piece_on_square(square_img)
                    if piece:
                        board[7-row][col] = piece
            
            # Convert board array to FEN
            fen = self._board_to_fen(board)
            return fen
            
        except Exception as e:
            print(f"Error in position extraction: {str(e)}")
            # Return starting position as fallback
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    def _detect_piece_on_square(self, square_img):
        """
        Detect chess piece in a square image
        
        Args:
            square_img: Image of a single chess square
            
        Returns:
            Piece code or None if empty
        """
        # Placeholder implementation - in a real app this would use ML
        # For simplicity, we'll just check brightness and color
        # to estimate if there's a piece and if it's white or black
        
        # Convert to grayscale and calculate average brightness
        if len(square_img.shape) == 3:
            gray = cv2.cvtColor(square_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = square_img
            
        avg_brightness = np.mean(gray)
        
        # If brightness is mid-range, assume empty square
        if 90 < avg_brightness < 170:
            return ' '
        
        # Very bright - assume white piece, darker - assume black
        if avg_brightness >= 170:
            # Simplified: return white pawn
            return 'P'
        else:
            # Simplified: return black pawn
            return 'p'
    
    def _board_to_fen(self, board):
        """
        Convert board array to FEN string
        
        Args:
            board: 8x8 array with piece symbols
            
        Returns:
            FEN string
        """
        fen = ""
        for row in range(8):
            empty_count = 0
            for col in range(8):
                if board[row][col] == ' ':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    fen += board[row][col]
            if empty_count > 0:
                fen += str(empty_count)
            if row < 7:
                fen += "/"
                
        # For simplicity, assume it's white's turn and all castling rights available
        fen += " w KQkq - 0 1"
        
        return fen
