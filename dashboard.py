"""Build a standalone dashboard from the SQLite forecast results."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from main import DATA


def main():
    project = Path(__file__).resolve().parent
    with closing(sqlite3.connect((DATA / "forecasting.sqlite3").as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        ranking = [dict(row) for row in db.execute((project / "replenishment_report.sql").read_text())]
        forecasts = [dict(row) for row in db.execute("""
            SELECT store_id, item_id, forecast_date, forecast_units
            FROM daily_forecasts
            WHERE forecast_date >= (SELECT MAX(forecast_start) FROM reorder_ranking)
            ORDER BY store_id, item_id, forecast_date
        """)]
    payload = json.dumps({"forecasts": forecasts, "ranking": ranking}).replace("<", "\\u003c")
    template = (project / "dashboard.html").read_text()
    output = DATA / "dashboard.html"
    output.write_text(template.replace('id="results" type="application/json"></script>',
                                       f'id="results" type="application/json">{payload}</script>'))
    print(f"Open {output}")


if __name__ == "__main__":
    main()
