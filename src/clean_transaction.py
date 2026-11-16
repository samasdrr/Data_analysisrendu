"""
Nettoyage du fichier transaction.csv
Encaissements et ventes en magasin
"""

import os
import csv


def find_transaction_file(default_path="transaction.csv"):
    candidates = [default_path, "transaction (1).csv", "data/raw/transaction.csv"]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Fichier transaction.csv introuvable")


def stream_clean_transactions(input_path=None):
    path = input_path or find_transaction_file()

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = str(row["Date"]).strip()
            time_str = str(row["Time"]).strip()
            item_code = str(row["Item Code"]).strip()
            qty_str = str(row["Quantity Sold (kilo)"]).strip()
            price_str = str(row["Unit Selling Price (RMB/kg)"]).strip()
            sale_return_str = str(row["Sale or Return"]).strip().lower()
            discount_str = str(row["Discount (Yes/No)"]).strip().lower()

            if not date_str or not item_code:
                continue

            try:
                raw_qty = float(qty_str)
                unit_price = float(price_str)
            except ValueError:
                continue

            if unit_price < 0:
                continue

            # Déduction des retours de marchandise
            is_return = (sale_return_str == "return")
            net_quantity = -abs(raw_qty) if is_return else abs(raw_qty)
            net_turnover = round(net_quantity * unit_price, 4)
            is_discounted = (discount_str == "yes")

            yield {
                "date": date_str,
                "time": time_str,
                "item_code": item_code,
                "net_quantity_kg": round(net_quantity, 4),
                "unit_selling_price_rmb_kg": round(unit_price, 4),
                "net_turnover_rmb": net_turnover,
                "is_return": is_return,
                "is_discounted": is_discounted
            }


if __name__ == "__main__":
    count = 0
    returns = 0
    total_ca = 0.0

    print("Nettoyage des transactions en cours...")
    for t in stream_clean_transactions():
        count += 1
        if t["is_return"]:
            returns += 1
        total_ca += t["net_turnover_rmb"]

    print(f"Transactions traitées : {count} (dont {returns} retours déduits).")
    print(f"Chiffre d'affaires net total : {total_ca:,.2f} RMB.")
