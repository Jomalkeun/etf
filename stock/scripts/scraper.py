import time
import json
import os
import yfinance as yf
from datetime import datetime, timedelta

def get_historical_prices(ticker_symbol, ex_date_str):
    # print(f"  -> Fetching historical prices for {ticker_symbol.upper()} around {ex_date_str}...")
    try:
        ex_date = datetime.strptime(ex_date_str, '%m/%d/%Y')
        start_date = ex_date - timedelta(days=7)
        end_date = ex_date + timedelta(days=2)
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(start=start_date, end=end_date)
        if hist.empty: return {"before_price": "N/A", "on_price": "N/A"}
        on_price, before_price = "N/A", "N/A"
        try:
            on_price_val = hist.loc[:ex_date.strftime('%Y-%m-%d')].iloc[-1]['Close']
            on_price = f"${on_price_val:.2f}"
        except IndexError: pass
        try:
            before_date_target = ex_date - timedelta(days=1)
            before_price_val = hist.loc[:before_date_target.strftime('%Y-%m-%d')].iloc[-1]['Close']
            before_price = f"${before_price_val:.2f}"
        except IndexError: pass
        return {"before_price": before_price, "on_price": on_price}
    except Exception as e:
        print(f"     Could not fetch price for {ticker_symbol}. Error: {e}")
        return {"before_price": "N/A", "on_price": "N/A"}

# --- 2. yfinance 전용 범용 스크래퍼 ---
def scrape_with_yfinance(ticker_symbol, company, frequency, group):
    print(f"Scraping {ticker_symbol.upper()} (Group: {group}) using yfinance API...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        from datetime import timezone # timezone 객체를 사용하기 위해 임포트

        # 시간대 정보가 포함된(aware) 현재 UTC 시간을 가져옵니다.
        now_utc = datetime.now(timezone.utc)
        
        # 한국 시간대(UTC+9)로 변환합니다.
        korea_timezone = timezone(timedelta(hours=9))
        now_kst = now_utc.astimezone(korea_timezone)
        
        update_time_str = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')

        full_name = info.get('longName', ticker_symbol.upper())

        ticker_info = {
            "name": ticker_symbol.upper(),
            "fullname": full_name,
            "company": company,
            "frequency": frequency,
            "group": group,
            "Update": update_time_str,
            "52Week": f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}" if info.get('fiftyTwoWeekLow') else "N/A",
            "Volume": f"{info.get('volume', 0):,}" if info.get('volume') else "N/A",
            "AvgVolume": f"{info.get('averageVolume', 0):,}" if info.get('averageVolume') else "N/A",
            "NAV": f"${info.get('navPrice', 0):.2f}" if info.get('navPrice') else "N/A",
            "Yield": f"{(info.get('trailingAnnualDividendYield', 0) * 100):.2f}%" if info.get('trailingAnnualDividendYield') else "N/A",
            "TotalReturn": f"{(info.get('ytdReturn', 0) * 100):.2f}%" if info.get('ytdReturn') else "N/A",
        }
        
        dividends_df = ticker.dividends.to_frame()
        dividend_history = []
        if not dividends_df.empty:
            dividends_df = dividends_df.reset_index()
            dividends_df.columns = ['ExDate', 'Dividend']
            
            for index, row in dividends_df.iterrows():
                ex_date = row['ExDate'].to_pydatetime().replace(tzinfo=None)
                
                if ex_date < datetime.now() - timedelta(days=365 * 10):
                    continue

                ex_date_str_mdy = ex_date.strftime('%m/%d/%Y')
                dividend_amount = row['Dividend']
                
                prices = get_historical_prices(ticker_symbol, ex_date_str_mdy)
                
                record = {
                    '배당락일': ex_date.strftime('%y. %m. %d'),
                    '배당금': f"${dividend_amount:.4f}",
                    '배당락전일종가': prices['before_price'],
                    '배당락일종가': prices['on_price'],
                }
                dividend_history.append(record)
        
        return {"tickerInfo": ticker_info, "dividendHistory": dividend_history}

    except Exception as e:
        print(f"  -> Error scraping {ticker_symbol.upper()} with yfinance: {e}")
        return None    
    
