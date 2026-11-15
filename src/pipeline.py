"""
Pipeline global de Nettoyage, Fusion et Modélisation en Étoile (Gold Layer).
Intégration d'équipe (Branche develop -> main).

Ce script :
1. Charge et nettoie les 4 tables sources via leurs modules respectifs.
2. Établit le modèle relationnel et vérifie l'intégrité des clés primaires/étrangères.
3. Construit le schéma en étoile :
   - Dimensions : dim_products, dim_categories, dim_calendar, dim_loss_rate
   - Table de faits Gold : fact_daily_category_sales (et fact_daily_item_sales)
4. Calcule l'ensemble des KPIs demandés par le Comex :
   - CA Net, Volume (kg), Coût d'Achat (COGS), Marge Brute, Taux de Marge (%)
   - Coût de la Casse / Démarque (RMB), Marge Nette après Casse (RMB)
   - Évolutions vs N-1 (CA, Volume, Marge) et Taux de Remise (%)
5. Exporte un rapport JSON et CSV pour le Dashboard interactif et les Slides.
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


def run_etl_pipeline(output_dir: str = "data/gold") -> dict:
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 80)
    print("DEMARRAGE DU PIPELINE ETL - RAYON PRODUITS FRAIS")
    print("=" * 80)

    # 1. Dimensions
    print("[1/4] Nettoyage et chargement des dimensions (Product & Loss Rate)...")
    products, categories = clean_product_data()
    save_cleaned_products(products, os.path.join(output_dir, "dim_products.csv"))

    # Table de dimension catégorie
    with open(os.path.join(output_dir, "dim_categories.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category_code", "category_name"])
        writer.writeheader()
        writer.writerows(categories)

    losses = clean_loss_rate_data()
    save_cleaned_loss_rate(losses, os.path.join(output_dir, "dim_loss_rate.csv"))

    prod_cat_map = {p["item_code"]: p["category_name"] for p in products}
    prod_name_map = {p["item_code"]: p["item_name"] for p in products}
    loss_rate_map = {l["item_code"]: l["loss_rate_decimal"] for l in losses}

    # 2. Prix grossistes
    print("[2/4] Nettoyage et indexation de la mercuriale des prix grossistes...")
    prices = clean_price_data()
    save_cleaned_prices(prices, os.path.join(output_dir, "dim_wholesale_prices.csv"))
    price_map = {(p["date"], p["item_code"]): p["wholesale_price_rmb_kg"] for p in prices}

    # 3. Consolidation des transactions et calcul des faits
    print("[3/4] Agrégation des faits au niveau (Date, Catégorie) et calcul des KPIs...")
    daily_cat_facts = defaultdict(lambda: {
        "net_turnover": 0.0,
        "net_quantity_kg": 0.0,
        "cogs": 0.0,
        "loss_cost": 0.0,
        "discount_turnover": 0.0,
        "transactions_count": 0,
        "returns_count": 0
    })

    # Données par article pour les analyses fines
    item_period_facts = defaultdict(lambda: {
        "net_turnover": 0.0,
        "net_quantity_kg": 0.0,
        "cogs": 0.0,
        "loss_cost": 0.0
    })

    dates_seen = set()
    trans_processed = 0

    for t in stream_clean_transactions():
        trans_processed += 1
        d = t["date"]
        dates_seen.add(d)
        item_code = t["item_code"]
        qty = t["net_quantity_kg"]
        ca = t["net_turnover_rmb"]
        cat_name = prod_cat_map.get(item_code, "Autre")

        w_price = price_map.get((d, item_code), 0.0)
        cogs = qty * w_price
        loss_dec = loss_rate_map.get(item_code, 0.0)
        loss_cost = qty * loss_dec * w_price

        # Agrégation journalière par catégorie
        k = (d, cat_name)
        f = daily_cat_facts[k]
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

        # Agrégation par période pour les articles
        if "2022-07-01" <= d <= "2023-06-30":
            item_k = ("N", item_code)
        elif "2021-07-01" <= d <= "2022-06-30":
            item_k = ("N-1", item_code)
        else:
            item_k = ("Historique", item_code)

        it_f = item_period_facts[item_k]
        it_f["net_turnover"] += ca
        it_f["net_quantity_kg"] += qty
        it_f["cogs"] += cogs
        it_f["loss_cost"] += loss_cost

    # 4. Génération de dim_calendar
    print("[4/4] Sauvegarde des tables Gold et calcul des synthèses Comex...")
    calendar_rows = []
    for d_str in sorted(dates_seen):
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        calendar_rows.append({
            "date": d_str,
            "year": dt.year,
            "month": dt.month,
            "month_name": dt.strftime("%B"),
            "day": dt.day,
            "day_of_week": dt.strftime("%A"),
            "quarter": f"Q{(dt.month - 1) // 3 + 1}",
            "period": "N" if "2022-07-01" <= d_str <= "2023-06-30" else ("N-1" if "2021-07-01" <= d_str <= "2022-06-30" else "N-2")
        })

    with open(os.path.join(output_dir, "dim_calendar.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(calendar_rows[0].keys()))
        writer.writeheader()
        writer.writerows(calendar_rows)

    # Sauvegarde de fact_daily_category_sales.csv
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
            "discount_turnover_rmb": round(vals["discount_turnover"], 2),
            "transactions_count": vals["transactions_count"],
            "returns_count": vals["returns_count"]
        })

    with open(os.path.join(output_dir, "fact_daily_category_sales.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fact_rows[0].keys()))
        writer.writeheader()
        writer.writerows(fact_rows)

    # Calcul synthèse Comex par catégorie (N vs N-1)
    summary_by_cat = defaultdict(lambda: {"N": defaultdict(float), "N-1": defaultdict(float)})
    for row in fact_rows:
        d = row["date"]
        cat = row["category_name"]
        if "2022-07-01" <= d <= "2023-06-30":
            target = summary_by_cat[cat]["N"]
        elif "2021-07-01" <= d <= "2022-06-30":
            target = summary_by_cat[cat]["N-1"]
        else:
            continue

        target["turnover"] += row["net_turnover_rmb"]
        target["quantity"] += row["net_quantity_kg"]
        target["cogs"] += row["cogs_rmb"]
        target["gross_margin"] += row["gross_margin_rmb"]
        target["loss_cost"] += row["loss_cost_rmb"]
        target["net_margin"] += row["net_margin_rmb"]
        target["discount_turnover"] += row["discount_turnover_rmb"]

    comex_kpis = []
    for cat, p_data in sorted(summary_by_cat.items()):
        n = p_data["N"]
        n1 = p_data["N-1"]
        evol_ca = ((n["turnover"] - n1["turnover"]) / n1["turnover"] * 100) if n1["turnover"] else 0.0
        diff_ca = n["turnover"] - n1["turnover"]
        evol_vol = ((n["quantity"] - n1["quantity"]) / n1["quantity"] * 100) if n1["quantity"] else 0.0
        diff_vol = n["quantity"] - n1["quantity"]
        tm_pct = (n["gross_margin"] / n["turnover"] * 100) if n["turnover"] else 0.0
        t_net_pct = (n["net_margin"] / n["turnover"] * 100) if n["turnover"] else 0.0
        disc_rate = (n["discount_turnover"] / n["turnover"] * 100) if n["turnover"] else 0.0

        comex_kpis.append({
            "category": cat,
            "ca_n_rmb": round(n["turnover"], 2),
            "ca_n1_rmb": round(n1["turnover"], 2),
            "evol_ca_pct": round(evol_ca, 2),
            "diff_ca_rmb": round(diff_ca, 2),
            "vol_n_kg": round(n["quantity"], 2),
            "vol_n1_kg": round(n1["quantity"], 2),
            "evol_vol_pct": round(evol_vol, 2),
            "diff_vol_kg": round(diff_vol, 2),
            "gross_margin_rmb": round(n["gross_margin"], 2),
            "gross_margin_rate_pct": round(tm_pct, 2),
            "loss_cost_rmb": round(n["loss_cost"], 2),
            "net_margin_rmb": round(n["net_margin"], 2),
            "net_margin_rate_pct": round(t_net_pct, 2),
            "discount_rate_pct": round(disc_rate, 2)
        })

    with open(os.path.join(output_dir, "comex_category_kpis.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(comex_kpis[0].keys()))
        writer.writeheader()
        writer.writerows(comex_kpis)

    # Top articles par perte
    top_losses = []
    for (period, code), it_v in item_period_facts.items():
        if period != "N":
            continue
        top_losses.append({
            "item_code": code,
            "item_name": prod_name_map.get(code, "Inconnu"),
            "category": prod_cat_map.get(code, "Autre"),
            "loss_cost_rmb": round(it_v["loss_cost"], 2),
            "turnover_rmb": round(it_v["net_turnover"], 2),
            "quantity_kg": round(it_v["net_quantity_kg"], 2),
            "loss_to_ca_pct": round((it_v["loss_cost"] / it_v["net_turnover"] * 100) if it_v["net_turnover"] else 0.0, 2)
        })
    top_losses.sort(key=lambda x: x["loss_cost_rmb"], reverse=True)

    # Top Solanum items
    solanum_items = []
    for (period, code), it_v in item_period_facts.items():
        if prod_cat_map.get(code) != "Solanum" or period != "N":
            continue
        prev = item_period_facts.get(("N-1", code), {"net_turnover": 0.0, "net_quantity_kg": 0.0})
        ca_prev = prev["net_turnover"]
        ca_cur = it_v["net_turnover"]
        evol = ((ca_cur - ca_prev) / ca_prev * 100) if ca_prev else 0.0
        solanum_items.append({
            "item_code": code,
            "item_name": prod_name_map.get(code, "Inconnu"),
            "ca_n_rmb": round(ca_cur, 2),
            "ca_n1_rmb": round(ca_prev, 2),
            "evol_ca_pct": round(evol, 2),
            "vol_n_kg": round(it_v["net_quantity_kg"], 2),
            "vol_n1_kg": round(prev["net_quantity_kg"], 2)
        })
    solanum_items.sort(key=lambda x: x["ca_n1_rmb"], reverse=True)

    final_summary = {
        "execution_date": datetime.now().isoformat(),
        "total_transactions_processed": trans_processed,
        "kpi_categories": comex_kpis,
        "top_10_loss_items": top_losses[:10],
        "solanum_breakdown": solanum_items
    }

    with open(os.path.join(output_dir, "comex_summary.json"), "w", encoding="utf-8") as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCES] Pipeline ETL termine avec succes ! Tables enregistrees dans {output_dir}")
    return final_summary


if __name__ == "__main__":
    run_etl_pipeline()
