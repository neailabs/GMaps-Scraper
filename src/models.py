"""
Data models and structures for the Google Maps Listings Scraper.
"""

import uuid
from typing import Dict, Any, Optional


class BusinessRecord:
    """Represents a business listing record."""
    
    def __init__(self, name: str = "", phone: str = "", address: str = "", 
                 gmaps_url: str = "", website: str = "", rating: Any = "NA"):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.phone = phone
        self.address = address
        self.gmaps_url = gmaps_url
        self.website = website
        self.rating = rating
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary."""
        return {
            "UUID": self.uuid,
            "Name": self.name,
            "Phone Number": self.phone,
            "Address": self.address,
            "GMaps URL": self.gmaps_url,
            "Website": self.website,
            "Rating": self.rating
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessRecord':
        """Create a BusinessRecord from a dictionary."""
        record = cls(
            name=data.get("Name", ""),
            phone=data.get("Phone Number", ""),
            address=data.get("Address", ""),
            gmaps_url=data.get("GMaps URL", ""),
            website=data.get("Website", ""),
            rating=data.get("Rating", "NA")
        )
        # Use existing UUID if available
        if "UUID" in data:
            record.uuid = data["UUID"]
        return record
    
    @classmethod
    def from_google_place(cls, place_details: Dict[str, Any], place_id: str) -> 'BusinessRecord':
        """Create a BusinessRecord from Google Places API response."""
        name = place_details.get('name', '')
        phone = place_details.get('formatted_phone_number', '')
        address = place_details.get('formatted_address', '')
        website = place_details.get('website', '')
        rating = place_details.get('rating', 'NA')
        
        # Generate Google Maps URL with place_id
        gmaps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        
        return cls(
            name=name,
            phone=phone,
            address=address,
            gmaps_url=gmaps_url,
            website=website,
            rating=rating
        )


class AppConfig:
    """Application configuration constants."""
    
    # Window settings
    WINDOW_TITLE = "Get Listings from Google Maps"
    ICON_PATH = "./res/company_icon.ico"
    
    # UI settings
    INPUT_FIELD_WIDTH = 300
    SPINBOX_MIN = 1
    SPINBOX_MAX = 100
    DEFAULT_RECORD_COUNT = 10
    
    # Colors
    BRAND_COLOR = "#EF275D"
    ACCENT_COLOR = "#2FC0F2"
    
    # Company info
    COMPANY_NAME = "NE AI Innovation Labs"
    COMPANY_URL = "https://www.neailabs.com"
    
    # Application info
    MENU_DISPLAY_NAME = "Gmaps Scraper"
    MENU_DESCRIPTION = "A simple app to scrape Google Maps listings."
    MENU_ICON = "./res/app_icon.ico"
    VERSION = "1.0.6"
    APPLICATION_URL = "https://github.com/neailabs/GMaps-Scraper/"
    
    # API settings
    PAGINATION_DELAY = 2.0  # seconds
    MAX_RECORDS_PER_REQUEST = 100
    
    # Table columns
    TABLE_COLUMNS = ["Name", "Address", "Phone", "Website", "Rating", "Google Map Link"]
