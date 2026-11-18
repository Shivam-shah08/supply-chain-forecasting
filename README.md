# Supply Chain Forecasting

Forecast seven days of retail sales with a moving-average baseline and use simulated inventory to prioritize replenishment. The example covers ten products at Walmart store CA_1. It includes an eight-week backtest and a comparison with actual sales for the next week.

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
