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
def scrape_roundhill(driver, ticker, error_dir):
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
                    '배당공시': cols[0].text.strip(),
                    '배당락': cols[1].text.strip(),
                    '주주확정': cols[2].text.strip(),
                    '배당지급일': cols[3].text.strip(),
                    '배당금': cols[4].text.strip(),
                 }
                 data.append(record)
        return data
    except Exception as e:
        print(f"Error scraping {ticker.upper()}: {type(e).__name__} - {e}")
        # 저장 경로를 error_dir 안으로 설정
        file_path = os.path.join(error_dir, f'{ticker.lower()}_error.png')
        driver.save_screenshot(file_path) # 이 부분이 올바르게 되어 있는지 확인
        return []
    


# 2. YieldMax 함수 (Shadow DOM 쿠키 팝업 해결 최종 버전)
def scrape_yieldmax(driver, url_ticker, error_dir):
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
        wait = WebDriverWait(driver, 5)
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
        file_path = os.path.join(error_dir, f'{url_ticker.lower()}_error.png')
        driver.save_screenshot(file_path)
        return []  
    
    
# YieldMax 사이트 전용 API 스크래핑 함수 (Selenium 불필요!)
def scrape_yieldmax_api(url_ticker, error_dir):
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
        file_path = os.path.join(error_dir, f'{url_ticker.lower()}_error.png')
        driver.save_screenshot(file_path)
        return []    
    


# 3. JPMorgan 함수
def scrape_jepi(driver, error_dir):
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
        file_path = os.path.join(error_dir, 'jepi_error.png')
        driver.save_screenshot(file_path)
        return []



# --- 메인 실행 로직 (YieldMax 그룹화 적용 버전) ---
if __name__ == "__main__":
    
    # --- 크롤링할 티커 목록들 ---
    
    roundhill_tickers = [
        "xdte", "qdte", "rdte", "xpay", "ybtc", "yeth", "week", "magy",
        "aapw", "amzw", "brkw", "coiw", "hoow", "metw", "nflw", "nvdw",
        "pltw", "tslw"
    ]
    
    # 요청하신 대로, YieldMax 티커들을 5개의 관리하기 쉬운 그룹으로 나눕니다.
    # (내용은 원하시는 대로 자유롭게 그룹 간에 이동하셔도 됩니다.)
    
    yieldmax_A_map = {
        "brkc": "brkc", "crsh": "crsh", "feat": "feat", "fivy": "fivy", "gooy": "gooy", 
        "oark": "oark", "snoy": "snoy", "tsly": "tsly", "tsmy": "tsmy", "xomo": "xomo",
         "ybit": "ybit"
    }
    
    yieldmax_B_map = {
        "babo": "babo", "dips": "dips", "fby": "fby", "gdxy": "gdxy", "jpmo": "jpmo",
        "maro": "maro", "mrny": "mrny", "nvdy": "nvdy", "plty": "plty"
    }
    
    yieldmax_C_map = {
        "abny": "abny", "amdy": "amdy", "cony": "cony", "cvny": "cvny", "fiat": "fiat", 
        "hooy": "hooy", "msfo": "msfo", "nfly": "nfly", "pypy": "pypy"
    }
    
    yieldmax_D_map = {
        "aiyy": "aiyy", "amzy": "amzy", "aply": "aply", "diso": "diso", "msty": "msty", 
        "smcy": "smcy", "wntr": "wntr", "yqqq": "yqqq",  "xyzy": "sqy" # URL(sqy)과 실제 티커(xyzy)가 다른 경우
    }
    
    yieldmax_Other_map = { # 이름을 Weekly 대신 Other로 했습니다. 더 명확해 보입니다.
        "lfgy": "lfgy", "gpty": "gpty", "chpy": "chpy", 
        "sdty": "sdty", "qdty": "qdty", "rdty": "rdty",
        "ymax": "ymax", "ymag": "ymag", "ulty": "ulty",
        "bigy": "bigy", "soxy": "soxy", "rnty": "rnty", 
    }
    
    # 데이터를 저장할 폴더와 에러 스크린샷을 저장할 폴더 생성
    output_dir = 'public/data'
    error_screenshot_dir = 'error_screenshots'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(error_screenshot_dir, exist_ok=True)

    # 모든 데이터를 저장할 최종 딕셔너리
    all_data = {}
    
    # --- 작업 그룹 1: Roundhill ETFs ---
    print("\n--- [GROUP 1] Starting Roundhill ETFs ---")
    driver = setup_driver()
    for ticker in roundhill_tickers:
        data = scrape_roundhill(driver, ticker, error_screenshot_dir)
        if data:
            file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f" => Saved data to {file_path}")
        time.sleep(1)
    driver.quit()
    print("--- [GROUP 1] Finished Roundhill ETFs ---")
    
    # --- 작업 그룹 2: YieldMax ETFs (그룹별로 처리) ---
    print("\n--- [GROUP 2] Starting YieldMax ETFs ---")
    
    # 처리할 YieldMax 그룹들을 리스트에 담습니다.
    yieldmax_groups_to_run = [
        ("Group A", yieldmax_A_map),
        ("Group B", yieldmax_B_map),
        ("Group C", yieldmax_C_map),
        ("Group D", yieldmax_D_map),
        ("Group Other", yieldmax_Other_map),
    ]

    # 각 그룹을 순회하며 크롤링 실행
    for group_name, ticker_map in yieldmax_groups_to_run:
        print(f"\n--- [YieldMax - {group_name}] Starting ---")
        driver = setup_driver() # 각 YieldMax 소그룹마다 새 드라이버 시작 (안정성 향상)
        for save_name, url_name in ticker_map.items():
            data = scrape_yieldmax(driver, url_name, error_screenshot_dir)
            if data:
                file_path = os.path.join(output_dir, f"{save_name.lower()}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f" => Saved data to {file_path}")
            time.sleep(1)
        driver.quit() # 소그룹 작업이 끝나면 드라이버 종료
        print(f"--- [YieldMax - {group_name}] Finished ---")
        
    # --- 작업 그룹 3: 개별 ETF들 ---
    print("\n--- [GROUP 3] Starting Individual ETFs ---")
    driver = setup_driver()
    jepi_data = scrape_jepi(driver, error_screenshot_dir)
    if jepi_data:
        file_path = os.path.join(output_dir, "jepi.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(jepi_data, f, ensure_ascii=False, indent=2)
        print(f" => Saved data to {file_path}")
    driver.quit()
    print("--- [GROUP 3] Finished Individual ETFs ---")

    print("\n--- ALL TASKS FINISHED ---")
    print("Individual JSON files created in public/data/ directory.")