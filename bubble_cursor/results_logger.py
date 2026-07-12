import csv
import os
import time

import config


class ResultsLogger:
    """Writes one row per trial to a CSV file in RESULTS_DIR. Created lazily
    so a mode that's never finished doesn't leave an empty file."""

    def __init__(self, prefix, fieldnames):
        self.prefix = prefix
        self.fieldnames = fieldnames
        self.rows = []

    def log(self, **row):
        self.rows.append(row)

    def save(self):
        if not self.rows:
            return None
        here = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(here, config.RESULTS_DIR)
        os.makedirs(out_dir, exist_ok=True)
        fname = f"{self.prefix}_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(out_dir, fname)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            for row in self.rows:
                writer.writerow(row)
        return path
