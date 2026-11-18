# Supply Chain Forecasting

Forecast seven days of retail sales with a moving-average baseline and use simulated inventory to prioritize replenishment. The example covers ten products at Walmart store CA_1. It includes an eight-week backtest and a comparison with actual sales for the next week.

## Project at a glance

- **Forecasting.** Compared 7-day and 28-day moving averages across ten products. The 28-day window reduced weekly mean absolute error by about 30% in the eight-week backtest and by 9% in the following week.
- **Replenishment.** Used forecast sales, simulated lead times, and safety stock to calculate reorder points. The 28-day model flagged six products in the dashboard's forecast week.
- **Inventory simulation.** Replayed 28 days of sales to compare how much demand each policy filled and how much inventory it carried. The seven-day policy filled 95.8% of simulated demand versus 93.5% for the 28-day policy at their original safety-stock settings.

## How it works

| File | Role |
| --- | --- |
| [`main.py`](main.py) | Reads the M5 sales and calendar files, backtests forecasts, and writes daily forecasts and reorder rankings to SQLite. |
| [`replenishment_report.sql`](replenishment_report.sql) | Queries the latest forecast week and ranks products flagged for reorder. |
| [`dashboard.py`](dashboard.py) and [`dashboard.html`](dashboard.html) | Generate an interactive local report with a product selector and replenishment table. |
| [`inventory_simulation.py`](inventory_simulation.py) | Compares fill rate, average inventory, and order counts across forecast and safety-stock settings. |

## Run locally

Download `calendar.csv`, `sales_train_validation.csv`, and `sales_train_evaluation.csv` from the [Walmart M5 Forecasting competition](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data) and place them in a `data/` folder. The evaluation file enables the comparison to actual sales.

```sh
python3 main.py
sqlite3 -header -column -readonly data/forecasting.sqlite3 < replenishment_report.sql
python3 dashboard.py
```

Open `data/dashboard.html` in a browser. The dashboard shows the seven-day forecast for the selected product and a ranked list of products that reached their reorder points. The Python scripts use only the standard library.

Sales come from the M5 data. Inventory positions, supplier lead times, and safety stock are simulated. Raw data and generated outputs are kept in the ignored `data/` folder.

## Backtest results

For `HOBBIES_1_001` at `CA_1`, both moving averages forecasted the same eight historical weeks using only sales available before each week.

| Moving average | Daily MAE (units/day) | Weekly MAE (units/week) |
| --- | ---: | ---: |
| 7 days | 0.98 | 5.00 |
| 28 days | 0.78 | 2.91 |

Across all ten products at `CA_1`, the 28-day window had lower weekly MAE for every product over the same eight weeks. Each product contributes equally to the averages below.

| Moving average | Mean daily MAE (units/day) | Mean weekly MAE (units/week) |
| --- | ---: | ---: |
| 7 days | 1.61 | 8.19 |
| 28 days | 1.54 | 5.71 |

## Held-out week

For April 25–May 1, 2016, forecasts used only sales through April 24. Across the same ten products, mean absolute error in the weekly total was **5.00 units per product** for the 7-day window and **4.55** for the 28-day window. The 28-day window reduced error by 9% on this week, but still underforecast the highest-selling product by 32 units (57 forecast against 89 actual).

The dashboard and reorder ranking use the 28-day moving average to forecast the next seven days. With the same simulated inventory, both models flagged the same six products. The order of those products changed. The top item, `HOBBIES_1_008`, stayed first and its reorder point rose from 40 to 41 units.

## Inventory simulation

Run `python3 inventory_simulation.py` with all three M5 files available. The script replays April 25–May 22, 2016 for ten products. M5 sales serve as demand, unmet units are treated as lost sales, and supplier lead times are fixed. Each evening the policy updates its forecast. If inventory position reaches the reorder point, it orders up to forecast lead-time demand plus seven days of coverage and safety stock.

| Moving average | Fill rate | Unfilled units | Product-days with unfilled demand | Mean ending inventory per product | Orders placed |
| --- | ---: | ---: | ---: | ---: | ---: |
| 7 days | 95.8% | 22 | 8 | 12.79 | 36 |
| 28 days | 93.5% | 34 | 10 | 11.29 | 37 |

The 28-day policy carried less inventory, while the 7-day policy met more of the simulated demand. The results describe this replay under the stated assumptions.

### Safety-stock sensitivity

The simulation also adds zero to five safety-stock units to each product under the 28-day policy. The seven-day policy keeps its original safety stock for comparison.

| Extra units per product | Demand filled | Unfilled units | Mean ending inventory per product |
| ---: | ---: | ---: | ---: |
| 0 | 93.5% | 34 | 11.29 |
| 1 | 93.9% | 32 | 11.96 |
| 2 | 94.3% | 30 | 12.96 |
| 3 | 94.5% | 29 | 13.76 |
| 4 | 94.7% | 28 | 14.59 |
| 5 | 94.9% | 27 | 15.38 |

None of the tested settings matched the seven-day policy's 95.8% fill rate. Adding two or more units also raised average inventory above the seven-day policy's 12.79 units per product. This sensitivity check uses the same replay period as the initial comparison.
