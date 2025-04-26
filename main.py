"""
Main entry point for the Chess Analyzer Overlay App
"""
import os
import threading
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform
from overlay_app import ChessOverlayApp

# Check if running on Android
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

def request_android_permissions():
    """Request necessary permissions on Android"""
    if platform == 'android':
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.SYSTEM_ALERT_WINDOW,  # For overlay
            Permission.FOREGROUND_SERVICE,   # For background service
        ])

def main():
    """Main function to start the app"""
    # Request necessary permissions on Android
    if platform == 'android':
        request_android_permissions()
        
        # Setup for overlay on Android
        try:
            # Setting up Android system overlay permissions
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            
            # Check if we have overlay permission
            if not Settings.canDrawOverlays(activity):
                intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
                activity.startActivity(intent)
                print("Please grant overlay permission and restart the app")
                return
        except Exception as e:
            print(f"Error setting up overlay permissions: {e}")
    
    # Start the app
    app = ChessOverlayApp()
    app.run()

if __name__ == '__main__':
    main()
