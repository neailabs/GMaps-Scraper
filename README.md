# Google Maps Listings Scraper

A desktop GUI application built with PySide6 that fetches business listings from Google Maps using the Google Maps Places API. The application provides a user-friendly interface for searching, fetching, displaying, and saving business data with support for pagination and data persistence.

## Features

- **User-Friendly GUI**: Clean, intuitive interface built with PySide6
- **Google Maps Integration**: Uses Google Maps Places API for accurate business data
- **Asynchronous Operations**: Non-blocking UI with threaded API calls
- **Data Persistence**: Support for JSON, CSV, and Excel file formats
- **Duplicate Prevention**: Automatic deduplication based on Google Maps place IDs
- **Pagination Support**: Continue fetching additional results
- **File Management**: Load existing data files and auto-append new results
- **Export Options**: Save results in multiple formats

## Requirements

- Python 3.8 or higher
- Google Maps API key with Places API enabled
- Required Python packages (see requirements.txt)

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Google Maps API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Maps Places API
4. Create an API key
5. (Optional, but RECOMMENDED) Restrict the API key to the Places API for security

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Enter your Google Maps API key in the API Key field

3. Enter a search query (e.g., "restaurants in New York", "hotels in Paris")

4. Set the number of listings you want to fetch (1-100)

5. Click "Fetch Data" to start scraping

6. Use "Continue Fetching" to get more results if available

7. Save your results using "Save as JSON" or load existing files with "Load File"

## Application Interface

### Input Panel
- **API Key**: Your Google Maps API key (hidden for security)
- **Search Query**: What you want to search for
- **Number of Listings**: How many results to fetch (1-100)
- **Fetched Count**: Real-time counter of fetched results
- **Continue Fetching**: Checkbox to enable pagination
- **Existing Data File**: Load and append to existing data files

### Data Table
Displays fetched business information in columns:
- Name
- Address
- Phone Number
- Website
- Rating
- Google Maps Link

### Action Buttons
- **Fetch Data**: Start a new search
- **Continue Fetching**: Get more results (if available)
- **Save as JSON**: Export current data to JSON file

## Data Format

Each business record contains:
```json
{
  "UUID": "unique-identifier",
  "Name": "Business Name",
  "Phone Number": "+1 (555) 123-4567",
  "Address": "123 Main St, City, State 12345",
  "GMaps URL": "https://www.google.com/maps/place/?q=place_id:...",
  "Website": "https://example.com",
  "Rating": 4.5
}
```

## File Support

### Input Formats
- JSON (.json)
- CSV (.csv)
- Excel (.xlsx, .xls)

### Output Formats
- JSON (.json)
- Excel (.xlsx)
- CSV (.csv)

## Technical Architecture

### Core Components
- **GmapsCrawler**: Main application window (QMainWindow)
- **DataFetcherWorker**: QThread-based worker for asynchronous API operations
- **BusinessRecord**: Data model for business listings
- **FileHandler**: Utility class for file operations
- **UIHelper**: UI utility functions

### Threading Model
- **Main Thread**: GUI operations and user interaction
- **Worker Thread**: API calls and data processing
- **Signal-Slot Communication**: Thread-safe communication between worker and UI

## Error Handling

The application includes comprehensive error handling for:
- Invalid API keys
- Network connectivity issues
- API rate limiting
- File I/O errors
- Malformed data

## Development Notes

### Current Implementation
The current version is fully functional and works ootb.

### API Integration
The application is structured to work with the Google Maps Places API. The main methods needed are:
- Text search for finding places
- Place details for getting comprehensive information
- Pagination support for large result sets

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure your API key is valid
   - Check that Places API is enabled
   - Verify API key restrictions

2. **No Results Found**
   - Try different search queries
   - Check your internet connection
   - Verify API quotas

3. **File Loading Issues**
   - Ensure file format is supported
   - Check file permissions
   - Verify file structure matches expected format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided under the MIT license, details of which are available in the LICENSE.txt file.

## Credits

Created by **NE AI Innovation Labs**
Website: [https://www.neailabs.com](https://www.neailabs.com)

## Support

For issues and questions, please refer to the application's error messages and this documentation.
