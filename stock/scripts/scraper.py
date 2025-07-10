import time
import json
import os
import yfinance as yf
from datetime import datetime, timedelta

def get_historical_prices(ticker_symbol, ex_date_str):
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
        
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        korea_timezone = timezone(timedelta(hours=9))
        now_kst = now_utc.astimezone(korea_timezone)
        update_time_str = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')

        full_name = info.get('longName', ticker_symbol.upper())
        ticker_info = {
            "name": ticker_symbol.upper(), "fullname": full_name, "company": company,
            "frequency": frequency, "group": group, "Update": update_time_str,
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
                if ex_date < datetime.now() - timedelta(days=365 * 10): continue
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
    
# --- 3. 메인 실행 로직 ---
if __name__ == "__main__":
    
    nav_file_path = 'public/nav.json'
    all_tickers_info = {}
    try:
        with open(nav_file_path, 'r', encoding='utf-8') as f:
            ticker_list = json.load(f).get('nav', [])
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
        print(f"An unexpected error occurred while loading {nav_file_path}: {e}")
        exit()

    output_dir = 'public/data'
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n--- Starting All Scrapes with Time-based Conditional Update ---")
    
    total_changed_files = 0
    
    for ticker, info in all_tickers_info.items():
        file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
        
        existing_data = None
        last_update_time = None
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    update_str = existing_data.get('tickerInfo', {}).get('Update', '')
                    if update_str:
                        # KST 정보를 제거하고 파싱해야 함
                        last_update_time = datetime.strptime(update_str.replace(' KST', ''), '%Y-%m-%d %H:%M:%S')
                    # print(f"  -> Found existing data for {ticker}. Last update: {update_str}")
            except Exception as e:
                print(f"  -> Warning: Could not read existing file for {ticker}. Error: {e}")
        
        from datetime import timezone
        now_kst = datetime.now(timezone(timedelta(hours=9)))
        
        should_update_ticker_info = True
        if last_update_time:
            # 시간대 정보가 없는 naive datetime 끼리 비교
            if now_kst.replace(tzinfo=None) - last_update_time < timedelta(hours=23):
                should_update_ticker_info = False
                # print(f"  -> Ticker info for {ticker} was updated recently. Skipping info update.")

        new_scraped_data = scrape_with_yfinance(ticker, info['company'], info['frequency'], info['group'])
        if not new_scraped_data: continue

        if should_update_ticker_info:
            final_ticker_info = new_scraped_data.get('tickerInfo', {})
        else:
            final_ticker_info = existing_data.get('tickerInfo', {}) if existing_data else {}
        
        new_dividend_history = new_scraped_data.get('dividendHistory', [])
        has_history_changed = False
        
        if not existing_data or not existing_data.get('dividendHistory'):
            final_history = new_dividend_history
            if final_history: has_history_changed = True
        else:
            final_history = existing_data.get('dividendHistory', [])
            existing_dates = {item['배당락일'] for item in final_history}
            new_entries_to_add = [item for item in new_dividend_history if item['배당락일'] not in existing_dates]
            
            if new_entries_to_add:
                has_history_changed = True
                print(f"  -> Found {len(new_entries_to_add)} new dividend entries for {ticker}.")
                final_history.extend(new_entries_to_add)

            enriched_count = 0
            new_dividends_map = {item['배당락일']: item for item in new_dividend_history}
            for item in final_history:
                if item.get('배당락전일종가', 'N/A') == 'N/A' and item['배당락일'] in new_dividends_map:
                    new_info_item = new_dividends_map[item['배당락일']]
                    item.update({
                        '배당락전일종가': new_info_item.get('배당락전일종가', 'N/A'),
                        '배당락일종가': new_info_item.get('배당락일종가', 'N/A'),
                    })
                    has_history_changed = True
                    enriched_count += 1
            if enriched_count > 0:
                print(f"  -> Enriched {enriched_count} entries with price data for {ticker}.")
        
        if should_update_ticker_info or has_history_changed:
            final_history.sort(key=lambda x: datetime.strptime(x['배당락일'], '%y. %m. %d'), reverse=True)
            final_data_to_save = {"tickerInfo": final_ticker_info, "dividendHistory": final_history}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
            print(f" => UPDATED and saved data for {ticker} to {file_path}")
            total_changed_files += 1
        # else:
        #     print(f"  -> No changes detected for {ticker}. Skipping file write.")
            
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")
    print(f"Total files updated: {total_changed_files}")