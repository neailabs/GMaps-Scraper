#!/usr/bin/env python3
"""
Google Maps Listings Scraper
Main entry point for the application.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import GmapsCrawler
from src.models import AppConfig


def main():
    """Main application entry point."""
    # Create QApplication instance
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName(AppConfig.WINDOW_TITLE)
    app.setApplicationDisplayName(AppConfig.MENU_DISPLAY_NAME)
    app.setApplicationVersion(AppConfig.VERSION)
    app.setOrganizationName(AppConfig.COMPANY_NAME)
    
    # Set application icon if available
    if os.path.exists(AppConfig.ICON_PATH):
        app.setWindowIcon(QIcon(AppConfig.ICON_PATH))
    
    # Create and show main window
    window = GmapsCrawler()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
