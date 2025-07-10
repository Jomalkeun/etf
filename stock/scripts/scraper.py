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
        
        existing_data = None
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # print(f"  -> Found existing data for {ticker}.")
            except Exception as e:
                print(f"  -> Warning: Could not read existing file for {ticker}. Error: {e}")
        
        new_scraped_data = scrape_with_yfinance(
            ticker, 
            info['company'], 
            info['frequency'], 
            info['group']
        )
        if not new_scraped_data:
            # print(f"  -> No data scraped from yfinance for {ticker}. Skipping update.")
            continue
            
        new_ticker_info = new_scraped_data.get('tickerInfo', {})
        new_dividend_history = new_scraped_data.get('dividendHistory', [])
        
        has_changed = False
        
        if not existing_data:
            final_data_to_save = new_scraped_data
            if new_scraped_data.get('dividendHistory'):
                has_changed = True
        else:
            final_history = existing_data.get('dividendHistory', [])
            
            # --- Ticker Info 변경 감지 ---
            existing_ticker_info_for_compare = existing_data.get('tickerInfo', {}).copy()
            existing_ticker_info_for_compare.pop('Update', None)
            new_ticker_info_for_compare = new_ticker_info.copy()
            new_ticker_info_for_compare.pop('Update', None)
            if new_ticker_info_for_compare != existing_ticker_info_for_compare:
                has_changed = True
                print(f"  -> Ticker info for {ticker} has changed.")

            # --- 데이터 보강 및 추가 로직 (핵심 수정) ---
            new_dividends_map = {item['배당락일']: item for item in new_dividend_history}
            enriched_items_count = 0
            
            # 1. 기존 데이터 보강
            for item in final_history:
                ex_date = item['배당락일']
                # 주가 정보가 비어있고, yfinance에 해당 날짜의 데이터가 있다면 보강 시도
                if item.get('배당락전일종가', 'N/A') == 'N/A' and ex_date in new_dividends_map:
                    print(f"  -> Enriching data for {ticker} on {ex_date}...")
                    new_item_info = new_dividends_map[ex_date]
                    
                    # 주가 정보만 가져와서 업데이트
                    item.update({
                        '배당락전일종가': new_item_info.get('배당락전일종가', 'N/A'),
                        '배당락일종가': new_item_info.get('배당락일종가', 'N/A'),
                    })
                    has_changed = True
                    enriched_items_count += 1
            
            if enriched_items_count > 0:
                print(f"  -> Enriched {enriched_items_count} existing entries with price data for {ticker}.")

            # 2. 새로운 데이터 추가
            existing_dates = {item['배당락일'] for item in final_history}
            new_entries_to_add = [
                item for item in new_dividend_history 
                if item['배당락일'] not in existing_dates
            ]
            if new_entries_to_add:
                has_changed = True
                print(f"  -> Found {len(new_entries_to_add)} new dividend entries for {ticker}.")
                final_history.extend(new_entries_to_add)
            
            final_data_to_save = {
                "tickerInfo": new_ticker_info,
                "dividendHistory": final_history
            }
        
        if has_changed:
            final_history.sort(key=lambda x: datetime.strptime(x['배당락일'], '%y. %m. %d'), reverse=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
            print(f" => UPDATED and saved data for {ticker} to {file_path}")
            total_changed_files += 1
        else:
            print(f"  -> No changes detected for {ticker}. Skipping file write.")
            
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")
    print(f"Total files updated: {total_changed_files}")