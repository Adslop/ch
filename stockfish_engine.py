"""
Stockfish engine integration for chess analysis
"""
import os
import subprocess
import time
import tempfile
import threading
import chess
import chess.engine
from kivy.utils import platform

class StockfishEngine:
    """
    Integrates with Stockfish 17 chess engine for position analysis
    """
    
    def __init__(self):
        """Initialize Stockfish engine"""
        self.stockfish_path = self._get_stockfish_path()
        self.engine = None
        self.engine_lock = threading.Lock()
        self._init_engine()
    
    def _get_stockfish_path(self):
        """Get the appropriate Stockfish binary path based on platform"""
        if platform == 'android':
            # On Android, Stockfish binary should be included in the app
            # and extracted to the app's private storage
            from android.storage import app_storage_path
            from jnius import autoclass
            
            # Get the app's private directory
            app_dir = app_storage_path()
            
            # Get the app's assets
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            assets = activity.getAssets()
            
            # Create the path where we'll extract Stockfish
            stockfish_path = os.path.join(app_dir, 'stockfish')
            
            # Check if we need to extract the binary
            if not os.path.exists(stockfish_path):
                try:
                    # Open the asset (Stockfish 17 binary)
                    input_stream = assets.open('stockfish')
                    
                    # Create the output file
                    with open(stockfish_path, 'wb') as out_file:
                        # Read and write in chunks
                        buff = bytearray(1024)
                        while True:
                            length = input_stream.read(buff)
                            if length <= 0:
                                break
                            out_file.write(buff, 0, length)
                    
                    # Close the input stream
                    input_stream.close()
                    
                    # Make the extracted file executable
                    os.chmod(stockfish_path, 0o755)
                    
                    print("Stockfish 17 extracted successfully")
                except Exception as e:
                    print(f"Error extracting Stockfish: {e}")
                    # Fallback to a default location
                    stockfish_path = '/data/data/org.test.chess_analyzer/files/stockfish'
            
            return stockfish_path
        elif platform == 'win':
            return 'stockfish_17.exe'  # For Windows
        else:
            # For testing in Replit or other Linux environments
            # In a real app, you would bundle Stockfish 17 with your application
            # and extract it to a suitable location
            stockfish_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stockfish')
            if not os.path.exists(stockfish_path):
                # Fallback to system stockfish
                return 'stockfish'
            return stockfish_path
    
    def _init_engine(self):
        """Initialize the Stockfish engine"""
        try:
            # Start the engine process
            with self.engine_lock:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                
                # Configure Stockfish
                self.engine.configure({
                    "Threads": 2,  # Use 2 threads for analysis
                    "Hash": 32,    # Use 32 MB of memory
                })
        except Exception as e:
            print(f"Error initializing Stockfish: {e}")
            self.engine = None
    
    def get_best_move(self, fen, depth=18, time_limit=2.0):
        """
        Get the best move for a position
        
        Args:
            fen: FEN string for the position
            depth: Maximum search depth
            time_limit: Time limit in seconds
            
        Returns:
            Dictionary with best move and evaluation
        """
        if not self.engine:
            try:
                self._init_engine()
                if not self.engine:
                    return {"error": "Could not initialize engine"}
            except Exception as e:
                return {"error": f"Engine error: {str(e)}"}
        
        try:
            # Create a board from the FEN
            board = chess.Board(fen)
            
            # Create a time limit
            limit = chess.engine.Limit(depth=depth, time=time_limit)
            
            # Get analysis
            with self.engine_lock:
                info = self.engine.analyse(board, limit)
                
                # Extract the principal variation (sequence of best moves)
                pv = []
                if 'pv' in info:
                    for move in info['pv']:
                        pv.append(move.uci())
                
                # Get the best move
                result = self.engine.play(board, limit)
                best_move = result.move.uci() if result.move else None
                
                # Get the score
                score = None
                if 'score' in info:
                    score_obj = info['score']
                    if score_obj.is_mate():
                        # It's a mate score
                        mate_in = score_obj.mate()
                        score = f"Mate in {mate_in}" if mate_in > 0 else f"Mated in {-mate_in}"
                    else:
                        # It's a centipawn score
                        cp = score_obj.cp
                        score = f"{cp/100:.2f}" if cp is not None else "0.00"
                
                return {
                    "best_move": best_move,
                    "score": score,
                    "depth": info.get('depth', 0),
                    "pv": pv
                }
                
        except Exception as e:
            print(f"Analysis error: {e}")
            return {"error": f"Analysis error: {str(e)}"}
    
    def quit(self):
        """Shut down the engine properly"""
        if self.engine:
            with self.engine_lock:
                self.engine.quit()
                self.engine = None
