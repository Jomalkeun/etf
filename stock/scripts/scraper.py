import time
import json
import os
import yfinance as yf
from datetime import datetime, timedelta

def get_historical_prices(ticker_symbol, ex_date_str):
    """yfinance를 사용해 특정 티커의 배당락일 및 배당락 전일 종가를 가져옵니다."""
    print(f"  -> Fetching historical prices for {ticker_symbol.upper()} around {ex_date_str}...")
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

# --- yfinance 전용 범용 스크래퍼 ---
def scrape_with_yfinance(ticker_symbol, company, frequency, group):
    print(f"Scraping {ticker_symbol.upper()} (Group: {group}) using yfinance API...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        now_utc = datetime.utcnow()
        now_kst = now_utc + timedelta(hours=9)
        update_time_str = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')

        # 1. 'longName' 키로 fullname을 가져옵니다. 없으면 티커를 기본값으로 사용합니다.
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
            
            for index, row in dividends_df.head(24).iterrows():
                ex_date = row['ExDate'].to_pydatetime()
                ex_date_str_mdy = ex_date.strftime('%m/%d/%Y')
                dividend_amount = row['Dividend']
                
                prices = get_historical_prices(ticker_symbol, ex_date_str_mdy)
                
                record = {
                    '배당락일_ts': ex_date.timestamp(),
                    '배당락일': ex_date.strftime('%y. %m. %d'),
                    '배당금': f"${dividend_amount:.4f}",
                    '배당락전일종가': prices['before_price'],
                    '배당락일종가': prices['on_price'],
                }
                dividend_history.append(record)
        
        final_data = {
            "tickerInfo": ticker_info,
            "dividendHistory": dividend_history
        }
        return final_data

    except Exception as e:
        print(f"  -> Error scraping {ticker_symbol.upper()} with yfinance: {e}")
        return None
    
# --- 3. 메인 실행 로직 (nav.json 실제 구조에 맞춤) ---
if __name__ == "__main__":
    
    # --- 1. nav.json 파일 로드 (group 정보 추가) ---
    nav_file_path = 'public/nav.json'
    all_tickers_info = {}

    try:
        with open(nav_file_path, 'r', encoding='utf-8') as f:
            nav_data_json = json.load(f)
            
            # nav.json의 실제 구조에 맞춰 데이터를 가져옵니다.
            # 최상위 키 'nav' 안에 있는 리스트를 사용합니다.
            ticker_list = nav_data_json.get('nav', [])
            
            for item in ticker_list:
                # 각 아이템(딕셔너리)에서 필요한 정보를 추출합니다.
                ticker = item.get('name')
                if ticker:
                    all_tickers_info[ticker] = {
                        "company": item.get('company', 'N/A'),
                        "frequency": item.get('frequency', 'N/A'),
                        "group": item.get('group', 'N/A')
                    }
        print(f"Successfully loaded {len(all_tickers_info)} tickers from {nav_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred while loading {nav_file_path}: {e}")
        exit()

    # --- 2. 스크래핑 실행 (함수 호출 시 group 정보 전달) ---
    output_dir = 'public/data'
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n--- Starting All Scrapes based on nav.json ---")
    
    for ticker, info in all_tickers_info.items():
        file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
        
        existing_data = None
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    print(f"  -> Found existing data for {ticker}.")
            except Exception as e:
                print(f"  -> Warning: Could not read existing file for {ticker}. Error: {e}")
        
        # 함수를 호출할 때 info['group']을 추가로 전달합니다.
        new_scraped_data = scrape_with_yfinance(
            ticker, 
            info['company'], 
            info['frequency'], 
            info['group']
        )
        
        if not new_scraped_data:
            print(f"  -> No data scraped from yfinance for {ticker}. Skipping update.")
            continue

        new_ticker_info = new_scraped_data.get('tickerInfo', {})
        new_dividend_history = new_scraped_data.get('dividendHistory', [])
        new_dividends_map_by_ts = {item['배당락일_ts']: item for item in new_dividend_history}

        if not existing_data or not existing_data.get('dividendHistory'):
            final_history = new_dividend_history
            print(f"  -> No existing history. Using all {len(final_history)} scraped records.")
        else:
            enriched_history = []
            existing_timestamps = set()

            for old_item in existing_data['dividendHistory']:
                old_date_str = old_item.get('배당락일')
                if not old_date_str: continue

                try:
                    old_timestamp = datetime.strptime(old_date_str, '%y. %m. %d.').timestamp()
                except ValueError:
                    continue
                
                existing_timestamps.add(old_timestamp)
                
                # 주가 정보 보강 로직
                if old_item.get('배당락전일종가', 'N/A') == 'N/A' and old_timestamp in new_dividends_map_by_ts:
                    print(f"  -> Enriching data for {ticker} on {old_date_str}...")
                    new_info = new_dividends_map_by_ts[old_timestamp]
                    old_item.update({
                        '배당락전일종가': new_info.get('배당락전일종가', 'N/A'),
                        '배당락일종가': new_info.get('배당락일종가', 'N/A'),
                        '배당금': new_info.get('배당금', old_item.get('배당금')),
                    })
                enriched_history.append(old_item)
            
            new_entries_to_add = [
                new_item for ts, new_item in new_dividends_map_by_ts.items() 
                if ts not in existing_timestamps
            ]

            if new_entries_to_add:
                print(f"  -> Found {len(new_entries_to_add)} completely new dividend entries for {ticker}.")
            
            final_history = new_entries_to_add + enriched_history

         # 1. '배당락일_ts'가 없는 항목(수동 추가 데이터)에 대해 타임스탬프를 생성해줍니다.
        for item in final_history:
            if '배당락일_ts' not in item:
                try:
                    # 마침표가 있든 없든 처리할 수 있도록 .strip('.') 사용
                    date_str = item.get('배당락일', '').strip('.')
                    item['배당락일_ts'] = datetime.strptime(date_str, '%y. %m. %d').timestamp()
                except (ValueError, TypeError):
                    # 변환 실패 시, 정렬에서 뒤로 밀리도록 0을 할당
                    item['배당락일_ts'] = 0

        # 2. 이제 모든 항목에 '배당락일_ts'가 있으므로, 이것으로 안전하게 정렬합니다.
        final_history.sort(key=lambda x: x['배당락일_ts'], reverse=True)
        
        # 3. 마지막으로, 내부 처리용이었던 '배당락일_ts' 필드를 제거합니다.
        for item in final_history:
            item.pop('배당락일_ts', None)

        # --- 이후 파일 저장 로직은 동일 ---
        final_data_to_save = {
            "tickerInfo": new_ticker_info,
            "dividendHistory": final_history
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
        print(f" => Processed and saved data for {ticker} to {file_path}")
        
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")