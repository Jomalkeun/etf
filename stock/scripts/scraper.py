import time
import json
import os
import undetected_chromedriver as uc
import requests
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- 드라이버 설정 ---
def setup_driver():
    options = uc.ChromeOptions()
    # Codespaces/GitHub Actions에서는 헤드리스 모드가 필수입니다.
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # 프로필 기능은 현재 사용하지 않으므로 주석 처리하거나 삭제해도 괜찮습니다.
    # 하지만 그냥 두어도 다른 사이트에 영향을 주지 않으므로 유지하겠습니다.
    profile_path = os.path.join(os.getcwd(), "chrome_profile") 
    options.add_argument(f"--user-data-dir={profile_path}")
    
    print("Setting up Chrome driver...")
    driver = uc.Chrome(
        browser_executable_path="/usr/bin/google-chrome", 
        options=options
    )
    driver.set_page_load_timeout(45)
    print("Driver setup complete.")
    return driver

# --- 범용 크롤링 함수들 ---

# 1. Roundhill 함수 사이트 전용 범용 함수 (NEW & IMPROVED)
def scrape_roundhill(driver, ticker):
    """
    roundhillinvestments.com 사이트의 모든 ETF를 처리하는 범용 함수.
    ticker 이름만 바꿔서 호출하면 됩니다.
    'Distribution History'와 'Weekly Distributions' 제목 모두 처리합니다.
    """
    url = f"https://www.roundhillinvestments.com/etf/{ticker.lower()}/"
    print(f"Scraping {ticker.upper()} from {url}")
    try:
        driver.get(url)
        # 테이블이 나타날 때까지 최대 20초 대기
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.distri-table")))
        time.sleep(1) # 데이터 렌더링을 위한 짧은 대기

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 제목이 'Distribution History' 또는 'Weekly Distributions'인 경우 모두 찾기
        heading = soup.find('h3', string='Distribution History')
        if not heading: heading = soup.find('h3', string='Weekly Distributions')
        # 만약 제목을 찾지 못했다면, 에러 메시지를 남기고 빈 리스트 반환
        if not heading:
            print(f"Could not find a distribution heading for {ticker.upper()}.")
            return []

        table = heading.find_next('table', class_='distri-table')
        data = []
        for row in table.select('tbody tr'):
            cols = row.find_all('td')
            # Roundhill 사이트는 항상 5개의 열을 가집니다.
            if len(cols) == 5:
                 record = {
                    'Declaration': cols[0].text.strip(),
                    'Ex Date': cols[1].text.strip(),
                    'Record Date': cols[2].text.strip(),
                    'Pay Date': cols[3].text.strip(),
                    'Amount Paid': cols[4].text.strip(),
                 }
                 data.append(record)
        return data
    except Exception as e:
        print(f"Error scraping {ticker.upper()}: {type(e).__name__} - {e}")
        driver.save_screenshot(f'{ticker.lower()}_error.png')
        return []
    


