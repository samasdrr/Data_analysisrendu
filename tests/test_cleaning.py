"""
Tests Unitaires et d'Intégration pour la CI/CD
Vérifie la robustesse de chaque étape de nettoyage et de la modélisation en étoile.
"""

import os
import sys
import unittest

# Ajout du répertoire src au path d'importation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from clean_product import clean_product_data
from clean_loss_rate import clean_loss_rate_data
from clean_price import clean_price_data
from clean_transaction import stream_clean_transactions


class TestDataCleaningPipeline(unittest.TestCase):

    def test_01_clean_products(self):
        """Vérifie l'intégrité du référentiel produit."""
        products, categories = clean_product_data()
        self.assertGreater(len(products), 0, "La table produit ne doit pas être vide.")
        self.assertGreater(len(categories), 0, "La table catégorie ne doit pas être vide.")

        # Test unicité des codes articles
        codes = [p["item_code"] for p in products]
        self.assertEqual(len(codes), len(set(codes)), "Il ne doit y avoir aucun doublon sur item_code.")

        # Test suppression des espaces insécables
        for p in products:
            self.assertNotIn("\xa0", p["category_name"], "Aucun espace insécable ne doit subsister dans les catégories.")
            self.assertTrue(len(p["item_name"]) > 0, "Le nom du produit ne doit pas être vide.")

    def test_02_clean_loss_rate(self):
        """Vérifie la table des taux de perte."""
        losses = clean_loss_rate_data()
        self.assertGreater(len(losses), 0, "La table loss_rate ne doit pas être vide.")

        for item in losses:
            self.assertFalse(item["item_code"].startswith("\ufeff"), "Le BOM UTF-8 doit être supprimé du code article.")
            self.assertGreaterEqual(item["loss_rate_pct"], 0.0, "Le taux de perte doit être >= 0%.")
            self.assertLessEqual(item["loss_rate_pct"], 100.0, "Le taux de perte doit être <= 100%.")
            self.assertAlmostEqual(item["loss_rate_pct"] / 100.0, item["loss_rate_decimal"], places=4)

    def test_03_clean_price(self):
        """Vérifie la mercuriale des prix d'achat grossiste."""
        prices = clean_price_data()
        self.assertGreater(len(prices), 0, "La table price ne doit pas être vide.")

        # Échantillonnage pour la performance du test
        for p in prices[:5000]:
            self.assertEqual(len(p["date"]), 10, "La date doit être au format YYYY-MM-DD.")
            self.assertGreaterEqual(p["wholesale_price_rmb_kg"], 0.0, "Le prix grossiste ne peut être négatif.")

    def test_04_clean_transactions(self):
        """Vérifie le traitement des encaissements et la règle métier des retours."""
        trans_gen = stream_clean_transactions()
        sample_trans = [next(trans_gen) for _ in range(2000)]

        for t in sample_trans:
            self.assertIn("net_quantity_kg", t)
            self.assertIn("net_turnover_rmb", t)
            if t["is_return"]:
                self.assertLessEqual(t["net_quantity_kg"], 0.0, "Les retours doivent avoir une quantité négative.")
                self.assertLessEqual(t["net_turnover_rmb"], 0.0, "Les retours doivent avoir un CA net négatif.")
            else:
                self.assertGreaterEqual(t["net_quantity_kg"], 0.0)
                self.assertGreaterEqual(t["net_turnover_rmb"], 0.0)


if __name__ == "__main__":
    unittest.main()
