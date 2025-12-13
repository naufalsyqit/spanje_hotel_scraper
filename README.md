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
- ⚡ **Multithreading**: Concurrent processing with ThreadPoolExecutor (10 hotels + 5 price options per thread)
- 🔁 **Pagination Support**: Automatically navigates through multiple price pages

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

1. **Hotel Discovery**: Fetches the list of hotels from TUI's Formentera page using curl_cffi
2. **Session Management**: Uses new cffi requests session to obtain authenticated cookies
3. **Price Grid Retrieval**: Fetches price grids for different departure airports and dates
4. **Pagination**: Automatically navigates through multiple price pages using the grid navigation API
5. **Price Extraction**: Parses HTML to extract all price options for each date/airport combination
6. **Multithreaded Processing**: Processes multiple price options concurrently (5 threads)
7. **Price Details**: Gets detailed pricing information including taxes, flight details, and room info
8. **Data Export**: Saves structured data to JSON format with timestamp

## API Endpoints Used

- `https://www.tui.nl/reizen/spanje/formentera/` - Hotel listing page
- `https://www.tui.nl/data/pricegrid/changepref/` - Price grid preference change API
- `https://www.tui.nl/data/pricegrid/priceselect/` - Price details selection API
- `https://www.tui.nl/data/pricegrid/gridnavigation/` - Price grid pagination API

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
Main pipeline orchestrator that manages the entire scraping workflow with multithreading support.

### `Crawl.crawl_hotels(hotel_link)`
Processes a single hotel, handling all date/airport combinations and pagination.

### `Crawl.process_price_option(price_option, ...)`
Processes individual price options concurrently (multithreaded).

### `get_hotel_cookies(hotel_link)`
Uses Camoufox to retrieve session cookies and initial page content.

### `get_hotel_cookies_alt(hotel_link)`
Uses clean cffi requests session to retrieve session cookies and initial page content.

### `get_hotel_basic_info(soup)`
Extracts hotel name and star rating from parsed HTML.

### `get_hotel_price_grid(url, cookies, payload, session)`
Fetches price grid data for a specific hotel, departure date, and airport.

### `get_trip_options(price_details_json)`
Extracts trip details (flights, pricing, dates) from API response JSON.

### `decode_and_soup(html_string)`
Decodes escaped HTML and returns BeautifulSoup object for parsing.

## Logging

The scraper uses Python's `logging` module with detailed output. Logs are printed to console with timestamps and severity levels:

```
2025-12-06 10:30:45,123 [INFO] main.py:45 - Processing hotel: example-hotel, Departure: AMS, Date: June 1-7
2025-12-06 10:30:50,456 [INFO] crawl.py:125 - Hotel: example-hotel, Departure: AMS, Lowest Price: €1,299
2025-12-06 10:30:55,789 [ERROR] crawl.py:150 - Error processing price option: Connection timeout
```

**Log levels:**
- `INFO` - Normal operation flow
- `ERROR` - Errors in processing (logged but doesn't stop execution)
- `WARNING` - Potential issues (e.g., empty responses)

## Error Handling

The scraper includes robust error handling for:
- Missing HTML elements (gracefully skips and logs)
- API failures and empty responses (caught and logged)
- Network timeouts (retries or skips hotel)
- Invalid data formats (uses try-except blocks)
- Empty pagination pages (breaks loop automatically)
- Failed price option processing (logs error, continues with next option)

Failed requests are logged with detailed error messages and the pipeline continues processing other hotels or price options.

## Performance Tips

1. **Reduce Month Count**: Set `month_count` to a smaller value to speed up scraping
2. **Adjust Thread Workers**: Modify `max_workers` in main.py for hotel processing (default: 10)
3. **Adjust Price Option Threads**: Modify `max_workers=5` in crawl.py for price option processing
4. **Rate Limiting**: Add delays between requests to avoid server blocking
5. **Limit Hotels**: Modify hotel_links slice to scrape fewer hotels for testing

## Limitations

- Currently scrapes only the Formentera destination (easily adaptable to other destinations)
- Requires active internet connection
- TUI may have rate limiting - add delays if needed
- Website structure changes may break the scraper
- All prices based on 2 person options
- Meal plan kept greyed out to select (limitation of website)
- Not all code branches have exception handling due to possible misleading blockers
- Headless browser automation may be slower than pure HTTP requests
- Some price details may not be available for all hotels/dates

## Future Enhancements

- [ ] Support for multiple destinations
- [ ] Database storage option (MongoDB/PostgreSQL)
- [ ] Async/await implementation for faster Camoufox cookie collection
- [ ] Proxy rotation support for large-scale scraping
- [ ] Email notifications for price drops
- [ ] Scheduled scraping with cron jobs
- [ ] Web dashboard for monitoring scraping progress
- [ ] Price comparison and analysis features

## Disclaimer

This scraper is for educational purposes only. Ensure you comply with TUI's Terms of Service and robots.txt before using this tool. Web scraping may violate website terms of service or local laws.

## License

MIT License - See LICENSE file for details

## Author

Naufal Syqit - [GitHub](https://github.com/naufalsyqit)

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/naufalsyqit/spanje_hotel_scraper).
