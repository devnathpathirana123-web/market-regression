# S&P 500 regression backtest

An educational linear regression model for three-month S&P 500 price returns. It uses rates, inflation, industrial production, unemployment, the broad dollar index, and real consumer spending.

Open `market_backtest.html` in a browser to explore the historical forecasts. Move the slider to compare the actual return, regression forecast, and historical-average forecast for any month. The ±8% lines mark the boom and bust thresholds used in this example.

Run the model with Python 3 from the repository directory.

```sh
python3 market_regression.py --cache-dir fred_data
```

The first run downloads public series from FRED. Subsequent runs reuse the cache. The chart is a snapshot of the November 2026 analysis. FRED updates and revises data, so a fresh download may change results.

The regression's mean absolute error was 6.30 percentage points across 54 walk-forward forecasts. The historical-average baseline scored 5.24 percentage points. The regression missed all three busts and all 12 booms. Macroeconomic observations were lagged by two months, and the data may contain historical revisions.


## Run from a fresh checkout

```sh
git clone https://github.com/devnathpathirana123-web/market-regression.git
cd market-regression
python3 market_regression.py --cache-dir fred_data
```

Python's standard library is sufficient. The first run needs internet access to FRED. Repeat the command from the same directory to reuse the downloaded data. Use a new cache directory to fetch fresh observations. Add `--as-of YYYY-MM-DD` to exclude the named month and every later month. This date filter uses the series available in your cache and does not retrieve historical data vintages.

## How the model learns

- **Inputs.** Fed funds and unemployment rates, plus year-over-year changes in consumer prices, industrial production, the broad dollar index, and real consumer spending.
- **Target.** The S&P 500 price return from this month's last trading close to the last trading close three months later.
- **Training.** Standardize the features within each training window and use gradient descent to minimize squared return errors.
- **Testing.** Walk forward one forecast month at a time. Each fit only uses training targets whose three-month outcome is already known. The historical mean uses the same training window.
- **Signals.** A predicted return of at least +8% is a boom, and a return of −8% or lower is a bust. Values between those thresholds are neutral.

To view the historical snapshot, download [market_backtest.html](market_backtest.html) and open it in a browser. Move the slider to inspect an individual forecast. Running the Python script prints a new backtest in the terminal.

## React dashboard and Python API

See the [dashboard setup guide](dashboard/README.md) for local development and container deployment.
