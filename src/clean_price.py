"""
Nettoyage du fichier price.csv
Prix d'achat grossiste
"""

import os
import csv
from datetime import datetime


def clean_price_data(input_path="price.csv"):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    cleaned_prices = []
    seen_composite_keys = set()

    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = str(row["Date"]).strip()
            item_code = str(row["Item Code"]).strip()
            price_str = str(row["Wholesale Price (RMB/kg)"]).strip()

            if not date_str or not item_code:
                continue

            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                clean_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

            try:
                wholesale_price = float(price_str)
            except ValueError:
                continue

            if wholesale_price < 0:
                continue

            composite_key = (clean_date, item_code)
            if composite_key in seen_composite_keys:
                continue
            seen_composite_keys.add(composite_key)

            cleaned_prices.append({
                "date": clean_date,
                "item_code": item_code,
                "wholesale_price_rmb_kg": round(wholesale_price, 4)
            })

    return cleaned_prices


def save_cleaned_prices(cleaned_prices, output_path="data/gold/dim_wholesale_prices.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["date", "item_code", "wholesale_price_rmb_kg"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_prices)


if __name__ == "__main__":
    prices = clean_price_data()
    save_cleaned_prices(prices)
    print(f"Prix grossistes nettoyés : {len(prices)} lignes.")