# --- 3. 메인 실행 로직 (근사치 비교 및 데이터 보강 최종 버전) ---
if __name__ == "__main__":
    
    nav_file_path = 'public/nav.json'
    all_tickers_info = {}
    try:
        with open(nav_file_path, 'r', encoding='utf-8') as f:
            nav_data_json = json.load(f)
            ticker_list = nav_data_json.get('nav', [])
            for item in ticker_list:
                ticker = item.get('name')
                if ticker:
                    all_tickers_info[ticker] = {
                        "company": item.get('company', 'N/A'),
                        "frequency": item.get('frequency', 'N/A'),
                        "group": item.get('group', 'N/A')
                    }
        print(f"Successfully loaded {len(all_tickers_info)} tickers from {nav_file_path}")
    except Exception as e:
        exit()

    output_dir = 'public/data'
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n--- Starting All Scrapes with Data Enrichment & Fuzzy Matching ---")
    
    total_changed_files = 0
    
    for ticker, info in all_tickers_info.items():
        file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
        
        # --- 1. 기존 데이터 로드 ---
        existing_data = None
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    print(f"  -> Found existing data for {ticker}.")
            except Exception as e:
                print(f"  -> Warning: Could not read existing file for {ticker}. Error: {e}")

        # --- 2. yfinance로 새로운 데이터 스크래핑 ---
        new_scraped_data = scrape_with_yfinance(ticker, info['company'], info['frequency'], info['group'])
        if not new_scraped_data:
            print(f"  -> No data scraped from yfinance for {ticker}. Skipping update.")
            continue
            
        new_ticker_info = new_scraped_data.get('tickerInfo', {})
        new_dividend_history = new_scraped_data.get('dividendHistory', [])
        
        has_changed = False # 데이터 변경 여부를 추적
        
        if not existing_data or not existing_data.get('dividendHistory'):
            final_history = new_dividend_history
            if final_history: has_changed = True
        else:
            final_history = existing_data.get('dividendHistory', [])
            
            # 빠른 조회를 위해 새로운 데이터를 '배당락일'을 키로 하는 딕셔너리로 변환
            new_dividends_map = {item['배당락일']: item for item in new_dividend_history}

            # --- 3. 데이터 보강 및 근사치 비교 (핵심 로직) ---
            enriched_items_count = 0
            for item in final_history:
                ex_date = item['배당락일']
                # 조건 1: 주가 정보가 비어있다.
                if item.get('배당락전일종가', 'N/A') == 'N/A':
                    # 조건 2: yfinance에 해당 날짜의 데이터가 존재한다.
                    if ex_date in new_dividends_map:
                        new_item_info = new_dividends_map[ex_date]
                        
                        # 조건 3: 배당금이 근사치 내에 있는지 확인
                        try:
                            old_amount = float(item.get('배당금', '$0').replace('$', ''))
                            new_amount = float(new_item_info.get('배당금', '$0').replace('$', ''))
                            # 오차 허용 범위 (예: 0.0001)
                            TOLERANCE = 0.0001
                            
                            if abs(old_amount - new_amount) < TOLERANCE:
                                print(f"  -> Enriching data for {ticker} on {ex_date} (Amounts match: {old_amount} ~ {new_amount})")
                                # 주가 정보만 보강
                                item.update({
                                    '배당락전일종가': new_item_info.get('배당락전일종가', 'N/A'),
                                    '배당락일종가': new_item_info.get('배당락일종가', 'N/A'),
                                    # 배당금은 반올림된 값으로 업데이트하여 통일
                                    '배당금': new_item_info.get('배당금', item.get('배당금'))
                                })
                                has_changed = True
                                enriched_items_count += 1
                        except (ValueError, TypeError):
                            # 숫자 변환 실패 시 그냥 넘어감
                            pass

            # --- 4. 완전히 새로운 데이터 추가 ---
            existing_dates = {item['배당락일'] for item in final_history}
            new_entries_to_add = [
                item for item in new_dividend_history if item['배당락일'] not in existing_dates
            ]
            if new_entries_to_add:
                has_changed = True
                print(f"  -> Found {len(new_entries_to_add)} new dividend entries for {ticker}.")
                final_history.extend(new_entries_to_add)

        # --- 5. 최종 저장 ---
        if has_changed:
            # tickerInfo는 항상 최신 정보로 업데이트
            final_history.sort(key=lambda x: datetime.strptime(x['배당락일'], '%y. %m. %d'), reverse=True)
            final_data_to_save = {"tickerInfo": new_ticker_info, "dividendHistory": final_history}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
            print(f" => UPDATED and saved data for {ticker} to {file_path}")
            total_changed_files += 1
        else:
            print(f"  -> No changes detected for {ticker}. Skipping file write.")
            
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")
    print(f"Total files updated: {total_changed_files}")