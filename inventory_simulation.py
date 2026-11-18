"""Replay 28 days of M5 sales against two simulated replenishment policies."""

import csv
from collections import defaultdict
from dataclasses import dataclass, replace
from math import ceil
from statistics import mean

from main import ACTIVE_WINDOW, DATA, FORECAST_DAYS, INVENTORY, daily_sales, load_actual_sales


STORE = "CA_1"
REPLAY_DAYS = 28


@dataclass
class Result:
    demand: int = 0
    unfilled: int = 0
    stockout_days: int = 0
    inventory_days: int = 0
    orders: int = 0


def replay(history, actuals, inputs, window):
    history = history.copy()
    on_hand = max(0, inputs.on_hand - inputs.backorders)
    arrivals = defaultdict(int)
    arrivals[inputs.lead_time_days] = inputs.on_order
    result = Result()
    for day, demand in enumerate(actuals):
        on_hand += arrivals.pop(day, 0)
        filled = min(on_hand, demand)
        on_hand -= filled
        result.demand += demand
        result.unfilled += demand - filled
        result.stockout_days += filled < demand
        result.inventory_days += on_hand

        # Actual M5 sales stand in for demand and become known after the day closes.
        history.append(demand)
        forecast = mean(history[-window:])
        reorder_point = ceil(forecast * inputs.lead_time_days + inputs.safety_stock)
        position = on_hand + sum(arrivals.values())
        if position <= reorder_point:
            target = ceil(forecast * (inputs.lead_time_days + FORECAST_DAYS) + inputs.safety_stock)
            quantity = target - position
            if quantity > 0:
                arrivals[day + inputs.lead_time_days] += quantity
                result.orders += 1
    return result


def main():
    products = []
    with (DATA / "sales_train_validation.csv").open(newline="") as file:
        for row in csv.DictReader(file):
            if row["store_id"] == STORE and row["item_id"] in INVENTORY:
                products.append(row)
                if len(products) == len(INVENTORY):
                    break

    histories = {row["item_id"]: daily_sales(row) for row in products}
    last_training_day = int(next(iter(histories.values()))[-1][0].removeprefix("d_"))
    replay_days = [f"d_{last_training_day + offset}" for offset in range(1, REPLAY_DAYS + 1)]
    actuals = load_actual_sales(products, replay_days)

    print(f"Inventory replay for {len(products)} products at {STORE} over {REPLAY_DAYS} days")
    scenarios = [(FORECAST_DAYS, 0)] + [(ACTIVE_WINDOW, extra) for extra in range(6)]
    print(f"{'Forecast window':>15} {'Extra safety stock':>18} {'Fill rate':>10} "
          f"{'Unfilled':>9} {'Stockout days':>14} {'Mean stock':>11} {'Orders':>7}")
    for window, extra_safety_stock in scenarios:
        results = []
        for item_id, sales in histories.items():
            inputs = INVENTORY[item_id]
            inputs = replace(inputs, safety_stock=inputs.safety_stock + extra_safety_stock)
            results.append(replay([units for _, units in sales], actuals[(STORE, item_id)], inputs, window))

        demand = sum(result.demand for result in results)
        unfilled = sum(result.unfilled for result in results)
        stockout_days = sum(result.stockout_days for result in results)
        average_stock = mean(result.inventory_days for result in results) / REPLAY_DAYS
        orders = sum(result.orders for result in results)
        print(f"{window:>11} days {extra_safety_stock:>18} {(demand - unfilled) / demand:>10.1%} "
              f"{unfilled:>9} {stockout_days:>14} {average_stock:>11.2f} {orders:>7}")


if __name__ == "__main__":
    main()
