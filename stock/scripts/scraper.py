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

# --- 2. yfinance 전용 범용 스크래퍼 (상세 정보 추가 버전, Update 시간 추가) ---
def scrape_with_yfinance(ticker_symbol, company, frequency):
    """
    yfinance API를 사용해 티커의 상세 정보와 배당 기록을 모두 가져옵니다.
    'Update 시간' 필드를 추가합니다.
    """
    print(f"Scraping {ticker_symbol.upper()} (Company: {company}) using yfinance API...")
    try:
        # 1. Ticker 객체 및 상세 정보 가져오기
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 2. 필요한 정보 추출 및 기본값 설정
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
        fifty_two_week_range = f"${fifty_two_week_low:.2f} - ${fifty_two_week_high:.2f}" if fifty_two_week_low and fifty_two_week_high else "N/A"
        
        volume = info.get('volume', 0)
        avg_volume = info.get('averageVolume', 0)
        nav = info.get('navPrice', 0)
        yield_val = info.get('trailingAnnualDividendYield') or info.get('yield') or info.get('dividendYield') or 0
        ytd_return = info.get('ytdReturn', 0)

        # --- 바로 여기가 핵심 수정 부분입니다! ---
        # 3. 현재 시간을 가져와 보기 좋은 형식의 문자열로 만듭니다.
        #    (한국 시간 기준)
        now_utc = datetime.utcnow()
        now_kst = now_utc + timedelta(hours=9)
        update_time_str = now_kst.strftime('%Y-%m-%d %H:%M:%S KST')

        # 4. tickerInfo 객체에 'Update 시간' 필드 추가
        ticker_info = {
            "티커": ticker_symbol.upper(),
            "운용사": company,
            "지급주기": frequency,
            "Update 시간": update_time_str, # <--- 추가된 필드!
            "52 Week Range": fifty_two_week_range,
            "Volume": f"{volume:,}" if volume else "N/A",
            "Avg. Volume": f"{avg_volume:,}" if avg_volume else "N/A",
            "NAV": f"${nav:.2f}" if nav else "N/A",
            "Yield": f"{(yield_val * 100):.2f}%" if yield_val else "N/A",
            "YTD Daily Total Return": f"{(ytd_return * 100):.2f}%" if ytd_return else "N/A",
        }
        
        # --- 배당 기록 가져오는 부분 (이전과 동일) ---
        dividends_df = ticker.dividends.to_frame()
        dividend_history = []
        if not dividends_df.empty:
            dividends_df = dividends_df.reset_index()
            dividends_df.columns = ['ExDate', 'Dividend']
            dividends_df = dividends_df.sort_values(by='ExDate', ascending=False)
            
            for index, row in dividends_df.head(24).iterrows():
                ex_date = row['ExDate'].to_pydatetime()
                ex_date_str_mdy = ex_date.strftime('%m/%d/%Y')
                dividend_amount = row['Dividend']
                
                prices = get_historical_prices(ticker_symbol, ex_date_str_mdy)
                
                record = {
                    '배당락일': ex_date_str_mdy,
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
    
    print("\n--- Starting All Scrapes (yfinance API only) ---")
    
    for ticker, info in all_tickers_info.items():
        # 이제 함수는 새로운 구조의 데이터를 반환합니다.
        data = scrape_with_yfinance(ticker, info['company'], info['frequency'])
        
        # 데이터가 정상적으로 생성되었을 때만 파일로 저장
        if data:
            file_path = os.path.join(output_dir, f"{ticker.lower()}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f" => Saved structured data for {ticker} to {file_path}")
            
        time.sleep(1)

    print("\n--- ALL TASKS FINISHED ---")
    print("All ETF data scraped and saved with the new structure.")