import csv
from collections import defaultdict

# 1. Product mapping
prod_cat = {}
prod_name = {}
with open('product.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cat = r['Category Name'].replace('\xa0', ' ')
        prod_cat[r['Item Code']] = cat
        prod_name[r['Item Code']] = r['Item Name']

# 2. Loss mapping
loss_map = {}
with open('loss_rate.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        code = r.get('Item Code') or r.get('\ufeffItem Code')
        rate_str = r['Loss Rate (%)'].strip()
        loss_map[code] = float(rate_str)/100.0 if rate_str else 0.0

# 3. Price mapping
price_map = {}
with open('price.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        price_map[(r['Date'], r['Item Code'])] = float(r['Wholesale Price (RMB/kg)'])

data = defaultdict(lambda: {
    'qty': 0.0,
    'ca': 0.0,
    'cogs': 0.0,
    'loss_cost': 0.0,
    'discount_ca': 0.0,
    'trans_count': 0,
    'returns_count': 0
})

with open('transaction (1).csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        d = r['Date']
        if '2022-07-01' <= d <= '2023-06-30':
            period = 'N'
        elif '2021-07-01' <= d <= '2022-06-30':
            period = 'N-1'
        else:
            continue
        
        code = r['Item Code']
        cat = prod_cat.get(code, 'Unknown')
        qty = float(r['Quantity Sold (kilo)'])
        price = float(r['Unit Selling Price (RMB/kg)'])
        is_return = (r['Sale or Return'].strip().lower() == 'return')
        
        if is_return:
            qty = -abs(qty)
            data[(period, cat)]['returns_count'] += 1
        else:
            data[(period, cat)]['trans_count'] += 1
            
        ca = qty * price
        w_price = price_map.get((d, code), 0.0)
        cogs = qty * w_price
        l_rate = loss_map.get(code, 0.0)
        loss_cost = qty * l_rate * w_price
        
        entry = data[(period, cat)]
        entry['qty'] += qty
        entry['ca'] += ca
        entry['cogs'] += cogs
        entry['loss_cost'] += loss_cost
        if r['Discount (Yes/No)'].strip().lower() == 'yes':
            entry['discount_ca'] += ca

cats = sorted(list(set(cat for (p, cat) in data.keys())))
print(f"{'Category':<28} | {'CA N':>9} | {'CA N-1':>9} | {'Evol CA':>8} | {'Vol N':>8} | {'Vol N-1':>8} | {'Evol Vol':>8} | {'Marge N':>9} | {'Taux Mg':>7} | {'Casse N':>8} | {'Mg Nette':>9} | {'Tx Remise':>9}")
print("-" * 150)

total_n = defaultdict(float)
total_n1 = defaultdict(float)

for c in cats:
    n = data[('N', c)]
    n1 = data[('N-1', c)]
    
    for k in ['ca', 'qty', 'cogs', 'loss_cost', 'discount_ca']:
        total_n[k] += n[k]
        total_n1[k] += n1[k]
        
    evol_ca = (n['ca'] - n1['ca']) / n1['ca'] * 100 if n1['ca'] else 0
    evol_vol = (n['qty'] - n1['qty']) / n1['qty'] * 100 if n1['qty'] else 0
    marge_n = n['ca'] - n['cogs']
    tm_pct = (marge_n / n['ca'] * 100) if n['ca'] else 0
    marge_nette = marge_n - n['loss_cost']
    remise_rate = (n['discount_ca'] / n['ca'] * 100) if n['ca'] else 0
    print(f"{c:<28} | {n['ca']:9.0f} | {n1['ca']:9.0f} | {evol_ca:+7.1f}% | {n['qty']:8.0f} | {n1['qty']:8.0f} | {evol_vol:+7.1f}% | {marge_n:9.0f} | {tm_pct:6.1f}% | {n['loss_cost']:8.0f} | {marge_nette:9.0f} | {remise_rate:8.1f}%")

print("-" * 150)
tot_evol_ca = (total_n['ca'] - total_n1['ca']) / total_n1['ca'] * 100
tot_evol_vol = (total_n['qty'] - total_n1['qty']) / total_n1['qty'] * 100
tot_marge = total_n['ca'] - total_n['cogs']
tot_tm = tot_marge / total_n['ca'] * 100
tot_mg_net = tot_marge - total_n['loss_cost']
tot_remise = total_n['discount_ca'] / total_n['ca'] * 100
print(f"{'TOTAL':<28} | {total_n['ca']:9.0f} | {total_n1['ca']:9.0f} | {tot_evol_ca:+7.1f}% | {total_n['qty']:8.0f} | {total_n1['qty']:8.0f} | {tot_evol_vol:+7.1f}% | {tot_marge:9.0f} | {tot_tm:6.1f}% | {total_n['loss_cost']:8.0f} | {tot_mg_net:9.0f} | {tot_remise:8.1f}%")

# Deep dive on Solanum
solanum_items = defaultdict(lambda: {'ca_n': 0.0, 'ca_n1': 0.0, 'vol_n': 0.0, 'vol_n1': 0.0, 'margin_n': 0.0, 'loss_n': 0.0})

with open('transaction (1).csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        d = r['Date']
        code = r['Item Code']
        if prod_cat.get(code) != 'Solanum':
            continue
        p = float(r['Unit Selling Price (RMB/kg)'])
        q = float(r['Quantity Sold (kilo)'])
        if r['Sale or Return'].strip().lower() == 'return':
            q = -abs(q)
        
        ca = p * q
        w_p = price_map.get((d, code), 0.0)
        cogs = q * w_p
        loss = q * loss_map.get(code, 0.0) * w_p
        
        if '2022-07-01' <= d <= '2023-06-30':
            solanum_items[code]['ca_n'] += ca
            solanum_items[code]['vol_n'] += q
            solanum_items[code]['margin_n'] += (ca - cogs)
            solanum_items[code]['loss_n'] += loss
        elif '2021-07-01' <= d <= '2022-06-30':
            solanum_items[code]['ca_n1'] += ca
            solanum_items[code]['vol_n1'] += q

print("\n--- SOLANUM ITEMS BREAKDOWN ---")
print(f"{'Item Name':<35} | {'CA N':>8} | {'CA N-1':>8} | {'Evol CA':>8} | {'Vol N':>8} | {'Vol N-1':>8}")
print("-" * 80)
for code, vals in sorted(solanum_items.items(), key=lambda x: x[1]['ca_n1'], reverse=True):
    name = prod_name[code]
    ca_n = vals['ca_n']
    ca_n1 = vals['ca_n1']
    evol = (ca_n - ca_n1) / ca_n1 * 100 if ca_n1 else 0
    print(f"{name:<35} | {ca_n:8.0f} | {ca_n1:8.0f} | {evol:+7.1f}% | {vals['vol_n']:8.0f} | {vals['vol_n1']:8.0f}")

# Top products by loss across all categories
all_items_loss = defaultdict(lambda: {'loss_n': 0.0, 'ca_n': 0.0, 'margin_n': 0.0, 'cat': ''})
with open('transaction (1).csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        d = r['Date']
        if not ('2022-07-01' <= d <= '2023-06-30'):
            continue
        code = r['Item Code']
        p = float(r['Unit Selling Price (RMB/kg)'])
        q = float(r['Quantity Sold (kilo)'])
        if r['Sale or Return'].strip().lower() == 'return':
            q = -abs(q)
        ca = p * q
        w_p = price_map.get((d, code), 0.0)
        cogs = q * w_p
        loss = q * loss_map.get(code, 0.0) * w_p
        all_items_loss[code]['loss_n'] += loss
        all_items_loss[code]['ca_n'] += ca
        all_items_loss[code]['margin_n'] += (ca - cogs)
        all_items_loss[code]['cat'] = prod_cat.get(code, '')

print("\n--- TOP 10 ITEMS GENERATING THE MOST LOSS / CASSE ---")
print(f"{'Item Name':<35} | {'Category':<25} | {'Loss Cost':>10} | {'CA N':>9} | {'Loss/CA %':>10}")
print("-" * 100)
for code, vals in sorted(all_items_loss.items(), key=lambda x: x[1]['loss_n'], reverse=True)[:10]:
    name = prod_name[code]
    l_c = vals['loss_n']
    ca = vals['ca_n']
    ratio = (l_c / ca * 100) if ca else 0
    print(f"{name:<35} | {vals['cat']:<25} | {l_c:10.0f} | {ca:9.0f} | {ratio:9.1f}%")
