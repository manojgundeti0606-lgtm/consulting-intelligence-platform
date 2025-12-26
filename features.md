# GeM Scraper - Current Features

## 1. Search & Filtering

The application provides robust search capabilities to find specific bids on the GeM portal.

- **Keyword Search**:
  - Allows searching by **Items**, **Ministry**, or **Department**.
  - Automatically switches between "Basic" and "Full Text" search modes based on input.
  
- **Date Filtering (Bid End Date)**:
  - **Quick Select Presets**:
    - `Today`: Bids ending today.
    - `Last 7 Days`: Bids ending in the last week.
    - `Last 30 Days`: Bids ending in the last month.
    - `Last 3 Months`: Bids ending in the last quarter.
  - **Custom Range**:
    - Users can manually select a specific **From Date** and **To Date**.

- **Default Filters** (Internal):
  - **Status**: Automatically filters for `ongoing_bids`.
  - **Sort Order**: Results are sorted by `Bid-End-Date-Oldest`.

## 2. Data Scraping & Display

- **Multi-Page Scraping**: Automatically traverses up to **5 pages** of results to gather comprehensive data.
- **Real-time Feedback**: Displays a spinner while scraping is in progress.
- **Results Table**: Presents data in an interactive table with the following columns:
  - `Bid Number`
  - `Items` (Category Name)
  - `Quantity`
  - `Department` (Ministry + Department Name)
  - `Start Date`
  - `End Date`
  - `Document Link`
- **Result Count**: Shows the total number of bids found.

## 3. Data Export

- **CSV Export**:
  - One-click download of the scraped results.
  - Filename: `gem_bids.csv`.
  - Includes all the fields visible in the results table.

## 4. Document Management

- **Bulk Document Download**:
  - Dedicated button to download **ALL** bid documents (PDFs) for the current search results.
  - **Progress Tracking**: Visual progress bar shows the download status (e.g., "Downloading 1 of 10...").
  - **Local Storage**: Automatically creates a `downloads` folder and saves files there.
  - **Smart Naming**:
    - Extracts the filename from the URL.
    - Sanitizes filenames to remove illegal characters.
    - Appends `.pdf` extension.

## 5. Technical Capabilities

- **Automated CSRF Handling**:
  - Fetches a fresh CSRF token from the GeM portal before every search to ensure authorized requests.
- **Session Management**:
  - Uses a persistent session with browser-like headers (`User-Agent`, `Referer`) to mimic a real user and avoid blocking.
- **Error Handling**:
  - Gracefully handles network errors or missing tokens.
  - Alerts the user if no bids are found or if an API error occurs.
