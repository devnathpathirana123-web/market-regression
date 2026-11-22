# S&P 500 regression backtest

An educational linear regression model for three-month S&P 500 price returns. It uses rates, inflation, industrial production, unemployment, the broad dollar index, and real consumer spending.

Open `market_backtest.html` in a browser to explore the historical forecasts. Move the slider to compare the actual return, regression forecast, and historical-average forecast for any month. The ±8% lines mark the boom and bust thresholds used in this example.

Run the model with Python 3 from the repository directory.

```sh
python3 market_regression.py --cache-dir fred_data
```

The first run downloads public series from FRED. Subsequent runs reuse the cache. The chart is a snapshot of the November 2026 analysis. FRED updates and revises data, so a fresh download may change results.

The regression's mean absolute error was 6.30 percentage points across 54 walk-forward forecasts. The historical-average baseline scored 5.24 percentage points. The regression missed all three busts and all 12 booms. Macroeconomic observations were lagged by two months, and the data may contain historical revisions.
