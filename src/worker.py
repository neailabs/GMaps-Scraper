"""
Worker thread for Google Maps API operations.
"""

import time
import googlemaps
from typing import List, Set, Optional, Any
from PySide6.QtCore import QThread, Signal
from src.models import BusinessRecord, AppConfig


class DataFetcherWorker(QThread):
    """Worker thread for fetching data from Google Maps API."""
    
    # Signal definitions
    data_fetched_signal = Signal(list)  # Emits list of BusinessRecord objects
    update_count_signal = Signal(str)   # Emits current count as string
    error_signal = Signal(str)          # Emits error messages
    finished_signal = Signal(bool, bool)  # Emits (has_more_data, success)
    
    def __init__(self, gmaps_client: googlemaps.Client, query: str, num_records: int, 
                 existing_links: Set[str], fetched_data: List[BusinessRecord], 
                 next_page_token: Optional[str] = None, parent=None):
        """
        Initialize the worker thread.
        
        Args:
            gmaps_client: Initialized Google Maps client
            query: Search query string
            num_records: Number of records to fetch
            existing_links: Set of existing Google Maps links for duplicate prevention
            fetched_data: List of already fetched records
            next_page_token: Token for pagination (optional)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.gmaps_client = gmaps_client
        self.query = query
        self.num_records = num_records
        self.existing_links = existing_links.copy()  # Create a copy to avoid race conditions
        self.fetched_data = fetched_data.copy()  # Create a copy
        self.next_page_token = next_page_token
        self._stop_requested = False
        
    def stop(self):
        """Request the worker to stop gracefully."""
        self._stop_requested = True
        
    def run(self):
        """Main thread execution method."""
        try:
            self._fetch_places_data()
        except Exception as e:
            self.error_signal.emit(f"Unexpected error: {str(e)}")
            self.finished_signal.emit(False, False)
    
    def _fetch_places_data(self):
        """Fetch places data from Google Maps API."""
        try:
            current_count = len(self.fetched_data)
            records_needed = self.num_records - current_count
            
            if records_needed <= 0:
                self.finished_signal.emit(False, True)
                return
            
            # Perform actual Google Maps Places API search
            try:
                if self.next_page_token:
                    # Continue with pagination using places text search
                    time.sleep(AppConfig.PAGINATION_DELAY)
                    # Use getattr to avoid type checking issues
                    places_method = getattr(self.gmaps_client, 'places')
                    search_result = places_method(
                        query=self.query,
                        page_token=self.next_page_token
                    )
                else:
                    # New search using places text search
                    # Use getattr to avoid type checking issues
                    places_method = getattr(self.gmaps_client, 'places')
                    search_result = places_method(
                        query=self.query
                    )
                
                if not search_result or 'results' not in search_result:
                    self.error_signal.emit("No results found for the search query.")
                    self.finished_signal.emit(False, False)
                    return
                
                places = search_result['results']
                
            except Exception as api_error:
                self.error_signal.emit(f"API call failed: {str(api_error)}")
                self.finished_signal.emit(False, False)
                return
            new_records = []
            
            for place in places:
                if self._stop_requested:
                    break
                
                if len(self.fetched_data) + len(new_records) >= self.num_records:
                    break
                
                try:
                    place_id = place.get('place_id')
                    if not place_id:
                        continue
                    
                    # Get detailed place information
                    place_details = self._get_place_details(place_id)
                    if not place_details:
                        continue
                    
                    # Create business record
                    record = BusinessRecord.from_google_place(place_details, place_id)
                    
                    # Check for duplicates
                    if record.gmaps_url in self.existing_links:
                        continue
                    
                    # Add to results
                    new_records.append(record)
                    self.existing_links.add(record.gmaps_url)
                    
                    # Update count
                    total_count = len(self.fetched_data) + len(new_records)
                    self.update_count_signal.emit(f"Fetched: {total_count}")
                    
                except Exception as e:
                    # Log error but continue with other places
                    print(f"Error processing place {place.get('name', 'Unknown')}: {str(e)}")
                    continue
            
            # Emit the new records
            if new_records:
                self.data_fetched_signal.emit(new_records)
                self.fetched_data.extend(new_records)
            
            # Check if we need more data and have pagination token
            has_more_data = False
            if len(self.fetched_data) < self.num_records:
                next_token = search_result.get('next_page_token')
                if next_token:
                    has_more_data = True
                    self.next_page_token = next_token
            
            # Signal completion
            self.finished_signal.emit(has_more_data, True)
            
        except googlemaps.exceptions.ApiError as e:
            self.error_signal.emit(f"Google Maps API Error: {str(e)}")
            self.finished_signal.emit(False, False)
        except Exception as e:
            self.error_signal.emit(f"Error fetching data: {str(e)}")
            self.finished_signal.emit(False, False)
    
    def _get_place_details(self, place_id: str) -> Optional[dict]:
        """
        Get detailed information for a place.
        
        Args:
            place_id: Google Places place ID
            
        Returns:
            Place details dictionary or None if error
        """
        try:
            # Define fields to retrieve from Places API
            # Use only valid field names as per Google Places API documentation
            fields = [
                'name', 'formatted_address', 'formatted_phone_number',
                'website', 'rating', 'place_id', 'user_ratings_total',
                'opening_hours', 'price_level', 'photo', 'type',
                'business_status', 'geometry', 'icon', 'plus_code',
                'vicinity', 'permanently_closed', 'url', 'delivery',
                'takeout', 'dine_in', 'serves_beer', 'serves_wine',
                'serves_breakfast', 'serves_lunch', 'serves_dinner',
                'serves_brunch', 'serves_vegetarian_food', 'reservable',
                'wheelchair_accessible_entrance', 'curbside_pickup'
            ]
            
            # Make actual API call to get place details
            # Use getattr to avoid type checking issues
            place_method = getattr(self.gmaps_client, 'place')
            result = place_method(
                place_id=place_id,
                fields=fields
            )
            
            if result and 'result' in result:
                return result['result']
            
            return None
            
        except googlemaps.exceptions.ApiError as e:
            print(f"API Error getting place details for {place_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error getting place details for {place_id}: {str(e)}")
            return None
