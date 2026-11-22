"""Learn linear regression by forecasting three-month S&P 500 price returns.

Run: python3 market_regression.py
Optional: --cache-dir PATH reuses or saves downloaded FRED series.
Use a new cache directory to refresh data.
"""
import argparse
import csv
from datetime import date
from io import StringIO
from math import isfinite, sqrt
from pathlib import Path
from statistics import mean, pstdev
from urllib.request import urlopen

HORIZON = 3
THRESHOLD = 8.0
MIN_TRAIN = 60
FEATURES = {
    "FEDFUNDS": "Fed funds rate (%)",
    "CPIAUCSL": "Inflation (year-over-year %)",
    "INDPRO": "Industrial production (year-over-year %)",
    "UNRATE": "Unemployment rate (%)",
    "DTWEXBGS": "Broad dollar index (year-over-year %)",
    "PCEC96": "Real consumer spending (year-over-year %)",
}
LEVELS = {"FEDFUNDS", "UNRATE"}
LABELS = ("Bust", "Neutral", "Boom")


def load_series(series_id, cutoff, cache_dir):
    path = cache_dir / f"{series_id}.csv" if cache_dir else None
    if path and path.exists():
        content = path.read_text()
    else:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        with urlopen(url, timeout=30) as response:
            content = response.read().decode("utf-8-sig")
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    # FRED daily series become monthly by taking the final available close.
    # Monthly releases carry their observation month as the date.
    monthly = {}
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames or series_id not in reader.fieldnames:
        raise ValueError(f"Unexpected data format for {series_id}")
    date_column = reader.fieldnames[0]
    for row in sorted(reader, key=lambda row: row[date_column]):
        observed = date.fromisoformat(row[date_column])
        if observed.replace(day=1) >= cutoff or row[series_id] in ("", "."):
            continue
        value = float(row[series_id])
        if isfinite(value):
            monthly[observed.year * 12 + observed.month - 1] = value
    return monthly


def percent_change(new, old):
    return 100 * (new / old - 1)


def make_rows(prices, macro):
    rows = []
    for month in sorted(prices):
        # At month-end, use macro observations from two calendar months earlier.
        # This approximates release delays. Current-vintage data can be revised.
        observed = month - 2
        inputs = []
        for key, values in macro.items():
            if observed not in values:
                break
            if key in LEVELS:
                inputs.append(values[observed])
            elif observed - 12 in values:
                inputs.append(percent_change(values[observed], values[observed - 12]))
            else:
                break
        if len(inputs) == len(macro):
            future = prices.get(month + HORIZON)
            target = percent_change(future, prices[month]) if future is not None else None
            rows.append((month, inputs, target))
    return rows


def predict(inputs, means, scales, intercept, weights):
    standardized = [(x - center) / scale for x, center, scale in zip(inputs, means, scales)]
    return intercept + sum(weight * x for weight, x in zip(weights, standardized))


def fit(train):
    columns = list(zip(*(inputs for _, inputs, _ in train)))
    means = [mean(column) for column in columns]
    scales = [pstdev(column) or 1.0 for column in columns]
    targets = [target for _, _, target in train]
    intercept = mean(targets)
    centered_targets = [target - intercept for target in targets]
    standardized = [
        [(x - center) / scale for x, center, scale in zip(inputs, means, scales)]
        for _, inputs, _ in train
    ]
    weights = [0.0] * len(columns)
    # Minimize mean squared error. With centered inputs, the best intercept
    # equals the average training target throughout the optimization.
    for _ in range(1500):
        errors = [
            sum(w * x for w, x in zip(weights, row)) - target
            for row, target in zip(standardized, centered_targets)
        ]
        adjustments = [
            0.15 * sum(error * row[j] for error, row in zip(errors, standardized)) / len(train)
            for j in range(len(weights))
        ]
        weights = [weight - adjustment for weight, adjustment in zip(weights, adjustments)]
        if max(map(abs, adjustments)) < 1e-8:
            break
    return means, scales, intercept, weights


def label(value):
    if value >= THRESHOLD:
        return "Boom"
    if value <= -THRESHOLD:
        return "Bust"
    return "Neutral"


def month_name(month):
    year, month_index = divmod(month, 12)
    return f"{year:04d}-{month_index + 1:02d}"


def backtest(known):
    scores = []
    for month, inputs, actual in known:
        # At forecast time, train only on targets whose endpoint is already known.
        train = [row for row in known if row[0] + HORIZON <= month]
        if len(train) >= MIN_TRAIN:
            model = fit(train)
            scores.append((month, actual, predict(inputs, *model), model[2]))

    return scores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    cutoff = args.as_of.replace(day=1)
    prices = load_series("SP500", cutoff, args.cache_dir)
    macro = {key: load_series(key, cutoff, args.cache_dir) for key in FEATURES}
    rows = make_rows(prices, macro)
    if not rows:
        parser.error("No aligned market and macro data.")
    known = [row for row in rows if row[2] is not None]

    scores = backtest(known)

    if not scores:
        parser.error("Insufficient history for a walk-forward test.")
    print(f"Walk-forward test: {month_name(scores[0][0])} to {month_name(scores[-1][0])}"
          f" ({len(scores)} monthly forecasts)")
    for name, index in (("Regression", 2), ("Historical mean", 3)):
        errors = [row[index] - row[1] for row in scores]
        accuracy = mean(label(row[index]) == label(row[1]) for row in scores)
        print(f"{name:16} MAE {mean(map(abs, errors)):.2f} pp | "
              f"RMSE {sqrt(mean(error**2 for error in errors)):.2f} pp | "
              f"Label accuracy {accuracy:.1%}")

    print("\nRegression counts (rows: actual; columns: predicted)")
    print(f"{'':10}" + "".join(f"{item:>9}" for item in LABELS))
    for actual in LABELS:
        counts = [sum(label(row[1]) == actual and label(row[2]) == predicted for row in scores)
                  for predicted in LABELS]
        print(f"{actual:10}" + "".join(f"{count:9d}" for count in counts))

    month, inputs, _ = rows[-1]
    train = [row for row in known if row[0] + HORIZON <= month]
    model = fit(train)
    predicted = predict(inputs, *model)
    print(f"\nLast available origin {month_name(month)} → {month_name(month + HORIZON)}: "
          f"{predicted:+.2f}% ({label(predicted)})")
    print(f"Intercept at average inputs: {model[2]:+.2f}%")
    print("Learned return change per one training standard deviation:")
    for name, weight in zip(FEATURES.values(), model[3]):
        print(f"  {name:45} {weight:+.2f} pp")


if __name__ == "__main__":
    main()
