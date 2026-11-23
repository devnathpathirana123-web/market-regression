"""Serve the regression API and the built Vite dashboard."""
import argparse
import json
import os
import sys
from datetime import date
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import mean
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import market_regression as model


@lru_cache(maxsize=1)
def run_backtest():
    cache = Path(os.environ.get("FRED_CACHE", HERE / "fred_data"))
    cutoff = date.fromisoformat(os.environ.get("BACKTEST_AS_OF", date.today().isoformat())).replace(day=1)
    prices = model.load_series("SP500", cutoff, cache)
    macro = {key: model.load_series(key, cutoff, cache) for key in model.FEATURES}
    rows = model.make_rows(prices, macro)
    known = [row for row in rows if row[2] is not None]
    scores = model.backtest(known)
    if not scores:
        raise ValueError("Insufficient aligned history for the backtest")
    month, inputs, _ = rows[-1]
    fit = model.fit([row for row in known if row[0] + model.HORIZON <= month])
    forecast = model.predict(inputs, *fit)
    return {
        "threshold": model.THRESHOLD,
        "horizon": model.HORIZON,
        "rows": [{"month": model.month_name(m), "actual": a, "prediction": p, "baseline": b,
                  "actualLabel": model.label(a), "predictionLabel": model.label(p)}
                 for m, a, p, b in scores],
        "mae": mean(abs(a - p) for _, a, p, _ in scores),
        "baselineMae": mean(abs(a - b) for _, a, _, b in scores),
        "forecast": {"origin": model.month_name(month), "end": model.month_name(month + model.HORIZON),
                     "return": forecast, "label": model.label(forecast)},
        "weights": [{"name": name, "weight": weight}
                    for name, weight in zip(model.FEATURES.values(), fit[3])],
    }


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path != "/api/backtest":
            return super().do_GET()
        try:
            self.send_json(200, run_backtest())
        except (OSError, ValueError, KeyError) as exc:
            self.log_error("Backtest failed: %s", exc)
            self.send_json(503, {"error": "Backtest unavailable. Check the FRED connection or data cache."})

    def send_json(self, status, payload):
        body = json.dumps(payload, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), partial(Handler, directory=HERE / "dist")) as server:
        print(f"Dashboard API at http://{args.host}:{server.server_port}", flush=True)
        server.serve_forever()
