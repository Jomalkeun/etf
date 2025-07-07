import time
import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- 드라이버 설정 (기존 코드를 그대로 사용, 안정적임) ---
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

# 1. Roundhill 사이트 전용 범용 함수 (NEW & IMPROVED)
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
        # 테이블이 나타날 때까지 최대 15초 대기
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.distri-table")))
        time.sleep(1) # 데이터 렌더링을 위한 짧은 대기

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 제목이 'Distribution History' 또는 'Weekly Distributions'인 경우 모두 찾기
        heading = soup.find('h3', string='Distribution History')
        if not heading:
            heading = soup.find('h3', string='Weekly Distributions')

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

# 2. YieldMax 사이트 전용 함수
def scrape_ymax(driver):
    url = "https://www.yieldmaxetfs.com/our-etfs/ymax/"
    print(f"Scraping YMAX from {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "table_11")))
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        table = soup.select_one('#table_11')
        headers = [th.get_text(strip=True) for th in table.select('thead tr th')]
        data = []
        for row in table.select('tbody tr'):
            cols = [td.get_text(strip=True) for td in row.select('td')]
            if len(cols) == len(headers):
                data.append(dict(zip(headers, cols)))
        return data
    except Exception as e:
        print(f"Error scraping YMAX: {type(e).__name__} - {e}")
        driver.save_screenshot('ymax_error.png')
        return []

# 3. JPMorgan 사이트 전용 함수
def scrape_jepi(driver):
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
        
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#card-component-dividendSchedule table")))
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

# --- 메인 실행 로직 (훨씬 깔끔해짐) ---
if __name__ == "__main__":
    
    # 크롤링할 Roundhill 티커 목록
    roundhill_tickers = [
        "xdte", "qdte", "rdte", "xpay", "ybtc", "yeth", "week", "magy",
        "aapw", "amzw", "brkw", "coiw", "hoow", "metw", "nflw", "nvdw",
        "pltw", "tslw"
    ]
    
    driver = setup_driver()
    all_data = {}
    
    # 반복문을 사용해 Roundhill 티커들을 한번에 처리
    for ticker in roundhill_tickers:
        all_data[ticker] = scrape_roundhill(driver, ticker)
        time.sleep(1) # 각 요청 사이에 1초의 간격을 두어 서버 부담을 줄임
        
    # 나머지 사이트들 처리
    all_data["ymax"] = scrape_ymax(driver)
    all_data["jepi"] = scrape_jepi(driver)

    driver.quit()
    
    with open('public/dividends.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("\n--- Scraping Finished ---")
    print("All ETF data scraped and saved to public/dividends.json")