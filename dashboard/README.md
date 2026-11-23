# Market Regression Lab

React and Vite display a walk-forward S&P 500 backtest. The Python API runs the existing linear regression and returns the results as JSON at `GET /api/backtest`.

From the repository root, using Node.js 20+ and Python 3:

```sh
npm --prefix dashboard ci
npm --prefix dashboard run build
python3 dashboard/api.py
```

Open http://127.0.0.1:8000. On the first API request the server fetches public FRED observations. To reuse existing CSV files, set `FRED_CACHE` to their folder. Set `BACKTEST_AS_OF=YYYY-MM-DD` to exclude that month and later months. The server caches one computed backtest in memory until restarted.

For frontend development, keep the Python server running and use `npm --prefix dashboard run dev` in a second terminal. Vite proxies API requests to port 8000.

The deployment requires a Python runtime. Build the frontend and serve it from the same origin as the API. Set `PORT` and run `python3 dashboard/api.py --host 0.0.0.0` behind a production reverse proxy.

For container hosting, build from the repository root with `docker build -f dashboard/Dockerfile -t market-regression .`, then run `docker run --rm -p 8000:8000 market-regression`. The container needs outbound HTTPS access for FRED.
