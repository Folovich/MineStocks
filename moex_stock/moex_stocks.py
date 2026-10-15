import json, socket, struct, time, urllib.request, os
from pathlib import Path
from datetime import datetime

BASE = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities"

# Пишете бирживой тикер для добавления.
TICKERS = {"SBER":"Сбер", "GAZP":"Газпром", "YDEX":"Яндекс", "OZON":"Ozon", "T":"Т-Технологии",
    "GMKN":"Норникель", "LKOH":"Лукойл","ROSN":"Роснефть", "SIBN":"Газпром-нефть"}

RCON_HOST, RCON_PORT = "127.0.0.1", 25575
RCON_PASSWORD = os.environ.get("RCONS_PASSWORD")
POLL_SECONDS = 60

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

def packet(sock, rid, typ, payload):
    body = struct.pack("<ii", rid, typ) + payload.encode() + b"\x00\x00"
    sock.sendall(struct.pack("<i", len(body)) + body)
    size = struct.unpack("<i", sock.recv(4))[0]
    data = b""
    while len(data) < size:
        data += sock.recv(size-len(data))
    return struct.unpack("<ii", data[:8])[0], data[8:-2].decode(errors="replace")

def command(cmd):
    with socket.create_connection((RCON_HOST, RCON_PORT), timeout=5) as s:
        s.settimeout(5)
        rid, _ = packet(s, 1, 3, RCON_PASSWORD)
        if rid == -1: raise RuntimeError("RCON password rejected")
        return packet(s, 2, 2, cmd)[1]

def price(ticker):
    url = f"{BASE}/{ticker}.json?iss.meta=off&iss.only=marketdata&marketdata.columns=SECID,LAST,LCURRENTPRICE,UPDATETIME"
    req = urllib.request.Request(url, headers={"User-Agent":"RFStocksMinecraft/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r: data = json.load(r)
    block = data.get("marketdata", {})
    rows, cols = block.get("data", []), block.get("columns", [])
    if not rows: raise RuntimeError("MOEX returned no market data")
    row = dict(zip(cols, rows[0]))
    value = row.get("LAST")
    if value is None: value = row.get("LCURRENTPRICE")
    if value is None: raise RuntimeError("No last price")
    return float(value), row.get("UPDATETIME")
def different(ticker):
    url = f"{BASE}/{ticker}.json?iss.meta=off&iss.only=marketdata&marketdata.columns=OPEN"
    req = urllib.request.Request(url, headers={"User-Agent":"RFStocksMinecraft/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r: data = json.load(r)
    block = data.get("marketdata", {})
    rows, cols = block.get("data", []), block.get("columns", [])
    if not rows: raise RuntimeError("MOEX returned no market data")
    row = dict(zip(cols, rows[0]))
    value = row.get("OPEN")
    if value is None: value = row.get("LCURRENTPRICE")
    if value is None: raise RuntimeError("No last price")
    return float(value)
def main():
    print("MOEX ISS -> Minecraft scoreboard. Ctrl+C to stop.")
    try: command("scoreboard objectives add stocks_price dummy")
    except Exception: pass
    while True:
        snapshot = {"checked_at":datetime.now().astimezone().isoformat(timespec="seconds"), "companies":{}}
        for ticker, name in TICKERS.items():
            try:
                value, market_time = price(ticker)
                scaled = round(value * 100)
                price_text = f"{value:.2f}"
                startPrice = different(ticker)
                pro = ((value - startPrice) / startPrice) * 100
                if (pro == 0):
                    command(
                    f'tellraw @a {json.dumps({"text": f"{name}: {price_text} ₽ ▲ {pro:.2f}% ▲ ", "color": "white"}, ensure_ascii=False)}'
                    )
                elif(pro > 0):
                    command(
                    f'tellraw @a {json.dumps({"text": f"{name}: {price_text} ₽ ▲ {pro:.2f}% ▲ ", "color": "green"}, ensure_ascii=False)}'
                    )
                else:
                    command(
                    f'tellraw @a {json.dumps({"text": f"{name}: {price_text} ₽ ▼ {pro:.2f}% ▼ ", "color": "red"}, ensure_ascii=False)}'
                    )
                snapshot["companies"][ticker] = {"name":name,"price":value,"scaled_price":scaled,"market_time":market_time,"status":"ok"}
                print(f"{name} {ticker}: {value:.2f} ₽; market time {market_time}")
            except Exception as e:
                snapshot["companies"][ticker] = {"name":name,"status":"error","error":str(e)}
                print(f"{name}: {e}")
        command(
        f'tellraw @a {json.dumps({"text": f"-----", "color": "gold"}, ensure_ascii=False)}'
        )
        tmp = OUT / "quotes.tmp"
        tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(OUT / "quotes.json")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("Stopped.")