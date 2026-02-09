"""Test Selenium-based download with better waiting and debugging"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob

def download_with_selenium(url, download_dir="downloads_test"):
    """Download document using headless Chrome"""
    
    # Create download directory
    abs_download = os.path.abspath(download_dir)
    os.makedirs(abs_download, exist_ok=True)
    
    # Setup Chrome options - NOT headless to see what happens
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Disable headless to debug
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Configure download directory
    prefs = {
        "download.default_directory": abs_download,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # Auto-download PDFs
        "safebrowsing.enabled": False,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        print(f"Starting Chrome driver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait longer and check periodically
        max_wait = 15
        for i in range(max_wait):
            time.sleep(1)
            print(f"Waiting... {i+1}/{max_wait}s")
            
            # Check for new PDF files
            pdfs = glob.glob(os.path.join(abs_download, "*.pdf"))
            for pdf in pdfs:
                size = os.path.getsize(pdf)
                print(f"  Found: {os.path.basename(pdf)} ({size} bytes)")
                if size > 1000:
                    print("✅ Download complete!")
                    driver.quit()
                    return pdf
        
        # Check page state
        print(f"\nFinal URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Take screenshot for debugging
        driver.save_screenshot("debug_screenshot.png")
        print("Saved screenshot: debug_screenshot.png")
        
        driver.quit()
        
        # List all files
        files = os.listdir(abs_download)
        print(f"\nFiles in download dir: {files}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with a bid document URL
    test_url = "https://bidplus.gem.gov.in/showbidDocument/GEM2026R613731"
    download_with_selenium(test_url)
