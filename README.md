# Hotel Scrapers - TUI Spain Hotel Price Scraper

A powerful web scraper for extracting hotel pricing and travel information from TUI.nl's Spain (Formentera) travel packages.

## Overview

This project automates the collection of hotel data from TUI Netherlands, including:
- Hotel information (name, stars, accommodation type)
- Room details and meal plans
- Flight information (departure/arrival times, airlines)
- Pricing data (per person, tourist taxes)
- Travel duration and departure dates
- Multiple departure airports and travel dates

## Features

- 🏨 **Hotel Data Extraction**: Scrapes hotel names, star ratings, and accommodation types
- ✈️ **Flight Details**: Captures departure/arrival times, airlines, and airports
- 💰 **Price Information**: Extracts pricing data across multiple departure dates and airports
- 🔄 **Cookie-Based Sessions**: Uses Camoufox browser automation to maintain authenticated sessions
- 📊 **Structured Output**: Exports data to JSON format
- 🛡️ **Anti-Detection**: Implements browser impersonation to bypass detection
- 📝 **Logging**: Comprehensive logging for debugging and monitoring

## Installation

### Prerequisites
- Python 3.11.1
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/naufalsyqit/spanje_hotel_scraper.git
cd hotel_scrapers
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate      # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. install Camoufox browser:
```
camoufox install
```

### Dependencies

The project uses the following libraries:

- **`curl_cffi`**: HTTP requests library with browser impersonation support
- **`BeautifulSoup`**: HTML parsing and web scraping
- **`Camoufox`**: Browser automation (headless Firefox with anti-bot detection)

## Usage

### Basic Usage

```python
from main import Collector

# Create a collector instance
collector = Collector()

# Set number of months to scrape (0 for all)
collector.month_count = 2

# Run the pipeline
hotel_data = collector.run_pipeline()
```

### Command Line

```bash
python main.py
```

This will scrape the first 3 hotels and save the data to `output/final_hotel_data_X_months.json`.

### Configuration

Edit the `Collector` class parameters:

```python
collector = Collector(month_count=2)  # Scrape only 2 months of data
```

- `month_count=0`: Scrapes all available months (default)
- `month_count=2`: Scrapes only the first 2 months

## Project Structure

```
hotel_scrapers/
├── main.py                 # Main runner
├── pipeline/               # Store pipeline scripts
|   └── crawl.py            # Hotel crawler pipeline
├── extractor/
│   └── hotel_extractor.py  # Hotel data extraction functions
├── helpers/
│   └── general_utils.py    # Utility functions (HTML decoding, etc.)
├── output/
│   ├── raw_json/           # Raw JSON responses (if debugging line is on)
│   ├── raw_html/           # HTML pages (if debugging line is on)
│   └── txt_output/         # Text outputs (if debugging line is on)
└── README.md
```

## How It Works

1. **Hotel Discovery**: Fetches the list of hotels from TUI's Formentera page
2. **Session Management**: Uses Camoufox to obtain authenticated cookies
3. **Price Grid Retrieval**: Fetches price grids for different departure airports and dates
4. **Data Extraction**: Parses HTML to extract prices, flight info, and hotel details
5. **Price Details**: Gets detailed pricing information including taxes and breakdowns
6. **Data Export**: Saves structured data to JSON format

## API Endpoints Used

- `https://www.tui.nl/reizen/spanje/formentera/` - Hotel listing page
- `https://www.tui.nl/data/pricegrid/changepref/` - Price grid API
- `https://www.tui.nl/data/pricegrid/priceselect/` - Price details API

## Output Format

The scraper exports data in the following JSON structure:

```json
[
  {
    "hotel_url": "https://www.tui.nl/reizen/spanje/formentera/...",
    "hotel_name": "Example Hotel",
    "hotel_stars": "4",
    "accomodation_type": "Hotel",
    "room_name": "Double Room",
    "meal_plan": "All Inclusive",
    "duration": "7 days / 6 nights",
    "departure_airport": "AMS",
    "departure_month": "June 2026",
    "departure_date": "2026-06-01",
    "return_date": "2026-06-07",
    "flight_departure_time": "10:30",
    "flight_arrival_time": "14:45",
    "flight_airline": "TUI fly",
    "final_price_per_person": "€1,299",
    "tourist_tax": "50",
    "currency": "€"
  }
]
```

## Key Functions

### `Collector.run_pipeline()`
Main pipeline that orchestrates the scraping process.

### `get_hotel_cookies(hotel_link)`
Uses Camoufox to retrieve session cookies and page content.

### `get_hotel_basic_info(soup)`
Extracts hotel name and star rating from parsed HTML.

### `get_hotel_price_grid(url, cookies, payload, session)`
Fetches price grid data for a specific hotel, departure date, and airport.

### `get_trip_options(price_details_json)`
Extracts trip details (flights, pricing, dates) from API response.

## Logging

The scraper uses Python's `logging` module. Logs are printed to console with timestamps and severity levels:

```
2025-12-06 10:30:45,123 - INFO - Processing hotel: example-hotel, Departure: AMS, Date: June 1-7
2025-12-06 10:30:50,456 - INFO - Hotel: example-hotel, Departure: AMS, Lowest Price: €1,299
```

## Error Handling

The scraper includes error handling for:
- Missing HTML elements
- API failures
- Network timeouts
- Invalid data formats

Failed requests are logged and the pipeline continues processing other hotels.

## Performance Tips

1. **Reduce Month Count**: Set `month_count` to a smaller value to speed up scraping
2. **Limit Hotels**: Modify `hotel_links[:count]` to scrape fewer hotels
3. **Parallel Processing**: Consider using ThreadPoolExecutor for faster scraping

## Limitations

- Currently scrapes only the Formentera destination (if flows are completely the same, it'll just need a modification on the url)
- Requires active internet connection
- TUI may have rate limiting - add delays if needed
- Website structure changes may break the scraper
- all using 2 person options
- Meal plan kept greyed out to select
- not every line of code exception are excepted due to possible misleading blocker

## Future Enhancements

- [ ] Support for multiple destinations
- [ ] Database storage option
- [ ] Async/await implementation for camoufox cookies collector

## Disclaimer

This scraper is for educational purposes only. Ensure you comply with TUI's Terms of Service and robots.txt before using this tool. Web scraping may violate website terms of service or local laws.

## License

MIT License - See LICENSE file for details

## Author

Naufal Syqit - [GitHub](https://github.com/naufalsyqit)

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/naufalsyqit/spanje_hotel_scraper).