# 2. YieldMax 함수 (Shadow DOM 쿠키 팝업 해결 최종 버전)
def scrape_yieldmax(driver, url_ticker):
    """
    yieldmaxetfs.com의 Shadow DOM으로 구현된 쿠키 팝업을 해결합니다.
    """
    url = f"https://www.yieldmaxetfs.com/our-etfs/{url_ticker.lower()}/"
    print(f"Scraping {url_ticker.upper()} from {url}")
    try:
        driver.get(url)
        
        # --- Shadow DOM 쿠키 동의 버튼 처리 로직 ---
        try:
            wait = WebDriverWait(driver, 15)
            shadow_host = wait.until(EC.presence_of_element_located((By.ID, "usercentrics-root")))
            
            shadow_root = driver.execute_script('return arguments[0].shadowRoot', shadow_host)
            
            accept_button = shadow_root.find_element(By.CSS_SELECTOR, 'button[data-testid="uc-accept-all-button"]')
            accept_button.click()
            
            print(f"Successfully handled Shadow DOM cookie banner for {url_ticker.upper()}.")
            time.sleep(2)

        except Exception as e:
            # 여기가 수정된 부분입니다.
            print(f"Cookie banner (Shadow DOM) not found or failed to click for {url_ticker.upper()}. Proceeding... Error: {e}")

        # --- 기존 테이블 스크래핑 로직 ---
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h2[text()='Distributions']/following-sibling::div//table/tbody")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        heading = soup.find('h2', string='Distributions')
        if not heading: return []
            
        table = heading.find_next('table')
        if not table: return []

        headers = [th.get_text(strip=True) for th in table.select('thead tr th')]
        data = []
        for row in table.select('tbody tr'):
            cols = [td.get_text(strip=True) for td in row.select('td')]
            if len(cols) == len(headers):
                data.append(dict(zip(headers, cols)))
        return data
    except Exception as e:
        print(f"Error scraping {url_ticker.upper()}: {type(e).__name__} - {e}")
        driver.save_screenshot(f'{url_ticker.lower()}_error.png')
        return []    
    
    
# YieldMax 사이트 전용 API 스크래핑 함수 (Selenium 불필요!)
def scrape_yieldmax_api(url_ticker):
    """
    yieldmaxetfs.com 사이트는 2단계 API 요청으로 데이터를 가져옵니다.
    1. 메인 페이지에서 포스트 ID를 알아냅니다.
    2. 그 ID로 API에 데이터를 요청합니다.
    이것이 유일하고 올바른 방법입니다.
    """
    print(f"Scraping {url_ticker.upper()} using direct API...")
    try:
        # 1단계: 메인 페이지에서 Post ID 추출
        main_url = f"https://www.yieldmaxetfs.com/our-etfs/{url_ticker.lower()}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        main_response = requests.get(main_url, headers=headers, timeout=20)
        main_response.raise_for_status()

        # 페이지 소스에서 'postid-1234' 같은 클래스를 찾아 ID를 추출
        match = re.search(r'postid-(\d+)', main_response.text)
        if not match:
            print(f"Error: Could not find Post ID for {url_ticker.upper()}.")
            return []
        post_id = match.group(1)

        #}")

        # --- 기존 테이블 스크래핑 로직 ---
        # 이제 쿠키 팝업이 사라졌으므로, 이 부분은 정상적으로 작동합니다.
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h2[text()='Distributions']/following-sibling::div//table/tbody")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        heading = soup.find('h2', string='Distributions')
        if not heading: return []
            
        table = heading.find_next('table')
        if not table: return []

        headers = [th.get_text(strip=True) for th in table.select('thead tr th')]
        data = []
        for row in table.select('tbody tr'):
            cols = [td.get_text(strip=True) for td in row.select('td')]
            if len(cols) == len(headers):
                data.append(dict(zip(headers, cols)))
        return data
    except Exception as e:
        print(f"Error scraping {url_ticker.upper()}: {type(e).__name__} - {e}")
        driver.save_screenshot(f'{url_ticker.lower()}_error.png')
        return []    
    


# 3. JPMorgan 함수
def scrape_jepi(driver):
    # (이전 코드와 동일, 안정성을 위해 대기 시간만 20초로 늘림)
    url = "https://am.jpmorgan.com/us/en/asset-management/adv/products/jpmorgan-equity-premium-income-etf-etf-shares-46641q332#/dividends"
    print(f"Scraping JEPI from {url}")
    try:
        driver.get(url)
        try:
            cookie_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "inner-footer-link")))
            cookie_button.click()
            time.sleep(2)
        except:
            print("JEPI: Cookie banner not found or could not be clicked.")
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#card-component-dividendSchedule table tbody")))
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        table = soup.select_one('#card-component-dividendSchedule table')
        headers = [th.get_text(strip=True) for th in table.select('thead tr th')]
        data = []
        for row in table.select('tbody tr'):
            cols = [td.get_text(strip=True) for td in row.select('td')]
            if len(cols) == len(headers):
                data.append(dict(zip(headers, cols)))
        return data
    except Exception as e:
        print(f"Error scraping JEPI: {type(e).__name__} - {e}")
        driver.save_screenshot('jepi_error.png')
        return []





