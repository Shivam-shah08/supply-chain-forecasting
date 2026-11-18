"""Forecast and evaluate one product's sales using a seven-day moving average."""

import csv
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil
from pathlib import Path
from statistics import mean


DATA = Path(__file__).resolve().parent / "data"
FORECAST_DAYS = 7
BACKTEST_WEEKS = 8
COMPARISON_WINDOW = 28
PRODUCT_LIMIT = 10


@dataclass(frozen=True)
class InventoryInputs:
    lead_time_days: int
    safety_stock: int
    on_hand: int
    on_order: int = 0
    backorders: int = 0


# Simulated inventory and supplier inputs for the ten example products at CA_1.
INVENTORY = {
    "HOBBIES_1_001": InventoryInputs(lead_time_days=5, safety_stock=3, on_hand=7),
    "HOBBIES_1_002": InventoryInputs(lead_time_days=3, safety_stock=2, on_hand=5),
    "HOBBIES_1_003": InventoryInputs(lead_time_days=6, safety_stock=4, on_hand=6, on_order=5),
    "HOBBIES_1_004": InventoryInputs(lead_time_days=4, safety_stock=4, on_hand=9, on_order=3),
    "HOBBIES_1_005": InventoryInputs(lead_time_days=7, safety_stock=5, on_hand=8, backorders=2),
    "HOBBIES_1_006": InventoryInputs(lead_time_days=3, safety_stock=2, on_hand=8),
    "HOBBIES_1_007": InventoryInputs(lead_time_days=6, safety_stock=3, on_hand=4),
    "HOBBIES_1_008": InventoryInputs(lead_time_days=4, safety_stock=8, on_hand=18, on_order=10),
    "HOBBIES_1_009": InventoryInputs(lead_time_days=5, safety_stock=4, on_hand=6, on_order=5),
    "HOBBIES_1_010": InventoryInputs(lead_time_days=7, safety_stock=3, on_hand=4, backorders=1),
}


def load_actual_sales(product, forecast_days):
    with (DATA / "sales_train_evaluation.csv").open(newline="") as file:
        for row in csv.DictReader(file):
            if row["item_id"] == product["item_id"] and row["store_id"] == product["store_id"]:
                return [int(row[day]) for day in forecast_days]

    raise SystemExit("The evaluation file has no sales row for this product and store.")


def backtest(sales_by_day, dates=None):
    if dates is not None:
        print("\nBacktest on the last eight weeks of training data")
    windows = (FORECAST_DAYS, COMPARISON_WINDOW)
    daily_errors = {window: [] for window in windows}
    weekly_errors = {window: [] for window in windows}
    first_week = len(sales_by_day) - BACKTEST_WEEKS * FORECAST_DAYS
    for start in range(first_week, len(sales_by_day), FORECAST_DAYS):
        actual_week = sales_by_day[start:start + FORECAST_DAYS]
        actual_total = sum(units for _, units in actual_week)
        forecasts = []
        for window in windows:
            history = sales_by_day[start - window:start]
            forecast = mean(units for _, units in history)
            predicted_total = forecast * FORECAST_DAYS
            daily_errors[window].extend(abs(forecast - units) for _, units in actual_week)
            weekly_errors[window].append(abs(predicted_total - actual_total))
            forecasts.append(f"{window}-day forecast {predicted_total:.2f}")
        if dates is not None:
            print(f"  Week of {dates[actual_week[0][0]]}: {', '.join(forecasts)}, actual {actual_total} units")

    return {
        window: (mean(daily_errors[window]), mean(weekly_errors[window]))
        for window in windows
    }


def print_portfolio_backtest(products):
    print("\nForecast comparison across all products (weekly MAE, units/week)")
    print(f"{'Product':<20}{'7-day average':>16}{'28-day average':>17}")
    results = []
    for product in products:
        metrics = backtest(daily_sales(product))
        results.append(metrics)
        print(f"{product['item_id']:<20}{metrics[FORECAST_DAYS][1]:>16.2f}"
              f"{metrics[COMPARISON_WINDOW][1]:>17.2f}")

    for window in (FORECAST_DAYS, COMPARISON_WINDOW):
        daily_mae = mean(metrics[window][0] for metrics in results)
        weekly_mae = mean(metrics[window][1] for metrics in results)
        print(f"{window}-day portfolio average: daily MAE {daily_mae:.2f} units/day, "
              f"weekly MAE {weekly_mae:.2f} units/week")


def reorder_levels(daily_forecast, inputs):
    lead_time_demand = daily_forecast * inputs.lead_time_days
    reorder_point = ceil(lead_time_demand + inputs.safety_stock)
    inventory_position = inputs.on_hand + inputs.on_order - inputs.backorders
    return lead_time_demand, reorder_point, inventory_position


def print_reorder_decision(daily_forecast, inputs):
    lead_time_demand, reorder_point, inventory_position = reorder_levels(daily_forecast, inputs)
    decision = "Reorder now" if inventory_position <= reorder_point else "Wait"

    print("\nReorder decision (simulated inventory and supplier inputs)")
    print(f"Expected sales over the {inputs.lead_time_days}-day lead time: {lead_time_demand:.2f} units")
    print(f"Safety stock: {inputs.safety_stock} units")
    print(f"Reorder point: {reorder_point} units")
    print(f"Inventory position: {inventory_position} units")
    print(f"Decision: {decision}")


def daily_sales(product):
    return [(day, int(units)) for day, units in product.items() if day.startswith("d_")]


