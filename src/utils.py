"""
Utility functions for the Google Maps Listings Scraper.
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Set, Optional, Tuple
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import Qt
from src.models import BusinessRecord


class FileHandler:
    """Handles file operations for various formats."""
    
    @staticmethod
    def load_existing_data(file_path: str) -> Tuple[List[BusinessRecord], Set[str]]:
        """
        Load existing data from a file and return records and existing links.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            Tuple of (records_list, existing_links_set)
        """
        records = []
        existing_links = set()
        
        if not os.path.exists(file_path):
            return records, existing_links
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            record = BusinessRecord.from_dict(item)
                            records.append(record)
                            if record.gmaps_url:
                                existing_links.add(record.gmaps_url)
            
            elif file_ext in ['.csv', '.xlsx', '.xls']:
                if file_ext == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                for _, row in df.iterrows():
                    record_data = {
                        "UUID": row.get("UUID", ""),
                        "Name": row.get("Name", ""),
                        "Phone Number": row.get("Phone Number", ""),
                        "Address": row.get("Address", ""),
                        "GMaps URL": row.get("GMaps URL", ""),
                        "Website": row.get("Website", ""),
                        "Rating": row.get("Rating", "NA")
                    }
                    record = BusinessRecord.from_dict(record_data)
                    records.append(record)
                    if record.gmaps_url:
                        existing_links.add(record.gmaps_url)
            
        except Exception as e:
            raise Exception(f"Error loading file {file_path}: {str(e)}")
        
        return records, existing_links
    
    @staticmethod
    def save_to_json(records: List[BusinessRecord], file_path: str) -> None:
        """Save records to JSON file."""
        try:
            data = [record.to_dict() for record in records]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error saving to JSON: {str(e)}")
    
    @staticmethod
    def save_to_excel(records: List[BusinessRecord], file_path: str) -> None:
        """Save records to Excel file."""
        try:
            data = [record.to_dict() for record in records]
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
        except Exception as e:
            raise Exception(f"Error saving to Excel: {str(e)}")
    
    @staticmethod
    def save_to_csv(records: List[BusinessRecord], file_path: str) -> None:
        """Save records to CSV file."""
        try:
            data = [record.to_dict() for record in records]
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
        except Exception as e:
            raise Exception(f"Error saving to CSV: {str(e)}")
    
    @staticmethod
    def append_to_existing_file(records: List[BusinessRecord], file_path: str) -> None:
        """Append new records to existing file, maintaining format."""
        if not os.path.exists(file_path):
            return
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                # Load existing data
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                # Append new records
                new_data = [record.to_dict() for record in records]
                if isinstance(existing_data, list):
                    existing_data.extend(new_data)
                else:
                    existing_data = new_data
                
                # Save back
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            elif file_ext in ['.csv', '.xlsx', '.xls']:
                # Load existing data
                if file_ext == '.csv':
                    existing_df = pd.read_csv(file_path)
                else:
                    existing_df = pd.read_excel(file_path)
                
                # Create new data frame
                new_data = [record.to_dict() for record in records]
                new_df = pd.DataFrame(new_data)
                
                # Combine and save
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                if file_ext == '.csv':
                    combined_df.to_csv(file_path, index=False)
                else:
                    combined_df.to_excel(file_path, index=False)
                    
        except Exception as e:
            raise Exception(f"Error appending to file: {str(e)}")


class UIHelper:
    """Helper functions for UI operations."""
    
    @staticmethod
    def show_error_message(parent: QWidget, title: str, message: str) -> None:
        """Show error message dialog."""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    @staticmethod
    def show_info_message(parent: QWidget, title: str, message: str) -> None:
        """Show information message dialog."""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    @staticmethod
    def show_warning_message(parent: QWidget, title: str, message: str) -> None:
        """Show warning message dialog."""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    @staticmethod
    def confirm_action(parent: QWidget, title: str, message: str) -> bool:
        """Show confirmation dialog and return user's choice."""
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes


def validate_api_key(api_key: str) -> bool:
    """Validate Google Maps API key format."""
    if not api_key or len(api_key.strip()) == 0:
        return False
    
    # Basic format validation - Google API keys are typically 39 characters
    api_key = api_key.strip()
    if len(api_key) < 20:  # Minimum reasonable length
        return False
    
    # Should contain only alphanumeric characters, hyphens, and underscores
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in api_key):
        return False
    
    return True


def validate_search_query(query: str) -> bool:
    """Validate search query."""
    if not query or len(query.strip()) == 0:
        return False
    
    # Should have at least 2 characters
    if len(query.strip()) < 2:
        return False
    
    return True
