"""
Chess position analyzer using Stockfish
"""
import chess
import chess.engine
import os
import tempfile
import time
from stockfish_engine import StockfishEngine

class ChessAnalyzer:
    """
    Handles chess position analysis using Stockfish engine
    """
    
    def __init__(self):
        """Initialize the chess analyzer"""
        self.stockfish = StockfishEngine()
        
        # Piece name mapping
        self.piece_names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }
    
    def analyze_position(self, fen, depth=18, time_limit=2.0):
        """
        Analyze a chess position and return the best move
        
        Args:
            fen: The FEN string representing the chess position
            depth: The search depth (default: 18)
            time_limit: Time limit in seconds (default: 2.0)
            
        Returns:
            Dict containing best move and evaluation
        """
        # Create a chess board from the FEN
        try:
            board = chess.Board(fen)
        except ValueError:
            return {"error": "Invalid FEN string"}
        
        # Get the analysis from Stockfish
        result = self.stockfish.get_best_move(fen, depth, time_limit)
        
        # Return formatted result
        return {
            "fen": fen,
            "best_move": result.get("best_move"),
            "score": result.get("score"),
            "depth": result.get("depth"),
            "pv": result.get("pv", [])
        }
    
    def format_move_with_pieces(self, fen, move_uci):
        """
        Format a UCI move with piece names for text-to-speech
        
        Args:
            fen: The FEN string of the position
            move_uci: The move in UCI format (e.g., "e2e4")
            
        Returns:
            String with formatted move description including piece names
        """
        if not move_uci or len(move_uci) < 4:
            return "No move available"
        
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(move_uci)
            
            # Get the piece type
            piece = board.piece_at(move.from_square)
            if not piece:
                return f"Move from {chess.square_name(move.from_square)} to {chess.square_name(move.to_square)}"
            
            piece_name = self.piece_names.get(piece.piece_type, "piece")
            color = "white" if piece.color == chess.WHITE else "black"
            
            # Check if the move is a capture
            capture = ""
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    captured_color = "white" if captured_piece.color == chess.WHITE else "black"
                    captured_name = self.piece_names.get(captured_piece.piece_type, "piece")
                    capture = f", capturing the {captured_color} {captured_name}"
            
            # Check if it's a promotion
            promotion = ""
            if move.promotion:
                promoted_piece = self.piece_names.get(move.promotion, "piece")
                promotion = f", promoting to a {promoted_piece}"
            
            # Special cases
            special_move = ""
            if board.is_castling(move):
                if chess.square_file(move.to_square) > chess.square_file(move.from_square):
                    special_move = " (kingside castling)"
                else:
                    special_move = " (queenside castling)"
                    
            # Check if it's a check or checkmate
            board.push(move)
            check_status = ""
            if board.is_check():
                if board.is_checkmate():
                    check_status = ", checkmate"
                else:
                    check_status = ", check"
            
            # Format the full move description
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            
            return f"{color} {piece_name} from {from_square} to {to_square}{capture}{promotion}{special_move}{check_status}"
            
        except Exception as e:
            return f"Move {move_uci}"
