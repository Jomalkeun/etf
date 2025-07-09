import time
import json
import os
import yfinance as yf
from datetime import datetime, timedelta

def get_historical_prices(ticker_symbol, ex_date_str):
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

# --- 2. yfinance 전용 범용 스크래퍼 ---
def scrape_with_yfinance(ticker_symbol, company, frequency, group):
    print(f"Scraping {ticker_symbol.upper()} (Group: {group}) using yfinance API...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        now_utc = datetime.utcnow()
        now_kst = now_utc + timedelta(hours=9)
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
    
# --- 3. 메인 실행 로직 (nav.json 실제 구조에 맞춤) ---
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
        print(f"An unexpected error occurred while loading {nav_file_path}: {e}")
        exit()

    output_dir = 'public/data'
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n--- Starting All Scrapes based on nav.json with Conditional Update ---")
    
    total_changed_files = 0
    
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
        
        has_changed = False
        
        if not existing_data:
            final_data_to_save = new_scraped_data
            if new_scraped_data.get('dividendHistory'):
                has_changed = True
            print(f"  -> No existing data. Creating new file for {ticker}.")
        else:
            final_history = existing_data.get('dividendHistory', [])
            
            existing_ticker_info_for_compare = existing_data.get('tickerInfo', {}).copy()
            existing_ticker_info_for_compare.pop('Update', None)
            new_ticker_info_for_compare = new_ticker_info.copy()
            new_ticker_info_for_compare.pop('Update', None)
            if new_ticker_info_for_compare != existing_ticker_info_for_compare:
                has_changed = True
                print(f"  -> Ticker info for {ticker} has changed.")

            existing_dates = {item['배당락일'] for item in final_history}
            new_entries_to_add = [
                item for item in new_dividend_history 
                if item['배당락일'] not in existing_dates
            ]
            if new_entries_to_add:
                has_changed = True
                print(f"  -> Found {len(new_entries_to_add)} new dividend entries for {ticker}.")
                final_history.extend(new_entries_to_add)

            enriched_items_count = 0
            new_dividends_map = {item['배당락일']: item for item in new_dividend_history}
            for item in final_history:
                if item.get('배당락전일종가', 'N/A') == 'N/A' and item['배당락일'] in new_dividends_map:
                    new_info_item = new_dividends_map[item['배당락일']]
                    item.update({
                        '배당락전일종가': new_info_item.get('배당락전일종가', 'N/A'),
                        '배당락일종가': new_info_item.get('배당락일종가', 'N/A'),
                    })
                    has_changed = True
                    enriched_items_count += 1
            if enriched_items_count > 0:
                print(f"  -> Enriched {enriched_items_count} existing entries with price data for {ticker}.")
            
            final_history.sort(key=lambda x: datetime.strptime(x['배당락일'], '%y. %m. %d'), reverse=True)
            final_data_to_save = {
                "tickerInfo": new_ticker_info,
                "dividendHistory": final_history
            }
        
        if has_changed:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
            print(f" => UPDATED and saved data for {ticker} to {file_path}")
            total_changed_files += 1
        else:
            print(f"  -> No changes detected for {ticker}. Skipping file write.")
            
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")
    print(f"Total files updated: {total_changed_files}")