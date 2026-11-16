# Exercice 1 : Cadrage métier (5W) et Dictionnaire des données

## Contexte
Premier jour en tant qu'Analytics Engineer.  
Message reçu du manager :  
> « Salut ! Le Comex trouve que nos ventes des produits frais ne performent pas assez sur certaines catégories. Il me faudrait un truc clair pour demain matin sur ce qui bloque, histoire qu'on sache où agir. Merci ! »

---

## 1. Méthode des 5W (Slide 13 & 19)

* **Why (Pourquoi) :**  
  Le Comex constate une baisse de performance sur certaines catégories de produits frais. L'objectif est de trouver quelles catégories posent problème, de comprendre si le blocage vient des volumes, des prix, des promotions ou de la casse, et de proposer des solutions concrètes pour redresser les ventes.

* **Who (Qui) :**  
  L'analyse est destinée au Comex (Comité Exécutif), à la Direction Générale et aux responsables de catégories du rayon frais. Le livrable doit être simple et lisible au premier coup d'œil.

* **What (Quoi) :**  
  * Livrable : Un dashboard de suivi simple (type Power BI) et des indicateurs clairs.
  * KPIs clés (Slide 20) :
    1. Chiffre d'Affaires Net (RMB) et évolution vs N-1 (%)
    2. Volumes vendus (kg) et évolution vs N-1 (%)
    3. Marge brute et taux de marge (%)
    4. Coût de la casse / pertes (RMB)
    5. Taux de remise (%)

* **Where (Où) :**  
  Les données proviennent de 4 fichiers :
  * `transaction.csv` : historique des encaissements en caisse.
  * `product.csv` : liste des produits et catégories.
  * `price.csv` : prix d'achat grossiste journaliers.
  * `loss_rate.csv` : taux de casse moyen par produit.

* **When (Quand) :**  
  * Échéance : Demain matin.
  * Période analysée : Les 12 derniers mois (Juillet 2022 à Juin 2023) comparés aux 12 mois de l'année précédente (Juillet 2021 à Juin 2022).

---

## 2. Dictionnaire des données

### Tables sources :

1. **`product.csv`**
   * `Item Code` (Texte) : Code unique de l'article (ex: `102900005115168`).
   * `Item Name` (Texte) : Nom du légume (ex: `Niushou Shengcai`).
   * `Category Code` (Texte) : Identifiant de la catégorie.
   * `Category Name` (Texte) : Nom de la catégorie (ex: `Flower/Leaf Vegetables`).

2. **`loss_rate.csv`**
   * `Item Code` (Texte) : Code de l'article.
   * `Item Name` (Texte) : Nom de l'article.
   * `Loss Rate (%)` (Nombre) : Pourcentage moyen de casse en rayon (ex: `4.39%`).

3. **`price.csv`**
   * `Date` (Date) : Date du cours grossiste (`YYYY-MM-DD`).
   * `Item Code` (Texte) : Code de l'article.
   * `Wholesale Price (RMB/kg)` (Décimal) : Prix d'achat au kilo payé au grossiste.

4. **`transaction.csv`**
   * `Date` (Date) : Date de l'achat.
   * `Time` (Heure) : Heure de passage en caisse.
   * `Item Code` (Texte) : Code de l'article acheté.
   * `Quantity Sold (kilo)` (Décimal) : Quantité vendue en kg.
   * `Unit Selling Price (RMB/kg)` (Décimal) : Prix de vente unitaire en rayon.
   * `Sale or Return` (Texte) : Type de ligne (`sale` pour une vente, `return` pour un retour client).
   * `Discount (Yes/No)` (Texte) : Indique si une promotion a été appliquée.

### Indicateurs calculés :
* **Quantité nette :** `Quantité` si vente, `- Quantité` si retour client.
* **CA Net :** `Quantité nette * Prix de vente unitaire`.
* **Coût d'achat :** `Quantité nette * Prix grossiste`.
* **Marge brute :** `CA Net - Coût d'achat`.
* **Coût de la casse :** `Quantité nette * (Taux de casse / 100) * Prix grossiste`.
* **Marge nette :** `Marge brute - Coût de la casse`.

---

## 3. Le piège dans les données brutes (Challenger la donnée)

1. **Les retours clients :** 461 lignes correspondent à des retours de marchandise. Si on ne les passe pas en négatif, le chiffre d'affaires et les volumes sont artificiellement gonflés.
2. **Le BOM UTF-8 (`\ufeff`) :** Dans `loss_rate.csv`, le nom de la première colonne contient un caractère invisible qui bloque les jointures si on n'utilise pas l'encodage `utf-8-sig`.
3. **Les espaces insécables (`\xa0`) :** Dans `product.csv`, la catégorie `Flower/Leaf Vegetables` contient un espace spécial qui divise la catégorie en deux lors des groupements.
4. **Le formatage du taux de casse :** Les pourcentages sont écrits sous forme de texte avec des espaces (ex: `'4.39 '`), il faut les nettoyer et les convertir en chiffres décimaux.

---

## 4. Maquette rapide (Décision en 3 secondes)

* **Ce qui saute aux yeux :**
  * La catégorie **Solanum (aubergines)** est la seule en chute libre : **-31.5% de CA** et **-30.8% de volume** par rapport à l'année précédente.
  * La casse totale s'élève à **63 040 RMB**, dont **34%** est concentrée sur les **légumes feuilles**.
* **Action immédiate :** Relancer des promotions sur les aubergines (taux de promo quasi nul à 0.2%) et revoir les quantités de commande sur les salades pour réduire les pertes.
