"""Test downloading Goa Shipyard PDF with Selenium"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import io
from PyPDF2 import PdfReader
import requests

def extract_pdf_title_selenium(pdf_url: str) -> str:
    """Download PDF using Selenium and extract title."""
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Enable PDF download
    options.add_experimental_option("prefs", {
        "plugins.always_open_pdf_externally": True,
        "download.default_directory": ".",
        "download.prompt_for_download": False,
    })
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # First visit tender page
        print("Visiting tender page...")
        driver.get("https://goashipyard.in/tender/Tenders")
        time.sleep(3)
        
        print(f"Page title: {driver.title}")
        
        # Find PDF links and get their actual hrefs
        pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
        print(f"Found {len(pdf_links)} PDF links")
        
        if pdf_links:
            for i, link in enumerate(pdf_links[:3]):
                href = link.get_attribute("href")
                text = link.text.strip()
                parent_text = link.find_element(By.XPATH, "..").text.strip()[:80]
                print(f"  {i+1}: {href}")
                print(f"      Text: {text[:50] if text else 'No text'}")
                print(f"      Parent: {parent_text}")
        
        # Try clicking a PDF link
        if pdf_links:
            first_pdf = pdf_links[0]
            print(f"\nClicking on first PDF link...")
            first_pdf.click()
            time.sleep(3)
            
            # Check if we navigated to PDF or opened in new tab
            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    extract_pdf_title_selenium("")
