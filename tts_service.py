"""
Text-to-speech service for announcing chess moves
"""
import os
import threading
from kivy.utils import platform

class TTSService:
    """
    Text-to-speech service for announcing chess analysis
    """
    
    def __init__(self):
        """Initialize the TTS engine based on platform"""
        self.tts_engine = None
        self._init_tts()
    
    def _init_tts(self):
        """Initialize the appropriate TTS engine based on platform"""
        if platform == 'android':
            self._init_android_tts()
        else:
            self._init_pyttsx3()
    
    def _init_android_tts(self):
        """Initialize Android TTS"""
        try:
            from jnius import autoclass
            
            # Get Android TextToSpeech classes
            Locale = autoclass('java.util.Locale')
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            # Get the current activity
            activity = PythonActivity.mActivity
            
            # Initialize TextToSpeech
            tts_listener = autoclass('org.kivy.android.PythonActivity$TTSListener')
            self.tts_engine = TextToSpeech(activity, tts_listener)
            
            # Set language to English
            self.tts_engine.setLanguage(Locale.US)
            
            # Set speech rate
            self.tts_engine.setSpeechRate(0.9)  # Slightly slower than normal
            
            print("Android TTS initialized")
        except Exception as e:
            print(f"Error initializing Android TTS: {e}")
            # Fallback to a dummy TTS
            self.tts_engine = None
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 for non-Android platforms"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure voice properties
            self.tts_engine.setProperty('rate', 160)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Try to use a better voice if available
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                # Try to find a female voice in English
                if "english" in voice.name.lower() and ("female" in voice.name.lower() or "f" in voice.id.lower()):
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            print("pyttsx3 TTS initialized")
        except Exception as e:
            print(f"Error initializing pyttsx3: {e}")
            self.tts_engine = None
    
    def speak(self, text):
        """
        Speak the given text using the appropriate TTS engine
        
        Args:
            text: Text to be spoken
        """
        if not text:
            return
            
        # Speak in a separate thread to avoid blocking the UI
        threading.Thread(target=self._speak_threaded, args=(text,), daemon=True).start()
    
    def _speak_threaded(self, text):
        """
        Internal method to speak text in a separate thread
        
        Args:
            text: Text to be spoken
        """
        if not self.tts_engine:
            print(f"TTS not available. Text: {text}")
            return
            
        try:
            if platform == 'android':
                # For Android TTS
                from jnius import autoclass
                
                # Constants for TextToSpeech
                QUEUE_ADD = 1  # Add to queue rather than flush queue
                
                # Speak the text
                self.tts_engine.speak(text, QUEUE_ADD, None)
            else:
                # For pyttsx3
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error speaking text: {e}")
