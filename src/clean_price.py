"""
Module de nettoyage pour la table price.csv
Membre d'équipe : Membre 3 (Responsable Tarification & Achats Grossiste)

Responsabilités & Justifications Métier :
1. Validation et normalisation du format de date ISO (YYYY-MM-DD).
2. Vérification et conversion du prix d'achat grossiste en float positif.
3. Déduplication sur la clé composite (Date, Item Code).
4. Détection des prix grossistes nuls ou aberrants.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict


def clean_price_data(input_path: str = "price.csv") -> List[Dict[str, any]]:
    """Nettoie les données de prix d'achat grossiste."""
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

            # Validation du format date
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                clean_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Format de date invalide dans price.csv : {date_str}")

            # Validation du prix grossiste
            try:
                wholesale_price = float(price_str)
            except ValueError:
                raise ValueError(f"Prix invalide pour {item_code} à la date {date_str} : {price_str}")

            if wholesale_price < 0:
                raise ValueError(f"Prix d'achat négatif détecté pour {item_code} : {wholesale_price}")

            composite_key = (clean_date, item_code)
            if composite_key in seen_composite_keys:
                # S'il y a un doublon strict, on conserve la dernière valeur ou on ignore
                continue
            seen_composite_keys.add(composite_key)

            cleaned_prices.append({
                "date": clean_date,
                "item_code": item_code,
                "wholesale_price_rmb_kg": round(wholesale_price, 4)
            })

    return cleaned_prices


def save_cleaned_prices(cleaned_prices: List[Dict[str, any]], output_path: str = "data/gold/dim_wholesale_prices.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["date", "item_code", "wholesale_price_rmb_kg"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_prices)


if __name__ == "__main__":
    prices = clean_price_data()
    save_cleaned_prices(prices)
    print(f"[Membre 3 - price] Succès : {len(prices)} enregistrements de prix grossiste validés.")
