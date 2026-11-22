"""Generates a SIMULATED community-pharmacy dataset (Nigeria, 2025).
Replace data/sales.csv and data/inventory.csv with real/anonymised data to reuse the analysis."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)

# product, category, unit_price (NGN), margin, avg daily units, seasonality profile
P = [
 ("Artemether/Lumefantrine 80/480mg","Antimalarial",2800,.28,9,"rain"),
 ("Artesunate/Amodiaquine","Antimalarial",1800,.30,6,"rain"),
 ("Sulfadoxine/Pyrimethamine","Antimalarial",900,.32,3,"rain"),
 ("Paracetamol 500mg (strip)","Analgesic",300,.35,40,"flat"),
 ("Ibuprofen 400mg (strip)","Analgesic",500,.33,14,"flat"),
 ("Diclofenac 50mg (strip)","Analgesic",600,.34,10,"flat"),
 ("Tramadol 50mg (strip)","Analgesic",1200,.25,4,"flat"),
 ("Amoxicillin 500mg (strip)","Antibiotic",1500,.30,12,"flat"),
 ("Ciprofloxacin 500mg (strip)","Antibiotic",1800,.30,8,"flat"),
 ("Metronidazole 400mg (strip)","Antibiotic",700,.35,11,"flat"),
 ("Azithromycin 500mg","Antibiotic",3200,.27,5,"flat"),
 ("Ampicillin/Cloxacillin caps","Antibiotic",1400,.31,7,"flat"),
 ("Amlodipine 10mg (strip)","Antihypertensive",1800,.26,6,"flat"),
 ("Lisinopril 10mg (strip)","Antihypertensive",2200,.25,4,"flat"),
 ("Losartan 50mg (strip)","Antihypertensive",2500,.25,5,"flat"),
 ("Hydrochlorothiazide 25mg","Antihypertensive",1000,.30,3,"flat"),
 ("Metformin 500mg (strip)","Antidiabetic",1300,.27,6,"flat"),
 ("Glibenclamide 5mg (strip)","Antidiabetic",900,.30,3,"flat"),
 ("Insulin 30/70 vial","Antidiabetic",6500,.15,1.2,"flat"),
 ("Vitamin C 1000mg (tube)","Vitamin/Supplement",2500,.40,7,"cold"),
 ("Multivitamin (bottle)","Vitamin/Supplement",3500,.42,5,"flat"),
 ("Folic Acid 5mg","Vitamin/Supplement",500,.38,4,"flat"),
 ("Ferrous Sulphate/Folic Acid","Vitamin/Supplement",800,.38,5,"flat"),
 ("Zinc 20mg dispersible","Vitamin/Supplement",900,.36,4,"rain"),
 ("Omeprazole 20mg (strip)","Gastrointestinal",1000,.34,13,"flat"),
 ("ORS sachet","Gastrointestinal",250,.40,18,"rain"),
 ("Loperamide 2mg","Gastrointestinal",600,.35,4,"rain"),
 ("Antacid suspension","Gastrointestinal",1100,.36,6,"flat"),
 ("Loratadine 10mg (strip)","Cough/Cold/Allergy",800,.37,8,"cold"),
 ("Cetirizine 10mg (strip)","Cough/Cold/Allergy",700,.37,9,"cold"),
 ("Cough syrup (adult)","Cough/Cold/Allergy",1800,.38,10,"cold"),
 ("Cough syrup (paediatric)","Cough/Cold/Allergy",1900,.38,7,"cold"),
 ("Chlorpheniramine 4mg","Cough/Cold/Allergy",300,.40,12,"cold"),
 ("Levonorgestrel 1.5mg","Reproductive health",1500,.35,5,"flat"),
 ("Combined oral contraceptive","Reproductive health",1200,.33,6,"flat"),
 ("Hydrocortisone cream","Dermatology",1100,.36,5,"cold"),
 ("Clotrimazole cream","Dermatology",1200,.37,6,"flat"),
 ("Povidone iodine 100ml","First aid/Consumables",1500,.35,4,"flat"),
 ("Blood glucose test strips (50)","First aid/Consumables",8500,.20,1.5,"flat"),
 ("Digital thermometer","First aid/Consumables",3000,.40,1.5,"flat"),
]
def season(kind, m):
    if kind=="rain": return 1.45 if 4<=m<=10 else 0.6
    if kind=="cold": return 1.6 if (m>=11 or m<=2) else 0.75
    return 1.0

days = pd.date_range("2025-01-01","2025-12-31")
rows=[]
for name,cat,price,margin,lam,kind in P:
    cost = round(price*(1-margin),0)
    for d in days:
        wk = 1.15 if d.dayofweek in (4,5) else (0.85 if d.dayofweek==6 else 1.0)
        mean = lam*season(kind,d.month)*wk
        # transactions per day; qty per transaction 1-3
        n = rng.poisson(mean/1.6)
        if n==0: continue
        qty = rng.choice([1,2,3],size=n,p=[.6,.28,.12])
        for q in qty:
            rows.append((d,name,cat,int(q),price,cost))
sales = pd.DataFrame(rows,columns=["date","product","category","quantity","unit_price","unit_cost"])
sales.insert(0,"transaction_id",[f"TX{i:06d}" for i in range(1,len(sales)+1)])
# real-world messiness
sales.loc[rng.choice(sales.index,60,replace=False),"quantity"] = np.nan
sales = pd.concat([sales, sales.sample(40,random_state=1)])  # duplicate rows
sales["product"] = sales["product"].where(rng.random(len(sales))>0.01, sales["product"].str.upper())
sales = sales.sort_values("date").reset_index(drop=True)
sales.to_csv("data/sales.csv",index=False)

inv=[]
for name,cat,price,margin,lam,kind in P:
    cover = rng.choice([4,8,14,25,40,70],p=[.12,.2,.25,.18,.15,.1])  # days of cover on hand
    stock = int(lam*cover)
    lead = int(rng.choice([2,3,5,7,10]))
    expiry = pd.Timestamp("2026-01-01")+pd.Timedelta(days=int(rng.choice([20,45,75,120,200,400,600],p=[.06,.1,.12,.2,.22,.2,.1])))
    inv.append((name,stock,lead,expiry.date(),round(price*(1-margin))))
pd.DataFrame(inv,columns=["product","stock_on_hand","supplier_lead_time_days","expiry_date","unit_cost"]).to_csv("data/inventory.csv",index=False)
print(len(sales),"sales rows")
