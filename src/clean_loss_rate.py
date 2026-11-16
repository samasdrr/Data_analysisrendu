"""
Nettoyage du fichier loss_rate.csv
Taux de casse et démarque
"""

import os
import csv


def clean_loss_rate_data(input_path="loss_rate.csv"):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    cleaned_losses = []
    seen_codes = set()

    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_code = (row.get("Item Code") or row.get("\ufeffItem Code") or "").strip()
            item_name = str(row.get("Item Name", "")).strip()
            loss_str = str(row.get("Loss Rate (%)", "")).strip()

            if not item_code:
                continue

            try:
                loss_pct = float(loss_str) if loss_str else 0.0
            except ValueError:
                loss_pct = 0.0

            loss_rate_decimal = round(loss_pct / 100.0, 6)

            if item_code in seen_codes:
                continue
            seen_codes.add(item_code)

            cleaned_losses.append({
                "item_code": item_code,
                "item_name": item_name,
                "loss_rate_pct": loss_pct,
                "loss_rate_decimal": loss_rate_decimal
            })

    return cleaned_losses


def save_cleaned_loss_rate(cleaned_losses, output_path="data/gold/dim_loss_rate.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["item_code", "item_name", "loss_rate_pct", "loss_rate_decimal"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_losses)


if __name__ == "__main__":
    losses = clean_loss_rate_data()
    save_cleaned_loss_rate(losses)
    print(f"Taux de casse nettoyés : {len(losses)} articles.")
