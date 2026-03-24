from fastapi import FastAPI, Query
from datetime import datetime
import yfinance as yf

app = FastAPI()

S3P_SECTORS = {
    "technology":             "XLK",
    "financials":             "XLF",
    "healthcare":             "XLV",
    "energy":                 "XLE",
    "consumer_discretionary": "XLY",
}

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/stocks")
def get_stocks(tickers: str = Query(..., description="Comma-separated tickers")):
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    result = []
    for ticker in ticker_list:
        try:
            info = yf.Ticker(ticker).fast_info
            result.append({
                "ticker":     ticker,
                "price":      round(info.last_price, 4),
                "prev_close": round(info.previous_close, 4),
                "pct_change": round((info.last_price - info.previous_close) / info.previous_close * 100, 2),
                "volume":     info.three_month_average_volume,
                "day_volume": info.last_volume,
                "52w_high":   round(info.year_high, 4),
                "52w_low":    round(info.year_low, 4),
                "market_cap": info.market_cap,
            })
        except Exception as e:
            result.append({"ticker": ticker, "error": str(e)})
    return {"stocks": result, "count": len(result)}

@app.get("/top-movers")
def get_top_movers(sector_etf: str = Query(...), count: int = 8):
    try:
        holdings = yf.Ticker(sector_etf).holdings
        tickers = list(holdings.index[:30]) if holdings is not None else []
        movers = []
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                pct = (info.last_price - info.previous_close) / info.previous_close * 100
                movers.append({
                    "ticker":     ticker,
                    "price":      round(info.last_price, 4),
                    "pct_change": round(pct, 2),
                    "volume":     info.last_volume,
                })
            except:
                pass
        movers.sort(key=lambda x: abs(x.get("pct_change", 0)), reverse=True)
        return {"sector_etf": sector_etf, "top_movers": movers[:count]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/earnings-upcoming")
def get_earnings_upcoming(days: int = 3):
    return {"earnings_upcoming": [], "note": "Earnings calendar integration pending"}

@app.get("/sector-etfs")
def get_sector_etfs():
    result = []
    for sector, etf in S3P_SECTORS.items():
        try:
            info = yf.Ticker(etf).fast_info
            result.append({
                "sector":     sector,
                "etf":        etf,
                "price":      round(info.last_price, 4),
                "pct_change": round((info.last_price - info.previous_close) / info.previous_close * 100, 2),
            })
        except Exception as e:
            result.append({"sector": sector, "etf": etf, "error": str(e)})
    return {"sector_etfs": result}

@app.get("/history")
def get_history(ticker: str, period: str = "5d"):
    try:
        df = yf.Ticker(ticker.upper()).history(period=period)
        records = []
        for date, row in df.iterrows():
            records.append({
                "date":   date.strftime("%Y-%m-%d"),
                "close":  round(row["Close"], 4),
                "volume": int(row["Volume"]),
            })
        return {"ticker": ticker.upper(), "history": records}
    except Exception as e:
        return {"error": str(e)}
