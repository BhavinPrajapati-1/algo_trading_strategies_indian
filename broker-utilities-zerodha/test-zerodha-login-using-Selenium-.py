# zerodha_auto_login.py
import os
import time
import pyotp
import requests
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WEBDRIVER_MANAGER = True
except ImportError:
    USE_WEBDRIVER_MANAGER = False

load_dotenv()

# Credentials
API_KEY = os.getenv("ZERODHA_API_KEY")
API_SECRET = os.getenv("ZERODHA_API_SECRET")
USER_ID = os.getenv("ZERODHA_USER_ID")
PASSWORD = os.getenv("ZERODHA_PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

def generate_access_token():
    """Generate Kite Connect access token using Selenium automation"""
    
    print("🚀 Starting Zerodha Auto-Login...")
    
    # Initialize Kite Connect
    kite = KiteConnect(api_key=API_KEY)
    login_url = kite.login_url()
    print(f"📌 Login URL: {login_url}")
    
    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Initialize driver
    if USE_WEBDRIVER_MANAGER:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Step 1: Open login URL
        print("📌 Opening Zerodha login page...")
        driver.get(login_url)
        time.sleep(3)
        
        # Step 2: Enter User ID
        print("📌 Entering User ID...")
        user_id_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
        )
        user_id_field.clear()
        user_id_field.send_keys(USER_ID)
        
        # Step 3: Enter Password
        print("📌 Entering Password...")
        password_field = driver.find_element(By.XPATH, "//input[@type='password']")
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        # Step 4: Click Login button
        print("📌 Clicking Login...")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        time.sleep(3)
        
        # Step 5: Handle TOTP/2FA
        print("📌 Entering TOTP...")
        try:
            totp_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='number']"))
            )
            
            # Generate TOTP
            totp = pyotp.TOTP(TOTP_SECRET)
            totp_code = totp.now()
            print(f"📌 TOTP Code: {totp_code}")
            
            totp_field.clear()
            totp_field.send_keys(totp_code)
            time.sleep(1)
            
            # Click continue/submit
            try:
                submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                submit_button.click()
            except:
                pass  # Some flows auto-submit after TOTP
                
        except Exception as e:
            print(f"⚠️ TOTP step issue: {e}")
        
        # Step 6: Wait for redirect and extract request_token
        print("📌 Waiting for redirect...")
        time.sleep(5)
        
        # Check URL for request_token (multiple attempts)
        request_token = None
        for _ in range(10):
            current_url = driver.current_url
            print(f"📌 Current URL: {current_url}")
            
            if "request_token=" in current_url:
                parsed = urlparse(current_url)
                params = parse_qs(parsed.query)
                request_token = params.get("request_token", [None])[0]
                break
            
            # Check if we're on the authorize page - need to click authorize
            if "/connect/authorize" in current_url:
                try:
                    # Look for authorize button
                    auth_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Authorize') or contains(text(), 'Continue')]")
                    auth_button.click()
                    print("📌 Clicked Authorize button...")
                    time.sleep(3)
                except:
                    pass
            
            time.sleep(2)
        
        if not request_token:
            # Try to get from page source as fallback
            page_source = driver.page_source
            if "request_token" in page_source:
                import re
                match = re.search(r'request_token["\s:=]+([a-zA-Z0-9]+)', page_source)
                if match:
                    request_token = match.group(1)
        
        if not request_token:
            print(f"❌ Failed to get request_token")
            print(f"📌 Final URL: {driver.current_url}")
            driver.save_screenshot("login_error.png")
            print("📸 Screenshot saved as login_error.png")
            return None
        
        print(f"✅ Request Token: {request_token}")
        
        # Step 7: Generate access token
        print("📌 Generating Access Token...")
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]
        
        print(f"✅ Access Token: {access_token}")
        
        # Step 8: Save to .env file
        save_token_to_env(access_token)
        
        # Step 9: Verify connection
        kite.set_access_token(access_token)
        profile = kite.profile()
        print(f"✅ Logged in as: {profile['user_name']} ({profile['user_id']})")
        
        return access_token
        
    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("📸 Screenshot saved as error_screenshot.png")
        return None
        
    finally:
        driver.quit()


def save_token_to_env(access_token):
    """Save access token to .env file"""
    env_path = ".env"
    
    # Read existing content
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add KITE_ACCESS_TOKEN
    token_found = False
    new_lines = []
    for line in lines:
        if line.startswith("KITE_ACCESS_TOKEN="):
            new_lines.append(f"KITE_ACCESS_TOKEN={access_token}\n")
            token_found = True
        else:
            new_lines.append(line)
    
    if not token_found:
        new_lines.append(f"KITE_ACCESS_TOKEN={access_token}\n")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Token saved to {env_path}")


if __name__ == "__main__":
    token = generate_access_token()
    if token:
        print("\n" + "="*50)
        print("✅ SUCCESS! Access token generated and saved.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ FAILED! Check the screenshot for debugging.")
        print("="*50)