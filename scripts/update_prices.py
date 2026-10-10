"""매일 시세 갱신: 해외주식(Yahoo → Stooq 대체), 업비트 코인(원화), 환율 → data/prices.json
표준 라이브러리만 사용. 실패한 항목은 이전 값을 유지한다."""
import csv, io, json, os, urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (money-calendar price bot)"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "prices.json")
WATCH = os.path.join(ROOT, "data", "watchlist.json")


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def yahoo(sym):
    j = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"))
    meta = j["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice") or meta.get("previousClose")
    t = meta.get("regularMarketTime")
    return {"price": round(float(price), 4), "currency": meta.get("currency", "USD"),
            "asOf": datetime.fromtimestamp(t, KST).strftime("%Y-%m-%d") if t else None, "src": "yahoo"}


def stooq(sym):
    s = sym.lower() if "." in sym else sym.lower() + ".us"
    rows = list(csv.DictReader(io.StringIO(get(f"https://stooq.com/q/l/?s={s}&f=sd2t2ohlcv&h&e=csv").decode())))
    close = rows[0].get("Close")
    if not close or close == "N/D":
        raise ValueError("no data")
    return {"price": round(float(close), 4), "currency": "USD", "asOf": rows[0].get("Date"), "src": "stooq"}


def upbit(codes):
    if not codes:
        return {}
    mk = ",".join(f"KRW-{c}" for c in codes)
    data = json.loads(get(f"https://api.upbit.com/v1/ticker?markets={mk}"))
    return {f"CRYPTO:{d['market'].split('-')[1]}": {"price": float(d["trade_price"]), "currency": "KRW",
            "asOf": datetime.now(KST).strftime("%Y-%m-%d"), "src": "upbit"} for d in data}


def fx():
    # open.er-api.com: 무료, 키 불필요. KRW 기준 환율을 받아 1단위당 원화로 뒤집는다.
    try:
        j = json.loads(get("https://open.er-api.com/v6/latest/KRW"))
        r = j["rates"]
        return {c: round(1 / r[c], 4) for c in ["USD", "JPY", "CNY", "EUR", "GBP"] if r.get(c)}
    except Exception as e:
        print("fx er-api failed:", e)
    try:  # 대체: ECB 기준환율(유로 기준)으로 교차 계산
        r = json.loads(get("https://api.frankfurter.dev/v1/latest?from=EUR&to=KRW,USD,JPY,CNY,GBP"))["rates"]
        out = {"EUR": round(r["KRW"], 4)}
        for c in ["USD", "JPY", "CNY", "GBP"]:
            out[c] = round(r["KRW"] / r[c], 4)
        return out
    except Exception as e:
        print("fx frankfurter failed:", e)
    out = {}
    return out


def main():
    prev = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            prev = json.load(f)
    with open(WATCH, encoding="utf-8") as f:
        w = json.load(f)
    quotes = dict(prev.get("quotes", {}))
    for sym in w.get("stocks", []):
        sym = sym.strip().upper()
        for fn in (yahoo, stooq):
            try:
                quotes[sym] = fn(sym)
                break
            except Exception as e:
                print(f"{fn.__name__} {sym} failed: {e}")
    try:
        quotes.update(upbit([c.strip().upper() for c in w.get("crypto", [])]))
    except Exception as e:
        print("upbit failed:", e)
    rates = fx() or prev.get("fx", {})
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), "fx": {**prev.get("fx", {}), **rates}, "quotes": quotes}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False)[:800])


if __name__ == "__main__":
    main()
