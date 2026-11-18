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

The 28-day window had lower errors for this product and period. The dashboard and reorder ranking still use the seven-day baseline while the longer window is evaluated across more products.
