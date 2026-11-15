"""
Module de nettoyage pour la table loss_rate.csv
Membre d'équipe : Membre 4 (Responsable Démarque & Pertes)

Responsabilités & Justifications Métier :
1. Suppression de l'en-tête corrompu UTF-8 BOM (\ufeffItem Code).
2. Trimming et conversion du taux de perte textuel en float (ex: '4.39 ' -> 0.0439).
3. Validation des bornes : le taux de perte doit être compris entre 0 et 100%.
4. Vérification de l'intégrité référentielle et déduplication.
"""

import os
import csv
from typing import List, Dict


def clean_loss_rate_data(input_path: str = "loss_rate.csv") -> List[Dict[str, any]]:
    """Nettoie les données de taux de perte."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    cleaned_losses = []
    seen_codes = set()

    # Utilisation de utf-8-sig pour éliminer automatiquement le BOM
    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Récupération sécurisée du code article
            item_code = (row.get("Item Code") or row.get("\ufeffItem Code") or "").strip()
            item_name = str(row.get("Item Name", "")).strip()
            loss_str = str(row.get("Loss Rate (%)", "")).strip()

            if not item_code:
                continue

            try:
                loss_pct = float(loss_str) if loss_str else 0.0
            except ValueError:
                loss_pct = 0.0

            if not (0.0 <= loss_pct <= 100.0):
                raise ValueError(f"Taux de perte aberrant ({loss_pct}%) pour l'article {item_code}")

            loss_rate_decimal = round(loss_pct / 100.0, 6)

            if item_code in seen_codes:
                raise ValueError(f"Doublon détecté sur Item Code dans loss_rate : {item_code}")
            seen_codes.add(item_code)

            cleaned_losses.append({
                "item_code": item_code,
                "item_name": item_name,
                "loss_rate_pct": loss_pct,
                "loss_rate_decimal": loss_rate_decimal
            })

    return cleaned_losses


def save_cleaned_loss_rate(cleaned_losses: List[Dict[str, any]], output_path: str = "data/gold/dim_loss_rate.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["item_code", "item_name", "loss_rate_pct", "loss_rate_decimal"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_losses)


if __name__ == "__main__":
    losses = clean_loss_rate_data()
    save_cleaned_loss_rate(losses)
    print(f"[Membre 4 - loss_rate] Succès : {len(losses)} articles traités avec taux de perte validé.")
