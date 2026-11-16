"""
Pipeline de consolidation des 4 fichiers nettoyés
Génération des tables du schéma en étoile (Gold) pour le dashboard
"""

import os
import csv
import json
from collections import defaultdict
from datetime import datetime

from clean_product import clean_product_data, save_cleaned_products
from clean_loss_rate import clean_loss_rate_data, save_cleaned_loss_rate
from clean_price import clean_price_data, save_cleaned_prices
from clean_transaction import stream_clean_transactions


def run_etl_pipeline(output_dir="data/gold"):
    os.makedirs(output_dir, exist_ok=True)
    print("Démarrage du traitement des données...")

    # 1. Nettoyage des dimensions
    products, categories = clean_product_data()
    save_cleaned_products(products, os.path.join(output_dir, "dim_products.csv"))

    with open(os.path.join(output_dir, "dim_categories.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category_code", "category_name"])
        writer.writeheader()
        writer.writerows(categories)

    losses = clean_loss_rate_data()
    save_cleaned_loss_rate(losses, os.path.join(output_dir, "dim_loss_rate.csv"))

    prod_cat_map = {p["item_code"]: p["category_name"] for p in products}
    loss_rate_map = {l["item_code"]: l["loss_rate_decimal"] for l in losses}

    # 2. Nettoyage des prix grossistes
    prices = clean_price_data()
    save_cleaned_prices(prices, os.path.join(output_dir, "dim_wholesale_prices.csv"))
    price_map = {(p["date"], p["item_code"]): p["wholesale_price_rmb_kg"] for p in prices}

    # 3. Consolidation des transactions
    daily_cat_facts = defaultdict(lambda: {
        "net_turnover": 0.0,
        "net_quantity_kg": 0.0,
        "cogs": 0.0,
        "loss_cost": 0.0,
        "discount_turnover": 0.0,
        "transactions_count": 0,
        "returns_count": 0
    })

    dates_seen = set()
    trans_count = 0

    for t in stream_clean_transactions():
        trans_count += 1
        d = t["date"]
        dates_seen.add(d)
        item_code = t["item_code"]
        qty = t["net_quantity_kg"]
        ca = t["net_turnover_rmb"]
        cat_name = prod_cat_map.get(item_code, "Autre")

        w_price = price_map.get((d, item_code), 0.0)
        cogs = qty * w_price
        loss_cost = qty * loss_rate_map.get(item_code, 0.0) * w_price

        f = daily_cat_facts[(d, cat_name)]
        f["net_turnover"] += ca
        f["net_quantity_kg"] += qty
        f["cogs"] += cogs
        f["loss_cost"] += loss_cost
        if t["is_discounted"]:
            f["discount_turnover"] += ca
        if t["is_return"]:
            f["returns_count"] += 1
        else:
            f["transactions_count"] += 1

    # 4. Table dimension calendrier
    calendar_rows = []
    for d_str in sorted(dates_seen):
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        calendar_rows.append({
            "date": d_str,
            "year": dt.year,
            "month": dt.month,
            "quarter": f"Q{(dt.month - 1) // 3 + 1}",
            "period": "N" if "2022-07-01" <= d_str <= "2023-06-30" else ("N-1" if "2021-07-01" <= d_str <= "2022-06-30" else "N-2")
        })

    with open(os.path.join(output_dir, "dim_calendar.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(calendar_rows[0].keys()))
        writer.writeheader()
        writer.writerows(calendar_rows)

    # 5. Table de faits
    fact_rows = []
    for (d, cat), vals in sorted(daily_cat_facts.items()):
        gross_margin = vals["net_turnover"] - vals["cogs"]
        margin_rate = (gross_margin / vals["net_turnover"] * 100.0) if vals["net_turnover"] else 0.0
        net_margin = gross_margin - vals["loss_cost"]
        fact_rows.append({
            "date": d,
            "category_name": cat,
            "net_turnover_rmb": round(vals["net_turnover"], 2),
            "net_quantity_kg": round(vals["net_quantity_kg"], 2),
            "cogs_rmb": round(vals["cogs"], 2),
            "gross_margin_rmb": round(gross_margin, 2),
            "gross_margin_rate_pct": round(margin_rate, 2),
            "loss_cost_rmb": round(vals["loss_cost"], 2),
            "net_margin_rmb": round(net_margin, 2),
            "discount_turnover_rmb": round(vals["discount_turnover"], 2)
        })

    with open(os.path.join(output_dir, "fact_daily_category_sales.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fact_rows[0].keys()))
        writer.writeheader()
        writer.writerows(fact_rows)

    print(f"Traitement terminé : {trans_count} transactions traitées avec succès.")


if __name__ == "__main__":
    run_etl_pipeline()