def replenishment_ranking(products):
    ranking = []
    for product in products:
        item_id = product["item_id"]
        last_week = daily_sales(product)[-FORECAST_DAYS:]
        forecast = mean(units for _, units in last_week)
        _, reorder_point, inventory_position = reorder_levels(forecast, INVENTORY[item_id])
        gap = reorder_point - inventory_position
        ranking.append((gap, item_id, reorder_point, inventory_position, forecast))
    return sorted(ranking, key=lambda row: (-row[0], row[1]))


def print_replenishment_ranking(ranking, store_id):
    print(f"\nReplenishment ranking for {len(ranking)} products at {store_id}")
    print("Inventory and supplier inputs are simulated for each product.")
    print(f"{'Product':<20}{'Reorder point':>15}{'Inventory':>12}{'Gap':>8}  Decision")
    for gap, item_id, reorder_point, inventory_position, _ in ranking:
        decision = "Reorder now" if gap >= 0 else "Wait"
        print(f"{item_id:<20}{reorder_point:>15}{inventory_position:>12}{gap:>8}  {decision}")


def save_results(store_id, forecast_dates, ranking):
    database = DATA / "forecasting.sqlite3"
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS daily_forecasts (
                store_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                forecast_date TEXT NOT NULL,
                forecast_units REAL NOT NULL,
                PRIMARY KEY (store_id, item_id, forecast_date)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS reorder_ranking (
                store_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                forecast_start TEXT NOT NULL,
                priority INTEGER NOT NULL,
                reorder_point INTEGER NOT NULL,
                inventory_position INTEGER NOT NULL,
                gap INTEGER NOT NULL,
                decision TEXT NOT NULL,
                PRIMARY KEY (store_id, item_id, forecast_start)
            )
        """)
        forecast_start = forecast_dates[0].isoformat()
        forecast_end = forecast_dates[-1].isoformat()
        connection.execute(
            "DELETE FROM daily_forecasts WHERE store_id = ? AND forecast_date BETWEEN ? AND ?",
            (store_id, forecast_start, forecast_end),
        )
        connection.execute(
            "DELETE FROM reorder_ranking WHERE store_id = ? AND forecast_start = ?",
            (store_id, forecast_start),
        )
        connection.executemany(
            "INSERT INTO daily_forecasts VALUES (?, ?, ?, ?)",
            (
                (store_id, item_id, day.isoformat(), forecast)
                for _, item_id, _, _, forecast in ranking
                for day in forecast_dates
            ),
        )
        connection.executemany(
            "INSERT INTO reorder_ranking VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                (store_id, item_id, forecast_start, priority, reorder_point,
                 inventory_position, gap, "Reorder now" if gap >= 0 else "Wait")
                for priority, (gap, item_id, reorder_point, inventory_position, _)
                in enumerate(ranking, start=1)
            ),
        )
    print(f"\nSaved forecasts and reorder rankings to {database}")


def main():
    with (DATA / "sales_train_validation.csv").open(newline="") as file:
        # Each row contains one product at one store. Start with the first row.
        reader = csv.DictReader(file)
        product = next(reader)
        products = [product]
        for row in reader:
            if row["store_id"] == product["store_id"]:
                products.append(row)
            if len(products) == PRODUCT_LIMIT:
                break

    sales_by_day = daily_sales(product)
    last_week = sales_by_day[-FORECAST_DAYS:]

    with (DATA / "calendar.csv").open(newline="") as file:
        dates = {row["d"]: date.fromisoformat(row["date"]) for row in csv.DictReader(file)}

    daily_forecast = mean(units for _, units in last_week)
    last_date = dates[last_week[-1][0]]
    print(f"Product {product['item_id']} at store {product['store_id']}")
    print("Sales during the last seven days in the training file")
    for day, units in last_week:
        print(f"  {dates[day]}  {units} units")

    forecast_dates = [
        last_date + timedelta(days=days_ahead)
        for days_ahead in range(1, FORECAST_DAYS + 1)
    ]
    forecast_total = daily_forecast * FORECAST_DAYS
    day_by_date = {calendar_date: day for day, calendar_date in dates.items()}
    try:
        actual_sales = load_actual_sales(product, [day_by_date[day] for day in forecast_dates])
    except FileNotFoundError:
        actual_sales = None

    print("Seven-day forecast")
    for index, forecast_date in enumerate(forecast_dates):
        line = f"  {forecast_date}  forecast {daily_forecast:.2f} units"
        if actual_sales is not None:
            line += f"  |  actual {actual_sales[index]} units"
        print(line)
    print(f"Forecast total for the week: {forecast_total:.1f} units")

    metrics = backtest(sales_by_day, dates)
    for window, (daily_mae, weekly_mae) in metrics.items():
        print(f"{window}-day moving average: daily MAE {daily_mae:.2f} units/day, "
              f"weekly MAE {weekly_mae:.2f} units/week")
    print_portfolio_backtest(products)
    print_reorder_decision(daily_forecast, INVENTORY[product["item_id"]])
    store_id = product["store_id"]
    ranking = replenishment_ranking(products)
    print_replenishment_ranking(ranking, store_id)
    save_results(store_id, forecast_dates, ranking)
    print("\nEvaluation on the week after the training data")
    if actual_sales is None:
        print("Add data/sales_train_evaluation.csv to compare with actual sales.")
        return

    actual_total = sum(actual_sales)
    weekly_error = forecast_total - actual_total
    daily_mae = mean(abs(daily_forecast - actual) for actual in actual_sales)
    print(f"Actual total for the week: {actual_total} units")
    print(f"Weekly error (forecast minus actual): {weekly_error:+.1f} units")
    print(f"Daily mean absolute error: {daily_mae:.2f} units/day")


if __name__ == "__main__":
    main()
