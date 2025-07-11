"""
Data models and structures for the Google Maps Listings Scraper.
"""

import uuid
from typing import Dict, Any, Optional, List


class BusinessRecord:
    """Represents a business listing record."""
    
    def __init__(self, name: str = "", phone: str = "", address: str = "", 
                 gmaps_url: str = "", website: str = "", rating: Any = "NA",
                 business_hours: str = "", price_range: str = "", 
                 rating_count: int = 0, photos_count: int = 0,
                 amenities: Optional[List[str]] = None, social_media: Optional[Dict[str, str]] = None,
                 delivery_options: Optional[List[str]] = None, business_type: str = ""):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.phone = phone
        self.address = address
        self.gmaps_url = gmaps_url
        self.website = website
        self.rating = rating
        self.business_hours = business_hours
        self.price_range = price_range
        self.rating_count = rating_count
        self.photos_count = photos_count
        self.amenities = amenities or []
        self.social_media = social_media or {}
        self.delivery_options = delivery_options or []
        self.business_type = business_type
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary."""
        return {
            "UUID": self.uuid,
            "Name": self.name,
            "Phone Number": self.phone,
            "Address": self.address,
            "GMaps URL": self.gmaps_url,
            "Website": self.website,
            "Rating": self.rating,
            "Business Hours": self.business_hours,
            "Price Range": self.price_range,
            "Rating Count": self.rating_count,
            "Photos Count": self.photos_count,
            "Amenities": ", ".join(self.amenities) if self.amenities else "",
            "Social Media": ", ".join([f"{k}: {v}" for k, v in self.social_media.items()]) if self.social_media else "",
            "Delivery Options": ", ".join(self.delivery_options) if self.delivery_options else "",
            "Business Type": self.business_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessRecord':
        """Create a BusinessRecord from a dictionary."""
                # Parse amenities from string
        amenities_str = data.get("Amenities", "")
        amenities = [a.strip() for a in amenities_str.split(",") if a.strip()] if amenities_str else []
        
        # Parse social media from string
        social_media = {}
        social_str = data.get("Social Media", "")
        if social_str:
            for item in social_str.split(","):
                if ":" in item:
                    key, value = item.split(":", 1)
                    social_media[key.strip()] = value.strip()
        
        # Parse delivery options from string
        delivery_str = data.get("Delivery Options", "")
        delivery_options = [d.strip() for d in delivery_str.split(",") if d.strip()] if delivery_str else []
        record = cls(
            name=data.get("Name", ""),
            phone=data.get("Phone Number", ""),
            address=data.get("Address", ""),
            gmaps_url=data.get("GMaps URL", ""),
            website=data.get("Website", ""),
            rating=data.get("Rating", "NA"),
            business_hours=data.get("Business Hours", ""),
            price_range=data.get("Price Range", ""),
            rating_count=data.get("Rating Count", 0),
            photos_count=data.get("Photos Count", 0),
            amenities=amenities,
            social_media=social_media,
            delivery_options=delivery_options,
            business_type=data.get("Business Type", "")
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
        
        business_hours = cls._extract_business_hours(place_details)
        price_range = cls._extract_price_range(place_details)
        rating_count = place_details.get('user_ratings_total', 0)
        photos_count = len(place_details.get('photo', []))
        amenities = cls._extract_amenities(place_details)
        social_media = cls._extract_social_media(place_details)
        delivery_options = cls._extract_delivery_options(place_details)
        business_type = cls._extract_business_type(place_details)
        
        return cls(
            name=name,
            phone=phone,
            address=address,
            gmaps_url=gmaps_url,
            website=website,
            rating=rating,
            business_hours=business_hours,
            price_range=price_range,
            rating_count=rating_count,
            photos_count=photos_count,
            amenities=amenities,
            social_media=social_media,
            delivery_options=delivery_options,
            business_type=business_type
        )

    @staticmethod
    def _extract_business_hours(place_details: Dict[str, Any]) -> str:
        """Extract business hours from place details."""
        opening_hours = place_details.get('opening_hours', {})
        if opening_hours and 'weekday_text' in opening_hours:
            return "; ".join(opening_hours['weekday_text'])
        return ""
    
    @staticmethod
    def _extract_price_range(place_details: Dict[str, Any]) -> str:
        """Extract price range from place details."""
        price_level = place_details.get('price_level')
        if price_level is not None:
            price_map = {0: "Free", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
            return price_map.get(price_level, "")
        return ""
    
    @staticmethod
    def _extract_amenities(place_details: Dict[str, Any]) -> List[str]:
        """Extract amenities from place details."""
        amenities = []
        
        # Check for common amenities in types (fallback)
        types = place_details.get('type', [])  # Note: API returns 'type' as array
        
        # Check for individual amenity fields from the API
        amenity_fields = {
            'wheelchair_accessible_entrance': 'Wheelchair Accessible',
            'serves_beer': 'Serves Beer',
            'serves_wine': 'Serves Wine',
            'serves_breakfast': 'Serves Breakfast',
            'serves_lunch': 'Serves Lunch',
            'serves_dinner': 'Serves Dinner',
            'serves_brunch': 'Serves Brunch',
            'serves_vegetarian_food': 'Serves Vegetarian Food',
            'reservable': 'Reservations',
            'curbside_pickup': 'Curbside Pickup'
        }
        
        # Check individual amenity fields
        for field_key, amenity_name in amenity_fields.items():
            if place_details.get(field_key) is True:
                amenities.append(amenity_name)
        
        # Fallback: check types for basic amenities
        type_amenity_mapping = {
            'meal_delivery': 'Delivery Available',
            'meal_takeaway': 'Takeout Available'
        }
        
        for type_key, amenity_name in type_amenity_mapping.items():
            if type_key in types:
                amenities.append(amenity_name)
        
        return amenities
    
    @staticmethod
    def _extract_social_media(place_details: Dict[str, Any]) -> Dict[str, str]:
        """Extract social media links from place details."""
        # Google Places API doesn't directly provide social media
        # This would need to be extracted from website or other sources
        return {}
    
    @staticmethod
    def _extract_delivery_options(place_details: Dict[str, Any]) -> List[str]:
        """Extract delivery options from place details."""
        options = []
        
        # Check individual delivery option fields from the API
        if place_details.get('delivery') is True:
            options.append('Delivery')
        if place_details.get('takeout') is True:
            options.append('Takeout')
        if place_details.get('dine_in') is True:
            options.append('Dine-in')
        if place_details.get('curbside_pickup') is True:
            options.append('Curbside Pickup')
        
        # Fallback: check types for basic delivery options
        types = place_details.get('type', [])  # Note: API returns 'type' as array
        
        if 'meal_delivery' in types and 'Delivery' not in options:
            options.append('Delivery')
        if 'meal_takeaway' in types and 'Takeout' not in options:
            options.append('Takeout')
        if 'restaurant' in types and 'Dine-in' not in options:
            options.append('Dine-in')
        
        return options
    
    @staticmethod
    def _extract_business_type(place_details: Dict[str, Any]) -> str:
        """Extract business type from place details."""
        types = place_details.get('type', [])  # Note: API returns 'type' as array
        
        # Priority mapping for business types
        type_mapping = {
            'restaurant': 'Restaurant',
            'food': 'Restaurant',
            'store': 'Retail Store',
            'hospital': 'Healthcare',
            'doctor': 'Healthcare',
            'bank': 'Financial Services',
            'gas_station': 'Gas Station',
            'hotel': 'Hotel',
            'tourist_attraction': 'Tourist Attraction',
            'gym': 'Fitness',
            'beauty_salon': 'Beauty & Wellness',
            'car_repair': 'Automotive',
            'school': 'Education',
            'church': 'Religious',
            'pharmacy': 'Pharmacy',
            'supermarket': 'Grocery Store'
        }
        
        for google_type in types:
            if google_type in type_mapping:
                return type_mapping[google_type]
        
        # Return first type if no mapping found
        return types[0].replace('_', ' ').title() if types else ""
    
class AppConfig:
    """Application configuration constants."""
        
    # Window settings
    WINDOW_TITLE = "Get Listings from Google Maps"
    ICON_PATH = "./res/company_icon.ico"
    
    # UI settings
    INPUT_FIELD_WIDTH = 300
    SPINBOX_MIN = 1
    SPINBOX_MAX = 60
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
    APPLICATION_URL = "https://github.com/neailabs/GMaps-Scraper/"
    
    # API settings
    PAGINATION_DELAY = 2.0  # seconds
    MAX_RECORDS_PER_REQUEST = 100
    
    # Table columns
    TABLE_COLUMNS = ["Name", "Address", "Phone", "Website", "Rating", "Rating Count",
        "Business Hours", "Price Range", "Photos Count", "Business Type",
        "Amenities", "Delivery Options", "Google Map Link"
    ]
