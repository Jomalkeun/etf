import time
import json
import os
import yfinance as yf
from datetime import datetime

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

# --- yfinance 전용 범용 스크래퍼 (날짜 형식 YY. MM. DD 로 변경) ---
def scrape_with_yfinance(ticker_symbol, company, frequency):
    """
    yfinance API를 사용해 티커 정보를 가져오고, 두 가지 날짜 형식을 포함하여 반환합니다.
    """
    print(f"Scraping {ticker_symbol.upper()} (Company: {company}) using yfinance API...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        now_utc = datetime.utcnow()
        now_kst = now_utc + timedelta(hours=9)
        update_time_str = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')

        ticker_info = {
            "티커": ticker_symbol.upper(), "운용사": company, "지급주기": frequency,
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
    
# --- 3. 메인 실행 로직 (초단순화 버전) ---
# --- 메인 실행 로직 (증분 업데이트 적용 최종 버전) ---
if __name__ == "__main__":
    
    # 형식: '티커': {'company': '운용사 이름', 'frequency': '지급 주기'}
    all_tickers_info = {
        # Roundhill
        "XDTE": {"company": "Roundhill", "frequency": "Weekly"},
        "QDTE": {"company": "Roundhill", "frequency": "Weekly"},
        "RDTE": {"company": "Roundhill", "frequency": "Weekly"},
        "XPAY": {"company": "Roundhill", "frequency": "Monthly"},
        "YBTC": {"company": "Roundhill", "frequency": "Weekly"},
        "YETH": {"company": "Roundhill", "frequency": "Weekly"},
        "WEEK": {"company": "Roundhill", "frequency": "Weekly"},
        "MAGY": {"company": "Roundhill", "frequency": "Weekly"},
        "AAPW": {"company": "Roundhill", "frequency": "Weekly"},
        "AMZW": {"company": "Roundhill", "frequency": "Weekly"},
        "BRKW": {"company": "Roundhill", "frequency": "Weekly"},
        "COIW": {"company": "Roundhill", "frequency": "Weekly"},
        "HOOW": {"company": "Roundhill", "frequency": "Weekly"},
        "METW": {"company": "Roundhill", "frequency": "Weekly"},
        "NFLW": {"company": "Roundhill", "frequency": "Weekly"},
        "NVDW": {"company": "Roundhill", "frequency": "Weekly"},
        "PLTW": {"company": "Roundhill", "frequency": "Weekly"},
        "TSLW": {"company": "Roundhill", "frequency": "Weekly"},

        # YieldMax
        "CHPY": {"company": "YieldMax", "frequency": "Weekly"},
        "GPTY": {"company": "YieldMax", "frequency": "Weekly"},
        "LFGY": {"company": "YieldMax", "frequency": "Weekly"},
        "QDTY": {"company": "YieldMax", "frequency": "Weekly"},
        "RDTY": {"company": "YieldMax", "frequency": "Weekly"},
        "SDTY": {"company": "YieldMax", "frequency": "Weekly"},
        "ULTY": {"company": "YieldMax", "frequency": "Weekly"},
        "YMAG": {"company": "YieldMax", "frequency": "Weekly"},
        "YMAX": {"company": "YieldMax", "frequency": "Weekly"},

        "TSLY": {"company": "YieldMax", "frequency": "GroupA"},
        "OARK": {"company": "YieldMax", "frequency": "GroupA"},
        "BRKC": {"company": "YieldMax", "frequency": "GroupA"},
        "CRSH": {"company": "YieldMax", "frequency": "GroupA"},
        "FEAT": {"company": "YieldMax", "frequency": "GroupA"},
        "GOOY": {"company": "YieldMax", "frequency": "GroupA"},
        "SNOY": {"company": "YieldMax", "frequency": "GroupA"},
        "TSMY": {"company": "YieldMax", "frequency": "GroupA"},
        "XOMO": {"company": "YieldMax", "frequency": "GroupA"},
        "YBIT": {"company": "YieldMax", "frequency": "GroupA"},

        "BABO": {"company": "YieldMax", "frequency": "GroupB"},
        "DIPS": {"company": "YieldMax", "frequency": "GroupB"},
        "FBY": {"company": "YieldMax", "frequency": "GroupB"},
        "GDXY": {"company": "YieldMax", "frequency": "GroupB"},
        "JPMO": {"company": "YieldMax", "frequency": "GroupB"},
        "MARO": {"company": "YieldMax", "frequency": "GroupB"},
        "MRNY": {"company": "YieldMax", "frequency": "GroupB"},
        "NVDY": {"company": "YieldMax", "frequency": "GroupB"},
        "PLTY": {"company": "YieldMax", "frequency": "GroupB"},

        "ABNY": {"company": "YieldMax", "frequency": "GroupC"},
        "AMDY": {"company": "YieldMax", "frequency": "GroupC"},
        "CONY": {"company": "YieldMax", "frequency": "GroupC"},
        "CVNY": {"company": "YieldMax", "frequency": "GroupC"},
        "FIAT": {"company": "YieldMax", "frequency": "GroupC"},
        "HOOY": {"company": "YieldMax", "frequency": "GroupC"},
        "MSFO": {"company": "YieldMax", "frequency": "GroupC"},
        "NFLY": {"company": "YieldMax", "frequency": "GroupC"},
        "PYPY": {"company": "YieldMax", "frequency": "GroupC"},

        "AIYY": {"company": "YieldMax", "frequency": "GroupD"},
        "AMZY": {"company": "YieldMax", "frequency": "GroupD"},
        "APLY": {"company": "YieldMax", "frequency": "GroupD"},
        "DISO": {"company": "YieldMax", "frequency": "GroupD"},
        "MSTY": {"company": "YieldMax", "frequency": "GroupD"},
        "SMCY": {"company": "YieldMax", "frequency": "GroupD"},
        "WNTR": {"company": "YieldMax", "frequency": "GroupD"},
        "XYZY": {"company": "YieldMax", "frequency": "GroupD"},
        "YQQQ": {"company": "YieldMax", "frequency": "GroupD"},

        # JPMorgan
        "JEPI": {"company": "J.P. Morgan", "frequency": "Monthly"},
        "JEPQ": {"company": "J.P. Morgan", "frequency": "Monthly"},
        "JFLI": {"company": "J.P. Morgan", "frequency": "Monthly"},

        
        # 슈왑
        "SCHD": {"company": "Schwab", "frequency": "Quarterly"},

        # Defiance
        "QQQY": {"company": "Defiance", "frequency": "Weekly"},
        "WDTE": {"company": "Defiance", "frequency": "Weekly"},
        "IWMY": {"company": "Defiance", "frequency": "Weekly"},
        "USOY": {"company": "Defiance", "frequency": "Weekly"},
        "GLDY": {"company": "Defiance", "frequency": "Weekly"},
        "MST": {"company": "Defiance", "frequency": "Weekly"},
        "SPYT": {"company": "Defiance", "frequency": "Monthly"},
        "QQQT": {"company": "Defiance", "frequency": "Monthly"},

        # Rex
        "COII": {"company": "Rex", "frequency": "Weekly"},
        "MSII": {"company": "Rex", "frequency": "Weekly"},
        "NVII": {"company": "Rex", "frequency": "Weekly"},
        "TSII": {"company": "Rex", "frequency": "Weekly"},
        
        #GraniteShares
        "XBTY": {"company": "GraniteShares", "frequency": "Weekly"},
        "NVYY": {"company": "GraniteShares", "frequency": "Weekly"},
        "TQQY": {"company": "GraniteShares", "frequency": "Weekly"},
        "YSPY": {"company": "GraniteShares", "frequency": "Weekly"},
        "TSYY": {"company": "GraniteShares", "frequency": "Weekly"},
    }
    
    output_dir = 'public/data'
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n--- Starting All Scrapes with Data Enrichment and Incremental Update ---")
    
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

        new_scraped_data = scrape_with_yfinance(ticker, info['company'], info['frequency'])
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

                old_timestamp = old_item.get('배당락일_ts')
                if not old_timestamp:
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

        # 최종 저장 전, 정렬 및 불필요한 필드 제거
        final_history.sort(key=lambda x: x.get('배당락일_ts', 0), reverse=True)
        for item in final_history:
            item.pop('배당락일_ts', None)

        final_data_to_save = {
            "tickerInfo": new_ticker_info,
            "dividendHistory": final_history
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
        print(f" => Processed and saved data for {ticker} to {file_path}")
        
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")