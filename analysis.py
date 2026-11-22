import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.dpi":130,"axes.spines.top":False,"axes.spines.right":False,"font.size":10})
TEAL="#0F766E"; GREY="#94A3B8"; RED="#DC2626"; AMB="#D97706"
naira = lambda x,_=None: f"₦{x/1e6:.1f}M"

# ---------- 1. LOAD & CLEAN ----------
sales = pd.read_csv("data/sales.csv", parse_dates=["date"])
inv   = pd.read_csv("data/inventory.csv", parse_dates=["expiry_date"])
log = {"raw_rows": len(sales)}
# identical product/day/qty rows can be genuine separate sales, so de-duplicate on transaction_id only
log["duplicates_removed"] = int(sales.duplicated(subset="transaction_id").sum()); sales = sales.drop_duplicates(subset="transaction_id")
sales["product"] = sales["product"].str.strip()
canon = {p.lower():p for p in inv["product"]}
log["name_fixes"] = int((~sales["product"].isin(canon.values())).sum())
sales["product"] = sales["product"].str.lower().map(canon)
log["missing_qty"] = int(sales["quantity"].isna().sum())
sales["quantity"] = sales["quantity"].fillna(sales.groupby("product")["quantity"].transform("median")).round()
sales["revenue"] = sales.quantity*sales.unit_price
sales["profit"]  = sales.quantity*(sales.unit_price-sales.unit_cost)
sales["month"] = sales.date.dt.to_period("M")
log["clean_rows"] = len(sales)
print("CLEANING LOG", log)

# ---------- 2. KPIs ----------
rev, prof = sales.revenue.sum(), sales.profit.sum()
print(f"Revenue ₦{rev:,.0f} | Profit ₦{prof:,.0f} | Margin {prof/rev:.1%}")

# ---------- 3. MONTHLY TREND & SEASONALITY ----------
m = sales.groupby("month").agg(revenue=("revenue","sum"),profit=("profit","sum"))
m.to_csv("data/monthly_summary.csv")
fig,ax=plt.subplots(figsize=(8,3.8)); ax.bar(m.index.astype(str),m.revenue,color=TEAL)
ax.yaxis.set_major_formatter(naira); ax.set_title("Monthly revenue, 2025"); plt.xticks(rotation=45)
plt.tight_layout(); plt.savefig("charts/1_monthly_revenue.png"); plt.close()

cat_m = sales.pivot_table(index="category",columns=sales.date.dt.month,values="quantity",aggfunc="sum")
cat_idx = cat_m.div(cat_m.mean(axis=1),axis=0)
fig,ax=plt.subplots(figsize=(8,4.2)); im=ax.imshow(cat_idx,cmap="YlGnBu",aspect="auto")
ax.set_yticks(range(len(cat_idx))); ax.set_yticklabels(cat_idx.index)
ax.set_xticks(range(12)); ax.set_xticklabels(["J","F","M","A","M","J","J","A","S","O","N","D"])
ax.set_title("Seasonality index by category (1.0 = category's monthly average)"); plt.colorbar(im)
plt.tight_layout(); plt.savefig("charts/2_seasonality_heatmap.png"); plt.close()

# ---------- 4. PRODUCT PERFORMANCE & ABC (PARETO) ----------
p = sales.groupby(["product","category"]).agg(units=("quantity","sum"),revenue=("revenue","sum"),profit=("profit","sum")).reset_index()
p["margin"]=p.profit/p.revenue
p = p.sort_values("revenue",ascending=False).reset_index(drop=True)
p["cum_share"]=p.revenue.cumsum()/p.revenue.sum()
p["abc"]=np.where(p.cum_share<=.8,"A",np.where(p.cum_share<=.95,"B","C"))
p.to_csv("data/product_performance.csv",index=False)
nA=(p.abc=="A").sum(); print(f"A-class: {nA} of {len(p)} products = {p[p.abc=='A'].revenue.sum()/p.revenue.sum():.0%} revenue")
print(p.head(8)[["product","revenue","margin"]])
fig,ax=plt.subplots(figsize=(8,4)); ax.bar(range(len(p)),p.revenue,color=[TEAL if a=="A" else GREY for a in p.abc])
ax.yaxis.set_major_formatter(naira); ax2=ax.twinx(); ax2.plot(range(len(p)),p.cum_share*100,color=AMB,marker="o",ms=3)
ax2.axhline(80,ls="--",color=RED,lw=.8); ax2.set_ylabel("Cumulative % of revenue"); ax.set_xlabel("Products ranked by revenue")
ax.set_title("Pareto: a few products drive most revenue (teal = class A)"); plt.tight_layout(); plt.savefig("charts/3_pareto_abc.png"); plt.close()

