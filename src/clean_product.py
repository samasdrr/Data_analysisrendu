"""
Nettoyage du fichier product.csv
Référentiel des produits
"""

import os
import csv


def clean_product_data(input_path="product.csv"):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier introuvable : {input_path}")

    cleaned_products = []
    categories_set = set()
    seen_codes = set()

    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_code = str(row["Item Code"]).strip()
            item_name = str(row["Item Name"]).strip()
            cat_code = str(row["Category Code"]).strip()
            cat_name = str(row["Category Name"]).replace("\xa0", " ").strip()

            if not item_code:
                continue

            if item_code in seen_codes:
                continue
            seen_codes.add(item_code)

            cleaned_products.append({
                "item_code": item_code,
                "item_name": item_name,
                "category_code": cat_code,
                "category_name": cat_name
            })
            categories_set.add((cat_code, cat_name))

    cleaned_categories = [
        {"category_code": c[0], "category_name": c[1]}
        for c in sorted(categories_set, key=lambda x: x[0])
    ]

    return cleaned_products, cleaned_categories


def save_cleaned_products(cleaned_products, output_path="data/gold/dim_products.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["item_code", "item_name", "category_code", "category_name"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_products)


if __name__ == "__main__":
    products, categories = clean_product_data()
    save_cleaned_products(products)
    print(f"Produits nettoyés : {len(products)} articles, {len(categories)} catégories.")
