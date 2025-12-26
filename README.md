# GeM Bid Scraper

A web-based application to scrape bid and tender documents from the [GeM (Government e-Marketplace)](https://bidplus.gem.gov.in/all-bids) website. This tool provides an intuitive Streamlit interface to search, filter, and download bid information and documents.

## Features

- 🔍 **Search Bids**: Search by keywords (items, ministries, departments, etc.)
- 📅 **Date Filtering**: Filter bids by end date with preset options (Today, Last 7 Days, Last 30 Days, Last 3 Months)
- 📊 **Data Export**: Download scraped results as CSV
- 📥 **Document Download**: Bulk download bid documents
- 🎨 **User-Friendly Interface**: Clean, intuitive Streamlit web interface

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone or navigate to the project directory**:

   ```bash
   cd c:\Users\manoj\.gemini\antigravity\scratch\gem_scraper
   ```

2. **Install required dependencies**:

   ```bash
   pip install streamlit pandas requests
   ```

   Or if you have a `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Web Application

1. **Start the Streamlit app**:

   ```bash
   streamlit run app.py
   ```

2. **Access the application**:
   - The app will automatically open in your default browser
   - If not, navigate to: `http://localhost:8501`

3. **Using the interface**:
   - **Sidebar**: Enter search filters
     - **Search Keywords**: Enter items, ministry names, department names, etc.
     - **Date Range**: Select a preset (Today, Last 7 Days, etc.) or choose custom dates
   - **Scrape Bids**: Click the button to fetch bids matching your criteria
   - **View Results**: Results are displayed in a table format
   - **Download CSV**: Export the results to a CSV file
   - **Download Documents**: Bulk download all bid PDFs to the `downloads` folder

### Using the Scraper Module Directly

You can also use the scraper module programmatically in your Python scripts:

```python
from gem_scraper import scrape_bids, download_document

# Scrape bids with filters
bids = scrape_bids(
    keywords="Computer",
    from_date="2025-12-01",
    to_date="2025-12-31",
    max_pages=5
)

# Print results
for bid in bids:
    print(bid['Bid Number'], bid['Items'], bid['Department'])

# Download a specific document
download_document(
    url="https://bidplus.gem.gov.in/showbidDocument/12345",
    save_dir="downloads"
)
```

## Project Structure

```text
gem_scraper/
├── app.py                  # Main Streamlit web application
├── gem_scraper.py          # Core scraping logic and API interaction
├── gem_bids.csv            # Sample output CSV file
├── downloads/              # Directory for downloaded bid documents (created automatically)
├── fetch_page.py           # Utility script to fetch page content
├── test_ministry.py        # Test script for ministry search
├── test_user_search.py     # Test script for user search
└── README.md               # This file
```

## How It Works

1. **CSRF Token Extraction**: The scraper first visits the GeM bids page to extract the CSRF token required for API authentication
2. **API Requests**: Makes POST requests to the `/all-bids-data` endpoint with search filters and pagination
3. **Data Parsing**: Extracts bid details including:
   - Bid Number
   - Items/Categories
   - Quantity
   - Department and Ministry
   - Start and End Dates
   - Document Links
4. **Document Download**: Fetches PDF documents for each bid

## Configuration

You can modify the following parameters in `gem_scraper.py`:

- `BASE_URL`: Base URL of the GeM website (default: `https://bidplus.gem.gov.in`)
- `max_pages`: Maximum number of pages to scrape (default: 5 in the function parameter)

## Troubleshooting

### Common Issues

1. **No CSRF token found**:
   - The website structure may have changed
   - Check your internet connection
   - Verify that the website is accessible

2. **No bids found**:
   - Try broader search terms
   - Remove date filters
   - Check if the website has any data for your search criteria

3. **Download errors**:
   - Ensure you have write permissions in the download directory
   - Check your internet connection
   - Some bid documents may not be publicly accessible

### Tips

- Start with a broad search (no keywords, no date filter) to verify the scraper is working
- Use date presets for quick filtering
- The scraper adds a 1-second delay between page requests to avoid overwhelming the server

## Legal Notice

This tool is for educational and research purposes only. Please respect the GeM website's terms of service and use this tool responsibly. Do not overload the server with excessive requests.

## Dependencies

- **streamlit**: Web application framework
- **pandas**: Data manipulation and CSV export
- **requests**: HTTP library for API calls
- **re**: Regular expressions for parsing
- **json**: JSON data handling
- **csv**: CSV file operations (built-in)
- **datetime**: Date and time operations (built-in)
- **os**: File system operations (built-in)

## Support

If you encounter any issues or have questions, please check the troubleshooting section above or review the code comments in `gem_scraper.py` and `app.py`.

---

**Last Updated**: December 2025