cat = sales.groupby("category").agg(revenue=("revenue","sum"),profit=("profit","sum")); cat["margin"]=cat.profit/cat.revenue
cat=cat.sort_values("revenue"); print(cat.assign(share=cat.revenue/rev).round(3))
fig,ax=plt.subplots(figsize=(8,4)); ax.barh(cat.index,cat.revenue,color=TEAL)
for i,(r,mg) in enumerate(zip(cat.revenue,cat.margin)): ax.text(r,i,f"  {mg:.0%} margin",va="center",fontsize=8)
ax.xaxis.set_major_formatter(naira); ax.set_title("Revenue and margin by category"); plt.tight_layout(); plt.savefig("charts/4_category_margin.png"); plt.close()

# ---------- 5. INVENTORY RISK ----------
last90 = sales[sales.date>"2025-10-02"].groupby("product").quantity.sum()/90
inv["daily_demand"]=inv["product"].map(last90)
inv["days_of_cover"]=inv.stock_on_hand/inv.daily_demand
inv["reorder_point"]=np.ceil(inv.daily_demand*(inv.supplier_lead_time_days+3))  # +3 days safety stock
inv["stockout_risk"]=inv.days_of_cover<inv.supplier_lead_time_days+3
snap=pd.Timestamp("2026-01-01")
inv["days_to_expiry"]=(inv.expiry_date-snap).dt.days
inv["units_sellable_before_expiry"]=inv.daily_demand*inv.days_to_expiry
inv["expiry_risk"]=inv.stock_on_hand>inv.units_sellable_before_expiry
inv["expiry_loss_ngn"]=np.where(inv.expiry_risk,(inv.stock_on_hand-inv.units_sellable_before_expiry)*inv.unit_cost,0)
inv["order_qty"]=np.where(inv.stockout_risk,np.ceil(inv.daily_demand*30-inv.stock_on_hand),0).clip(min=0)
inv=inv.merge(p[["product","abc"]],on="product")
inv.to_csv("data/inventory_actions.csv",index=False,float_format="%.1f")
print("Stock-out risk:",inv.stockout_risk.sum(),"| A-class at risk:",((inv.abc=="A")&inv.stockout_risk).sum())
print("Expiry risk:",inv.expiry_risk.sum(),"| potential write-off ₦",round(inv.expiry_loss_ngn.sum()))
print(inv[inv.stockout_risk].sort_values("days_of_cover")[["product","abc","days_of_cover","supplier_lead_time_days","order_qty"]].head(10).round(1))
print(inv[inv.expiry_risk].sort_values("expiry_loss_ngn",ascending=False)[["product","days_to_expiry","stock_on_hand","expiry_loss_ngn"]].head(6).round(0))

fig,ax=plt.subplots(figsize=(7,4.5))
c=np.where(inv.stockout_risk,RED,np.where(inv.expiry_risk,AMB,TEAL))
ax.scatter(inv.days_of_cover,inv.days_to_expiry,c=c,s=45)
ax.set_xlabel("Days of stock cover"); ax.set_ylabel("Days to expiry"); ax.set_title("Inventory risk map (red = stock-out risk, amber = expiry risk)")
plt.tight_layout(); plt.savefig("charts/5_inventory_risk.png"); plt.close()
