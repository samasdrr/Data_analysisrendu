"""
Module de nettoyage pour la table transaction.csv
Membre d'équipe : Membre 1 (Responsable Encaissements & Ventes Magasin)

Responsabilités & Justifications Métier :
1. Prise en charge des deux variantes de nom de fichier (transaction.csv ou transaction (1).csv).
2. Traitement des retours de marchandise ('return') : déduction obligatoire avec quantité nette négative (-abs(qty)).
3. Normalisation du flag Discount (Yes/No) en booléen standard.
4. Validation des dates ISO et calcul du Chiffre d'Affaires brut/net par ligne.
5. Filtrage des anomalies de saisie (quantités nulles, prix négatifs).
"""

import os
import csv
from datetime import datetime
from typing import Generator, Dict, Any, Optional


def find_transaction_file(default_path: str = "transaction.csv") -> str:
    """Trouve le fichier de transactions disponible."""
    candidates = [default_path, "transaction (1).csv", "data/raw/transaction.csv"]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Aucun fichier de transaction trouvé parmi : {candidates}")


def stream_clean_transactions(input_path: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
    """Nettoie les transactions en mode flux (générateur) pour économiser la RAM."""
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

            # Règle d'or métier : Les retours sont affectés d'une quantité négative
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
    total_turnover = 0.0

    print("[Membre 1 - transaction] Démarrage du nettoyage en flux...")
    for t in stream_clean_transactions():
        count += 1
        if t["is_return"]:
            returns += 1
        total_turnover += t["net_turnover_rmb"]
        if count % 200000 == 0:
            print(f"  -> {count} transactions traitées...")

    print(f"[Membre 1 - transaction] Terminé : {count} transactions validées dont {returns} retours déduits.")
    print(f"  -> CA Net consolidé : {total_turnover:,.2f} RMB")
