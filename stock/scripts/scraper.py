import time
import json
import os
import yfinance as yf
from datetime import datetime, timedelta

# --- 1. 주가 조회 헬퍼 함수 (수정 없음) ---
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

# --- yfinance 전용 범용 스크래퍼 (날짜 형식 YY. MM. DD. 로 변경) ---
def scrape_with_yfinance(ticker_symbol, company, frequency):
    """
    yfinance API를 사용해 티커의 모든 정보를 가져오고,
    날짜 형식을 'YY. MM. DD.'로 통일하여 반환합니다.
    """
    print(f"Scraping {ticker_symbol.upper()} (Company: {company}) using yfinance API...")
    try:
        # 1. Ticker 객체 및 상세 정보 가져오기
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 2. Update 시간 생성
        now_utc = datetime.utcnow()
        now_kst = now_utc + timedelta(hours=9)
        update_time_str = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')

        # 3. tickerInfo 객체 생성
        ticker_info = {
            "티커": ticker_symbol.upper(),
            "운용사": company,
            "지급주기": frequency,
            "Update": update_time_str,
            "52Week": f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}" if info.get('fiftyTwoWeekLow') else "N/A",
            "Volume": f"{info.get('volume', 0):,}",
            "AvgVolume": f"{info.get('averageVolume', 0):,}",
            "NAV": f"${info.get('navPrice', 0):.2f}" if info.get('navPrice') else "N/A",
            "Yield": f"{(info.get('trailingAnnualDividendYield', 0) * 100):.2f}%" if info.get('trailingAnnualDividendYield') else "N/A",
            "TotalReturn": f"{(info.get('ytdReturn', 0) * 100):.2f}%" if info.get('ytdReturn') else "N/A",
        }
        
        # --- 배당 기록 가져오는 부분 ---
        dividends_df = ticker.dividends.to_frame()
        dividend_history = []
        if not dividends_df.empty:
            dividends_df = dividends_df.reset_index()
            dividends_df.columns = ['ExDate', 'Dividend']
            dividends_df = dividends_df.sort_values(by='ExDate', ascending=False)
            
            for index, row in dividends_df.head(24).iterrows():
                ex_date = row['ExDate'].to_pydatetime()
                
                # 4. 원하는 형식의 날짜 문자열 생성
                ex_date_str_yy_mm_dd = ex_date.strftime('%y. %m. %d') # YY. MM. DD 형식
                ex_date_str_mdy = ex_date.strftime('%m/%d/%Y') # 주가 조회를 위한 기존 형식
                
                dividend_amount = row['Dividend']
                
                # 주가 조회는 기존의 MM/DD/YYYY 형식으로 호출
                prices = get_historical_prices(ticker_symbol, ex_date_str_mdy)
                
                record = {
                    # 최종 저장되는 날짜는 새로운 형식으로
                    '배당락일': ex_date_str_yy_mm_dd, 
                    '배당금': f"${dividend_amount:.4f}",
                    '배당락전일종가': prices['before_price'],
                    '배당락일종가': prices['on_price'],
                }
                dividend_history.append(record)
        
        # --- 최종 JSON 구조 생성 ---
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
    
    print("\n--- Starting All Scrapes with Incremental Update ---")
    
    for ticker, info in all_tickers_info.items():
        file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
        
        # --- 1. 기존 데이터 로드 및 최신 배당락일 확인 ---
        existing_data = None
        latest_existing_date = None
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # 기존 데이터의 dividendHistory에서 가장 최신 날짜를 찾음
                    if existing_data and existing_data.get('dividendHistory'):
                        history = existing_data['dividendHistory']
                        # 'YY. MM. DD.' 형식을 datetime으로 변환하여 비교
                        latest_existing_date = max(
                            datetime.strptime(d['배당락일'], '%y. %m. %d.') for d in history
                        )
                        print(f"  -> Found existing data for {ticker}. Latest date: {latest_existing_date.strftime('%y. %m. %d.')}")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"  -> Warning: Could not read existing file for {ticker}. Will overwrite. Error: {e}")
                existing_data = None
                latest_existing_date = None

        # --- 2. yfinance로 새로운 데이터 스크래핑 ---
        # scrape_with_yfinance는 이제 {'tickerInfo': {...}, 'dividendHistory': [...]} 구조를 반환
        new_scraped_data = scrape_with_yfinance(ticker, info['company'], info['frequency'])

        if not new_scraped_data:
            print(f"  -> No new data scraped for {ticker}. Skipping update.")
            continue

        # --- 3. 최신 데이터만 필터링 ---
        new_dividends_to_add = []
        if latest_existing_date:
            for new_dividend in new_scraped_data.get('dividendHistory', []):
                new_date = datetime.strptime(new_dividend['배당락일'], '%y. %m. %d.')
                # 새로 가져온 데이터가 기존의 최신 날짜보다 더 새로운 경우에만 추가
                if new_date > latest_existing_date:
                    new_dividends_to_add.append(new_dividend)
        else:
            # 기존 데이터가 없으면, 스크래핑한 모든 데이터를 사용
            new_dividends_to_add = new_scraped_data.get('dividendHistory', [])

        # --- 4. 데이터 병합 및 저장 ---
        if not new_dividends_to_add:
            print(f"  -> No new dividend entries to add for {ticker}.")
            # 새로운 배당 기록은 없지만, tickerInfo는 업데이트될 수 있으므로
            # 기존 dividendHistory와 새로운 tickerInfo를 합쳐서 저장
            if existing_data:
                final_data_to_save = {
                    "tickerInfo": new_scraped_data['tickerInfo'], # tickerInfo는 항상 최신으로
                    "dividendHistory": existing_data['dividendHistory']
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
                print(f" => Updated tickerInfo for {ticker} in {file_path}")

        else:
            print(f"  -> Found {len(new_dividends_to_add)} new dividend entries for {ticker}.")
            # 기존 데이터가 있으면, 새로운 기록을 기존 기록 앞에 추가
            if existing_data and existing_data.get('dividendHistory'):
                combined_history = new_dividends_to_add + existing_data['dividendHistory']
            else: # 기존 데이터가 없으면, 새로 찾은 것만 사용
                combined_history = new_dividends_to_add
            
            # 최종 데이터를 새로운 구조로 만듦
            final_data_to_save = {
                "tickerInfo": new_scraped_data['tickerInfo'], # tickerInfo는 항상 최신으로
                "dividendHistory": combined_history
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data_to_save, f, ensure_ascii=False, indent=2)
            print(f" => Merged and saved data for {ticker} to {file_path}")

        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")