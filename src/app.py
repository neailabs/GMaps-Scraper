"""
Main application window for the Google Maps Listings Scraper.
"""

import os
import sys
import googlemaps
from typing import List, Set, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QHeaderView, QMessageBox, QMenuBar,
    QTextEdit, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QAction, QKeySequence
from PySide6.QtWidgets import QAbstractItemView

from src.models import BusinessRecord, AppConfig
from src.worker import DataFetcherWorker
from src.utils import FileHandler, UIHelper, validate_api_key, validate_search_query


class AboutDialog(QDialog):
    """About dialog for the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Google Maps Scraper")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Application info
        info_text = f"""
        <h2>{AppConfig.WINDOW_TITLE}</h2>
        <p><b>Version:</b> 1.0.5</p>
        <p><b>Company:</b> {AppConfig.COMPANY_NAME}</p>
        <p><b>Website:</b> <a href="{AppConfig.COMPANY_URL}">{AppConfig.COMPANY_URL}</a></p>
        
        <p>A powerful tool for scraping business listings from Google Maps using the Google Places API.</p>
        
        <p><b>Features:</b></p>
        <ul>
            <li>Search for businesses by query</li>
            <li>Export data to JSON format</li>
            <li>Load existing data files</li>
            <li>Pagination support for large datasets</li>
        </ul>
        
        <p><small>Built with PySide6 and Python</small></p>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        layout.addWidget(info_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class HelpDialog(QDialog):
    """Help dialog for the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help - Google Maps Scraper")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Help content
        help_text = """
        <h2>Google Maps Scraper Help</h2>
        
        <h3>Getting Started</h3>
        <p>1. <b>API Key:</b> Enter your Google Maps API key in the API Key field. You can get this from the Google Cloud Console.</p>
        <p>2. <b>Search Query:</b> Enter your search query (e.g., "restaurants in New York", "hotels in Paris").</p>
        <p>3. <b>Number of Listings:</b> Set how many listings you want to fetch (maximum 60 per request).</p>
        <p>4. Click <b>Fetch Data</b> to start scraping.</p>
        
        <h3>Features</h3>
        <p><b>Continue Fetching:</b> If there are more results available, use this to get additional pages of data.</p>
        <p><b>Load Existing File:</b> Load previously saved data to avoid duplicates when continuing a search.</p>
        <p><b>Save as JSON:</b> Export your scraped data to a JSON file for further processing.</p>
        
        <h3>File Formats Supported</h3>
        <ul>
            <li>JSON (.json) - Recommended for data exchange</li>
            <li>CSV (.csv) - For spreadsheet applications</li>
            <li>Excel (.xlsx, .xls) - For Microsoft Excel</li>
        </ul>
        
        <h3>Tips</h3>
        <ul>
            <li>Use specific search queries for better results</li>
            <li>Check "Continue Fetching" to automatically load more results</li>
            <li>Save your data regularly to avoid losing progress</li>
            <li>Use the existing file feature to resume interrupted searches</li>
        </ul>
        
        <h3>Troubleshooting</h3>
        <p><b>API Errors:</b> Make sure your API key is valid and has the Places API enabled.</p>
        <p><b>No Results:</b> Try different search queries or check your internet connection.</p>
        <p><b>Rate Limits:</b> Google API has rate limits. If you hit them, wait a moment before continuing.</p>
        """
        
        help_content = QTextEdit()
        help_content.setHtml(help_text)
        help_content.setReadOnly(True)
        
        layout.addWidget(help_content)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class GmapsCrawler(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data structures
        self.fetched_data: List[BusinessRecord] = []
        self.existing_links: Set[str] = set()
        self.next_page_token: Optional[str] = None
        self.input_file_path: Optional[str] = None
        self.gmaps: Optional[googlemaps.Client] = None
        self.worker_thread: Optional[DataFetcherWorker] = None
        self.is_fetching = False
        
        # Setup UI
        self.setup_ui()
        self.setup_menus()
        self.setup_connections()
        self.update_button_states()
        
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle(AppConfig.WINDOW_TITLE)
        self.setMinimumSize(900, 600)
        
        # Set window icon if available
        if os.path.exists(AppConfig.ICON_PATH):
            self.setWindowIcon(QIcon(AppConfig.ICON_PATH))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Input panel
        input_group = self.create_input_panel()
        main_layout.addWidget(input_group)
        
        # Data table
        self.table_widget = self.create_data_table()
        main_layout.addWidget(self.table_widget)
        
        # Action buttons
        button_layout = self.create_action_buttons()
        main_layout.addLayout(button_layout)
        
        # Credits footer
        credits_layout = self.create_credits_footer()
        main_layout.addLayout(credits_layout)
        
    def setup_menus(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Start a new search")
        new_action.triggered.connect(self.new_search)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open existing data file")
        open_action.triggered.connect(self.load_existing_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save action
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setStatusTip("Save current data")
        self.save_action.triggered.connect(self.save_as_json)
        self.save_action.setEnabled(False)
        file_menu.addAction(self.save_action)
        
        # Save As action
        self.save_as_action = QAction("Save &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.setStatusTip("Save current data with new name")
        self.save_as_action.triggered.connect(self.save_as_json)
        self.save_as_action.setEnabled(False)
        file_menu.addAction(self.save_as_action)
        
        # Export submenu
        export_menu = file_menu.addMenu("&Export")
        
        self.export_csv_action = QAction("Export as &CSV...", self)
        self.export_csv_action.setStatusTip("Export data to CSV file")
        self.export_csv_action.triggered.connect(self.export_as_csv)
        self.export_csv_action.setEnabled(False)
        export_menu.addAction(self.export_csv_action)
        
        self.export_excel_action = QAction("Export as &Excel...", self)
        self.export_excel_action.setStatusTip("Export data to Excel file")
        self.export_excel_action.triggered.connect(self.export_as_excel)
        self.export_excel_action.setEnabled(False)
        export_menu.addAction(self.export_excel_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Clear action
        clear_action = QAction("&Clear Data", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.setStatusTip("Clear all fetched data")
        clear_action.triggered.connect(self.clear_data)
        edit_menu.addAction(clear_action)
        
        edit_menu.addSeparator()
        
        # Select All action
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.setStatusTip("Select all table rows")
        select_all_action.triggered.connect(self.select_all_table)
        edit_menu.addAction(select_all_action)
        
        # Copy action
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setStatusTip("Copy selected data to clipboard")
        copy_action.triggered.connect(self.copy_selected_data)
        edit_menu.addAction(copy_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.setStatusTip("Refresh the data table")
        refresh_action.triggered.connect(self.refresh_table)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setStatusTip("Increase font size")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setStatusTip("Decrease font size")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.setStatusTip("Reset font size to default")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        # Help action
        help_action = QAction("&Help", self)
        help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.setStatusTip("Show help documentation")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        # Visit Website action
        website_action = QAction("Visit &Github &Page", self)
        website_action.setStatusTip(f"Visit {AppConfig.COMPANY_NAME} website")
        website_action.triggered.connect(self.visit_website)
        help_menu.addAction(website_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # About Qt action
        about_qt_action = QAction("About &Qt", self)
        about_qt_action.setStatusTip("About Qt framework")
        about_qt_action.triggered.connect(self.show_about_qt)
        help_menu.addAction(about_qt_action)
    
    def create_input_panel(self) -> QWidget:
        """Create the input panel with form fields."""
        group_widget = QWidget()
        layout = QGridLayout(group_widget)
        layout.setSpacing(10)
        
        # API Key field
        layout.addWidget(QLabel("API Key:"), 0, 0)
        self.api_key_input = QLineEdit()
        self.api_key_input.setFixedWidth(AppConfig.INPUT_FIELD_WIDTH)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your Google Maps API key")
        layout.addWidget(self.api_key_input, 0, 1)
        
        # Search Query field
        layout.addWidget(QLabel("Search Query:"), 1, 0)
        self.search_query_input = QLineEdit()
        self.search_query_input.setFixedWidth(AppConfig.INPUT_FIELD_WIDTH)
        self.search_query_input.setPlaceholderText("e.g., restaurants in New York")
        layout.addWidget(self.search_query_input, 1, 1)
        
        # Number of Listings spinbox
        layout.addWidget(QLabel("Number of Listings:"), 2, 0)
        self.num_listings_spinbox = QSpinBox()
        self.num_listings_spinbox.setRange(AppConfig.SPINBOX_MIN, AppConfig.SPINBOX_MAX)
        self.num_listings_spinbox.setValue(AppConfig.DEFAULT_RECORD_COUNT)
        layout.addWidget(self.num_listings_spinbox, 2, 1)
        
        # Fetched count label
        layout.addWidget(QLabel("Fetched Count:"), 3, 0)
        self.fetched_count_label = QLabel("0")
        self.fetched_count_label.setStyleSheet(f"color: {AppConfig.BRAND_COLOR}; font-weight: bold;")
        layout.addWidget(self.fetched_count_label, 3, 1)
        
        # Continue fetching checkbox
        self.continue_fetching_checkbox = QCheckBox("Continue Fetching")
        self.continue_fetching_checkbox.setChecked(True)
        layout.addWidget(self.continue_fetching_checkbox, 4, 0, 1, 2)
        
        # Existing data file
        layout.addWidget(QLabel("Existing Data File:"), 5, 0)
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.load_file_button = QPushButton("Load File")
        self.load_file_button.setFixedWidth(100)
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.load_file_button)
        layout.addLayout(file_layout, 5, 1)
        
        return group_widget
    
    def create_data_table(self) -> QTableWidget:
        """Create the data display table."""
        table = QTableWidget()
        table.setColumnCount(len(AppConfig.TABLE_COLUMNS))
        table.setHorizontalHeaderLabels(AppConfig.TABLE_COLUMNS)
        
        # Table properties
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        # Header properties
        header = table.horizontalHeader()
        header.setStretchLastSection(True)  # Stretch last column
        for i in range(len(AppConfig.TABLE_COLUMNS) - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        return table
    
    def create_action_buttons(self) -> QHBoxLayout:
        """Create the action buttons layout."""
        layout = QHBoxLayout()
        
        # Fetch Data button
        self.fetch_button = QPushButton("Fetch Data")
        self.fetch_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppConfig.BRAND_COLOR};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #d91e50;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)
        
        # Continue Fetching button
        self.continue_button = QPushButton("Continue Fetching")
        self.continue_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppConfig.ACCENT_COLOR};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #26a8d1;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)
        
        # Save as JSON button
        self.save_json_button = QPushButton("Save as JSON")
        self.save_json_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        layout.addWidget(self.fetch_button)
        layout.addWidget(self.continue_button)
        layout.addWidget(self.save_json_button)
        layout.addStretch()  # Push buttons to the left
        
        return layout
    
    def create_credits_footer(self) -> QHBoxLayout:
        """Create the credits footer."""
        layout = QHBoxLayout()
        
        credits_label = QLabel(f'Created by <a href="{AppConfig.COMPANY_URL}" style="color: {AppConfig.BRAND_COLOR};">{AppConfig.COMPANY_NAME}</a>')
        credits_label.setOpenExternalLinks(True)
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setStyleSheet("font-size: 12px; color: gray;")
        
        layout.addStretch()
        layout.addWidget(credits_label)
        layout.addStretch()
        
        return layout
    
    def setup_connections(self):
        """Setup signal-slot connections."""
        self.fetch_button.clicked.connect(self.start_fetching)
        self.continue_button.clicked.connect(self.continue_fetching)
        self.save_json_button.clicked.connect(self.save_as_json)
        self.load_file_button.clicked.connect(self.load_existing_file)
    
    def update_button_states(self):
        """Update button enabled/disabled states."""
        has_data = len(self.fetched_data) > 0
        has_pagination = self.next_page_token is not None
        
        self.fetch_button.setEnabled(not self.is_fetching)
        self.continue_button.setEnabled(not self.is_fetching and has_pagination)
        self.save_json_button.setEnabled(has_data and not self.is_fetching)
        
        # Update menu actions
        self.save_action.setEnabled(has_data and not self.is_fetching)
        self.save_as_action.setEnabled(has_data and not self.is_fetching)
        self.export_csv_action.setEnabled(has_data and not self.is_fetching)
        self.export_excel_action.setEnabled(has_data and not self.is_fetching)
    
    # Menu Action Handlers
    def new_search(self):
        """Start a new search (clear all data)."""
        if self.is_fetching:
            UIHelper.show_warning_message(self, "Operation in Progress", 
                                        "Please wait for the current operation to complete.")
            return
        
        if self.fetched_data:
            reply = QMessageBox.question(
                self, "New Search", 
                "This will clear all current data. Are you sure?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.clear_data()
        self.api_key_input.clear()
        self.search_query_input.clear()
        self.num_listings_spinbox.setValue(AppConfig.DEFAULT_RECORD_COUNT)
        self.continue_fetching_checkbox.setChecked(True)
        self.file_path_label.setText("No file selected")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        self.input_file_path = None
    
    def clear_data(self):
        """Clear all fetched data."""
        self.fetched_data.clear()
        self.existing_links.clear()
        self.next_page_token = None
        self.table_widget.setRowCount(0)
        self.fetched_count_label.setText("0")
        self.update_button_states()
    
    def select_all_table(self):
        """Select all rows in the table."""
        self.table_widget.selectAll()
    
    def copy_selected_data(self):
        """Copy selected table data to clipboard."""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return
        
        # Get selected rows
        selected_rows = set()
        for item in selected_items:
            selected_rows.add(item.row())
        
        # Build clipboard text
        clipboard_text = []
        headers = [self.table_widget.horizontalHeaderItem(i).text() 
                  for i in range(self.table_widget.columnCount())]
        clipboard_text.append("\t".join(headers))
        
        for row in sorted(selected_rows):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            clipboard_text.append("\t".join(row_data))
        
        # Copy to clipboard
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText("\n".join(clipboard_text))
        
        UIHelper.show_info_message(self, "Copied", 
                                 f"Copied {len(selected_rows)} rows to clipboard.")
    
    def refresh_table(self):
        """Refresh the data table."""
        if self.fetched_data:
            self.table_widget.setRowCount(0)
            self.update_table_with_records(self.fetched_data)
    
    def zoom_in(self):
        """Increase font size."""
        font = self.font()
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)
    
    def zoom_out(self):
        """Decrease font size."""
        font = self.font()
        if font.pointSize() > 8:  # Minimum font size
            font.setPointSize(font.pointSize() - 1)
            self.setFont(font)
    
    def reset_zoom(self):
        """Reset font size to default."""
        font = self.font()
        font.setPointSize(9)  # Default font size
        self.setFont(font)
    
    def export_as_csv(self):
        """Export data as CSV file."""
        if not self.fetched_data:
            UIHelper.show_warning_message(self, "No Data", "No data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export as CSV", "google_maps_listings.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                FileHandler.save_to_csv(self.fetched_data, file_path)
                UIHelper.show_info_message(self, "Success", 
                                         f"Successfully exported {len(self.fetched_data)} records to CSV.")
            except Exception as e:
                UIHelper.show_error_message(self, "Export Error", 
                                          f"Failed to export CSV: {str(e)}")
    
    def export_as_excel(self):
        """Export data as Excel file."""
        if not self.fetched_data:
            UIHelper.show_warning_message(self, "No Data", "No data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export as Excel", "google_maps_listings.xlsx", "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                FileHandler.save_to_excel(self.fetched_data, file_path)
                UIHelper.show_info_message(self, "Success", 
                                         f"Successfully exported {len(self.fetched_data)} records to Excel.")
            except Exception as e:
                UIHelper.show_error_message(self, "Export Error", 
                                          f"Failed to export Excel: {str(e)}")
    
    def show_help(self):
        """Show help dialog."""
        help_dialog = HelpDialog(self)
        help_dialog.exec()
    
    def visit_website(self):
        """Visit Github Page."""
        QDesktopServices.openUrl(QUrl(AppConfig.APPLICATION_URL))
    
    def show_about(self):
        """Show about dialog."""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
    
    def show_about_qt(self):
        """Show about Qt dialog."""
        QMessageBox.aboutQt(self, "About Qt")
    
    def start_fetching(self):
        """Start fetching data from Google Maps API."""
        # Validate inputs
        api_key = self.api_key_input.text().strip()
        query = self.search_query_input.text().strip()
        
        if not validate_api_key(api_key):
            UIHelper.show_error_message(self, "Invalid API Key", 
                                      "Please enter a valid Google Maps API key.")
            return
        
        if not validate_search_query(query):
            UIHelper.show_error_message(self, "Invalid Search Query", 
                                      "Please enter a valid search query (at least 2 characters).")
            return
        
        # Initialize Google Maps client
        try:
            self.gmaps = googlemaps.Client(key=api_key)
        except Exception as e:
            UIHelper.show_error_message(self, "API Error", 
                                      f"Failed to initialize Google Maps client: {str(e)}")
            return
        
        # Reset data for new search
        self.fetched_data.clear()
        self.existing_links.clear()
        self.next_page_token = None
        self.table_widget.setRowCount(0)
        self.fetched_count_label.setText("0")
        
        # Start fetching
        self._start_worker_thread()
    
    def continue_fetching(self):
        """Continue fetching with pagination."""
        if not self.gmaps or not self.next_page_token:
            return
        
        self._start_worker_thread()
    
    def _start_worker_thread(self):
        """Start the worker thread for API operations."""
        if self.is_fetching or not self.gmaps:
            return
        
        self.is_fetching = True
        self.update_button_states()
        
        # Create and start worker thread
        self.worker_thread = DataFetcherWorker(
            gmaps_client=self.gmaps,
            query=self.search_query_input.text().strip(),
            num_records=self.num_listings_spinbox.value(),
            existing_links=self.existing_links,
            fetched_data=self.fetched_data,
            next_page_token=self.next_page_token,
            parent=self
        )
        
        # Connect signals
        self.worker_thread.data_fetched_signal.connect(self.on_data_fetched)
        self.worker_thread.update_count_signal.connect(self.on_count_updated)
        self.worker_thread.error_signal.connect(self.on_error)
        self.worker_thread.finished_signal.connect(self.on_fetching_finished)
        
        # Start thread
        self.worker_thread.start()
    
    def on_data_fetched(self, new_records: List[BusinessRecord]):
        """Handle new data from worker thread."""
        # Add records to main list
        self.fetched_data.extend(new_records)
        
        # Update existing links set
        for record in new_records:
            self.existing_links.add(record.gmaps_url)
        
        # Update table
        self.update_table_with_records(new_records)
        
        # Auto-save to input file if loaded
        if self.input_file_path and new_records:
            try:
                FileHandler.append_to_existing_file(new_records, self.input_file_path)
            except Exception as e:
                print(f"Warning: Could not auto-save to input file: {str(e)}")
    
    def on_count_updated(self, count_text: str):
        """Handle count update from worker thread."""
        self.fetched_count_label.setText(count_text)
    
    def on_error(self, error_message: str):
        """Handle error from worker thread."""
        UIHelper.show_error_message(self, "Fetching Error", error_message)
    
    def on_fetching_finished(self, has_more_data: bool, success: bool):
        """Handle completion of fetching operation."""
        self.is_fetching = False
        
        if success and has_more_data:
            # Update pagination token from worker
            if self.worker_thread:
                self.next_page_token = self.worker_thread.next_page_token
        else:
            self.next_page_token = None
        
        self.update_button_states()
        
        if success:
            count = len(self.fetched_data)
            self.fetched_count_label.setText(f"Fetched: {count}")
            if count > 0:
                UIHelper.show_info_message(self, "Success", 
                                         f"Successfully fetched {count} business listings.")
    
    def update_table_with_records(self, records: List[BusinessRecord]):
        """Update the table widget with new records."""
        current_row_count = self.table_widget.rowCount()
        
        for i, record in enumerate(records):
            row = current_row_count + i
            self.table_widget.insertRow(row)
            
            # Add data to columns
            self.table_widget.setItem(row, 0, QTableWidgetItem(record.name))
            self.table_widget.setItem(row, 1, QTableWidgetItem(record.address))
            self.table_widget.setItem(row, 2, QTableWidgetItem(record.phone))
            self.table_widget.setItem(row, 3, QTableWidgetItem(record.website))
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(record.rating)))
            self.table_widget.setItem(row, 5, QTableWidgetItem(record.gmaps_url))
    
    def load_existing_file(self):
        """Load existing data file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Existing Data File",
            "",
            "All Supported (*.json *.csv *.xlsx *.xls);;JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # Load data
            records, existing_links = FileHandler.load_existing_data(file_path)
            
            # Update application state
            self.input_file_path = file_path
            self.existing_links = existing_links
            
            # Update UI
            filename = os.path.basename(file_path)
            self.file_path_label.setText(filename)
            self.file_path_label.setStyleSheet("color: black; font-style: normal;")
            
            # Show success message
            UIHelper.show_info_message(self, "File Loaded", 
                                     f"Successfully loaded {len(records)} existing records from {filename}")
            
        except Exception as e:
            UIHelper.show_error_message(self, "File Load Error", 
                                      f"Failed to load file: {str(e)}")
    
    def save_as_json(self):
        """Save current data as JSON file."""
        if not self.fetched_data:
            UIHelper.show_warning_message(self, "No Data", "No data to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save as JSON",
            "google_maps_listings.json",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            FileHandler.save_to_json(self.fetched_data, file_path)
            UIHelper.show_info_message(self, "Success", 
                                     f"Successfully saved {len(self.fetched_data)} records to {os.path.basename(file_path)}")
        except Exception as e:
            UIHelper.show_error_message(self, "Save Error", 
                                      f"Failed to save file: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait(3000)  # Wait up to 3 seconds
        
        event.accept()