# --- 메인 실행 로직 (파일 분리 버전) ---
if __name__ == "__main__":
    
    # 크롤링할 티커 목록들
    roundhill_tickers = [
        "xdte", "qdte", "rdte", "xpay", "ybtc", "yeth", "week", "magy",
        "aapw", "amzw", "brkw", "coiw", "hoow", "metw", "nflw", "nvdw",
        "pltw", "tslw"
    ]
    
    yieldmax_tickers_map = {
        "tsly": "tsly", "oark": "oark", "aply": "aply", "nvdy": "nvdy", "amzy": "amzy", 
        "fby": "fby", "gooy": "gooy", "cony": "cony", "nfly": "nfly", "diso": "diso", 
        "msfo": "msfo", "xomo": "xomo", "jpmo": "jpmo", "amdy": "amdy", "pypy": "pypy", 
        "mrny": "mrny", "aiyy": "aiyy", "msty": "msty", "ybit": "ybit", "gdxy": "gdxy", 
        "snoy": "snoy", "abny": "abny", "babo": "babo", "tsmy": "tsmy", "smcy": "smcy", 
        "plty": "plty", "maro": "maro", "cvny": "cvny", "hooy": "hooy", "brkc": "brkc",
        "ymax": "ymax", "ymag": "ymag", "fivy": "fivy", "feat": "feat", "ulty": "ulty",
        "crsh": "crsh", "fiat": "fiat", "dips": "dips", "yqqq": "yqqq", "wntr": "wntr",
        "bigy": "bigy", "soxy": "soxy", "rnty": "rnty", "lfgy": "lfgy", "gpty": "gpty",
        "chpy": "chpy", "sdty": "sdty", "qdty": "qdty", "rdty": "rdty",
        "xyzy": "sqy"
    }
    
    # 데이터를 저장할 폴더 생성 (폴더가 없으면 만들어줌)
    output_dir = 'public/data'
    os.makedirs(output_dir, exist_ok=True)

    # --- 작업 그룹 1: Roundhill ETFs ---
    print("\n--- [GROUP 1] Starting Roundhill ETFs ---")
    driver = setup_driver()
    for ticker in roundhill_tickers:
        data = scrape_roundhill(driver, ticker)
        # 데이터를 가져왔을 경우에만 파일로 저장
        if data:
            file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f" => Saved data to {file_path}")
        time.sleep(1)
    driver.quit()
    print("--- [GROUP 1] Finished Roundhill ETFs ---")
    
    # --- 작업 그룹 2: YieldMax ETFs ---
    print("\n--- [GROUP 2] Starting YieldMax ETFs ---")
    driver = setup_driver()
    for save_name, url_name in yieldmax_tickers_map.items():
        data = scrape_yieldmax(driver, url_name)
        if data:
            file_path = os.path.join(output_dir, f"{save_name.lower()}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f" => Saved data to {file_path}")
        time.sleep(1)
    driver.quit()
    print("--- [GROUP 2] Finished YieldMax ETFs ---")
        
    # --- 작업 그룹 3: 개별 ETF들 ---
    print("\n--- [GROUP 3] Starting Individual ETFs ---")
    driver = setup_driver()
    jepi_data = scrape_jepi(driver)
    if jepi_data:
        file_path = os.path.join(output_dir, "jepi.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(jepi_data, f, ensure_ascii=False, indent=2)
        print(f" => Saved data to {file_path}")
    driver.quit()
    print("--- [GROUP 3] Finished Individual ETFs ---")

    print("\n--- ALL TASKS FINISHED ---")
    print("Individual JSON files created in public/data/ directory.")