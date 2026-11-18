"""Forecast one product's daily sales using a seven-day moving average."""

import csv
from datetime import date, timedelta
from pathlib import Path
from statistics import mean


DATA = Path(__file__).resolve().parent / "data"


def main():
    with (DATA / "sales_train_validation.csv").open(newline="") as file:
        # Each row contains one product at one store. Start with the first row.
        product = next(csv.DictReader(file))

    sales_by_day = [
        (day, int(units)) for day, units in product.items() if day.startswith("d_")
    ]
    last_week = sales_by_day[-7:]

    with (DATA / "calendar.csv").open(newline="") as file:
        dates = {row["d"]: date.fromisoformat(row["date"]) for row in csv.DictReader(file)}

    daily_forecast = mean(units for _, units in last_week)
    last_date = dates[last_week[-1][0]]
    print(f"Product {product['item_id']} at store {product['store_id']}")
    print("Sales during the last seven days in the training file")
    for day, units in last_week:
        print(f"  {dates[day]}  {units} units")

    print("Seven-day forecast")
    for days_ahead in range(1, 8):
        forecast_date = last_date + timedelta(days=days_ahead)
        print(f"  {forecast_date}  {daily_forecast:.2f} units")
    print(f"Forecast total for the week: {daily_forecast * 7:.1f} units")


if __name__ == "__main__":
    main()
