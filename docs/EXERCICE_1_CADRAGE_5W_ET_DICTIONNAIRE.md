# EXERCICE 1 : CADRAGE MÉTIER (5W), DICTIONNAIRE DES DONNÉES & MAQUETTE DÉCISIONNELLE

> **Contexte** : Premier jour en tant qu'Analytics Engineer.  
> **Message Slack du Manager** :  
> *« Salut ! Le Comex trouve que nos ventes des produits frais ne performent pas assez sur certaines catégories. Il me faudrait un truc clair pour demain matin sur ce qui bloque, histoire qu'on sache où agir. Merci ! »*

---

## 1. Compréhension Métier — Méthode des "5W"

| Question | Cadrage Opérationnel | Réponse Stratégique & Décisionnelle |
| :--- | :--- | :--- |
| **Why ?** *(Pourquoi)* | **Pourquoi cette demande ? Qu'est-ce qu'on cherche à accomplir ?** | Le Comité Exécutif (Comex) constate un ralentissement de la performance commerciale sur le rayon des produits frais. L'objectif est d'identifier précisément **quelles catégories sous-performent**, de **diagnostiquer les causes racines** (effondrement des volumes, perte de marge, politique de prix inadaptée, manque d'animation promotionnelle ou explosion de la casse/démarque), et de fournir des **leviers d'action concrets et chiffrés** pour redresser la rentabilité dès demain. |
| **Who ?** *(Qui)* | **Qui est l'audience cible ?** | **Le Comex et la Direction Générale**, ainsi que les **Directeurs Marchandise / Category Managers** du rayon Frais. Cette audience a besoin d'une vue synthétique, sans jargon technique, permettant une prise de décision en **3 secondes chrono** (arbitrage budgétaire, renégociation fournisseur, plan d'action démarque). |
| **What ?** *(Quoi)* | **Quel est le livrable attendu ? Quels KPIs ?** | **Livrables :** Un rapport exécutif synthétique (Slide Deck Comex) et un Dashboard interactif de pilotage.<br>**KPIs Clés (Slide 20) :**<br>1. **Chiffre d'Affaires (CA)** (RMB) & Évolution vs N-1 (%)<br>2. **Marge Brute** (RMB) & Taux de Marge Brute (%)<br>3. **Volume Vendu** (kilos) & Évolution vs N-1 (%)<br>4. **Coût de la Casse / Démarque connue** (RMB) & Taux de Perte moyen (%)<br>5. **Marge Nette après Casse** (RMB) (indicateur de rentabilité réelle)<br>6. **Taux de Remise / Promo** (% du CA remisé) |
| **Where ?** *(Où)* | **Où se trouvent les données ?** | Données multi-sources réparties sur 4 tables du système d'information :<br>1. `transaction.csv` : Système d'encaissement caisses (POS)<br>2. `product.csv` : Référentiel articles et hiérarchie produits (ERP/MDM)<br>3. `price.csv` : Mercuriale des prix d'achat grossiste quotidiens (Système Achats/Supply)<br>4. `loss_rate.csv` : Registre des taux de perte d'exploitation (Gestion des stocks / Qualité) |
| **When ?** *(Quand)* | **Quelle est l'échéance et la période temporelle couverte ?** | **Échéance :** Demain matin à la première heure (livraison sous 24h).<br>**Période d'analyse :** Les 12 derniers mois consolidés (**Juillet 2022 à Juin 2023 - Période N**) comparés aux 12 mois précédents (**Juillet 2021 à Juin 2022 - Période N-1**), avec historique de référence depuis Juillet 2020. |

---

## 2. Compréhension des Données — Dictionnaire des Données

### A. Données Minimales Sources (Tables Brutes)

#### 1. Table `product.csv` (Référentiel Articles)
| Champ | Type | Description | Règle / Format | Exemple | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Item Code` | String / Text | Identifiant unique de l'article (Clé Primaire) | Code numérique standardisé | `102900005115168` | ERP Produit |
| `Item Name` | String / Text | Libellé commercial de l'article | Texte sans caractères parasites | `Niushou Shengcai` | ERP Produit |
| `Category Code` | String / Text | Identifiant de la catégorie de produit | Code hiérarchique | `1011010101` | ERP Produit |
| `Category Name` | String / Text | Nom de la catégorie de produit frais | Nettoyé des espaces insécables | `Flower/Leaf Vegetables` | ERP Produit |

#### 2. Table `loss_rate.csv` (Taux de Démarque / Casse)
| Champ | Type | Description | Règle / Format | Exemple | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Item Code` | String / Text | Identifiant unique du produit (Clé Étrangère) | Nettoyé du BOM `\ufeff` | `102900005115168` | Registre Démarque |
| `Item Name` | String / Text | Libellé du produit | Texte de contrôle | `Niushou Shengcai` | Registre Démarque |
| `Loss Rate (%)` | Float (Décimal) | Taux de perte moyen constaté en rayon | Pourcentage converti (0 à 1) | `4.39` (-> `0.0439`) | Registre Démarque |

#### 3. Table `price.csv` (Mercuriale des Prix d'Achat Grossiste)
| Champ | Type | Description | Règle / Format | Exemple | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Date` | Date (ISO) | Date du cours d'achat | Format `YYYY-MM-DD` | `2020-07-01` | Système Achats |
| `Item Code` | String / Text | Identifiant du produit (Clé Étrangère) | Code numérique | `102900005115762` | Système Achats |
| `Wholesale Price (RMB/kg)` | Float / Decimal | Prix d'achat unitaire au kilo payé au grossiste | Montant en RMB/kg (> 0) | `3.88` | Système Achats |

#### 4. Table `transaction.csv` (Transactions de Caisse)
| Champ | Type | Description | Règle / Format | Exemple | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Date` | Date (ISO) | Date de la transaction | Format `YYYY-MM-DD` | `2022-07-01` | Caisse (POS) |
| `Time` | Time / String | Horodatage précis du passage en caisse | Format `HH:MM:SS.sss` | `09:15:07.924` | Caisse (POS) |
| `Item Code` | String / Text | Identifiant du produit vendu | Référence article | `102900005117056` | Caisse (POS) |
| `Quantity Sold (kilo)` | Float / Decimal | Poids vendu ou retourné en kilogrammes | Quantité brute en kg | `0.396` | Caisse (POS) |
| `Unit Selling Price (RMB/kg)`| Float / Decimal | Prix unitaire de vente au détail TTC en rayon | Montant en RMB/kg | `7.60` | Caisse (POS) |
| `Sale or Return` | String / Enum | Nature du flux en caisse | `'sale'` ou `'return'` | `sale` | Caisse (POS) |
| `Discount (Yes/No)` | Boolean / Flag | Indique si le produit a bénéficié d'une remise | `Yes` / `No` (converti en `True`/`False`) | `No` | Caisse (POS) |

---

### B. Indicateurs Métier Calculés (Couche Gold)

| Indicateur | Type | Formule Métier | Unité | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Quantité Nette Vendue** | Float | `IF(Sale_or_Return == 'return', -Quantity, Quantity)` | kg | Volume net réel sorti du magasin |
| **Chiffre d'Affaires Net (CA)** | Float | `Quantité Nette * Unit_Selling_Price` | RMB | Valeur monétaire réelle des encaissements |
| **Coût d'Achat (COGS)** | Float | `Quantité Nette * Wholesale_Price` | RMB | Coût d'achat grossiste des marchandises vendues |
| **Marge Brute** | Float | `Chiffre d'Affaires Net - COGS` | RMB | Bénéfice brut avant frais d'exploitation |
| **Taux de Marge Brute** | Float (%) | `(Marge Brute / Chiffre d'Affaires Net) * 100` | % | Pourcentage de rentabilité brute |
| **Coût de la Démarque / Casse** | Float | `Quantité Nette * (Loss_Rate / 100) * Wholesale_Price` | RMB | Valeur financière des invendus / avaries jetés |
| **Marge Nette après Casse** | Float | `Marge Brute - Coût de la Démarque` | RMB | Rentabilité économique finale de la catégorie |
| **Taux de Vente Remisée** | Float (%) | `(CA des ventes avec Discount=='Yes' / CA Total) * 100` | % | Intensité promotionnelle |
| **Évolution CA vs N-1** | Float (%) | `((CA_Période_N - CA_Période_N_1) / CA_Période_N_1) * 100` | % | Taux de croissance annuel |
| **Écart CA vs N-1** | Float | `CA_Période_N - CA_Période_N_1` | RMB | Gain ou perte absolu de chiffre d'affaires |

---

## 3. Le Piège : Challenger la Donnée Brute

Avant toute modélisation, l'analyse approfondie des données brutes a révélé **5 pièges et anomalies critiques** :

1. **La gestion des retours clients (`return`) :**  
   461 transactions correspondent à des retours de marchandise. Si elles sont sommées aveuglément en positif, le chiffre d'affaires et le volume sont surévalués. Les retours doivent obligatoirement être **affectés d'un signe négatif** pour obtenir le CA et le volume nets réels.
2. **L'en-tête corrompu par un BOM UTF-8 (`\ufeff`) :**  
   Dans `loss_rate.csv`, la colonne d'identifiant commence par `\ufeffItem Code`. Sans nettoyage UTF-8 (`utf-8-sig`), toute jointure SQL ou Pandas sur `Item Code` échoue silencieusement et renvoie des valeurs nulles.
3. **Les espaces insécables (`\xa0`) dans la hiérarchie produits :**  
   Dans `product.csv`, la catégorie `'Flower/Leaf Vegetables'` contient un espace insécable `\xa0`. Une recherche ou un regroupement avec un espace standard sépare artificiellement la catégorie en deux.
4. **Le formatage string du taux de perte (`Loss Rate (%)`) :**  
   Les valeurs sont stockées avec un espace final (ex: `'4.39 '`). De plus, un taux de perte doit être valorisé en RMB (coût financier) et non seulement en pourcentage, car 5% de perte sur un produit à fort volume coûte beaucoup plus cher que 20% sur un produit de niche.
5. **Désalignement de granularité temporelle :**  
   Les transactions sont enregistrées à la milliseconde (`Time`), alors que les prix grossistes sont journaliers. La fusion doit être faite sur la troncature à la date du jour `(Date, Item Code)`.

---

## 4. La Maquette Visuelle Rapide (Décision en 3 secondes chrono)

Voici la maquette du **Dashboard Décisionnel Comex** conçu pour identifier le problème en 3 secondes :

```
========================================================================================================================
 [TABLEAU DE BORD EXÉCUTIF COMEX] - PERFORMANCE DU RAYON PRODUITS FRAIS (Juillet 2022 - Juin 2023)
========================================================================================================================
 [1. LES 4 KPI CARDS STRATÉGIQUES]
 +--------------------------+--------------------------+--------------------------+--------------------------+
 | CHIFFRE D'AFFAIRES TOTAL | VOLUME TOTAL VENDU       | MARGE NETTE APRÈS CASSE  | COÛT TOTAL DE LA CASSE   |
 |   1 154 272 RMB          |   191 900 kg             |   383 762 RMB            |   63 040 RMB             |
 |   ▲ +24.2% vs N-1        |   ▲ +66.3% vs N-1        |   Taux Net : 33.2%       |   5.5% du CA global      |
 +--------------------------+--------------------------+--------------------------+--------------------------+

 [2. LE GRAPHIQUE D'ARBITRAGE IMMÉDIAT (3 SECONDES)] : MATRICE CROISSANCE CA vs MARGE NETTE
     Taux Marge Nette (%)
          ▲
      45% |                                   [Capsicum] (▲ +22.1% CA | 98.3k RMB Mg Nette)
          |
      35% |          [Cabbage] (▲ +49.8%)     [Flower/Leaf Veg.] (▲ +17.1% | 124.9k RMB Mg Nette)
          |          [Edible Mushroom] (▲ +43.2%)
      25% |          [Aquatic Tuberous] (▲ +38.6% | Casse élevée 10.2k RMB)
          |
       0% |------------------------------------------------------------------------------------>
          |  [Solanum] (Aubergines)   ◄◄◄ ALERTE ROUGE : SEULE CATÉGORIE EN DÉCLIN SÉVÈRE !
     -35% |  ▼ -31.5% CA (-22.8k RMB) | ▼ -30.8% Volume | Promo quasi nulle (0.2%)
          |
         -40%          -20%           0%           +20%          +40%          +60%   Évol CA vs N-1 (%)

 [3. PLAN D'ACTION IMMÉDIAT EN 3 POINTS]
  1. 🚨 RELANCE D'URGENCE SUR LES SOLANUM : CA -31.5% tiré par la chute du Changxianqie (-71.8%). 
     Action : Réactiver les promotions (actuellement à 0.2%) et repositionner le prix face à la concurrence.
  2. 🥬 PLAN ANTI-CASSE SUR LES LÉGUMES FEUILLES : 21 521 RMB perdus en casse (34.1% de toute la casse du magasin).
     Action : Ajuster les cadencements de livraison et instaurer un bradage à J-1 le soir.
  3. 📦 PILOTAGE DU MIX PRIX : Les volumes ont bondi de +66.3% mais le CA n'a crû que de +24.2%.
     Action : Remonter progressivement le prix moyen au kilo sur les produits volumiques (Capsicum / Champignons).
========================================================================================================================
```
