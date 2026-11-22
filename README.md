# Community Pharmacy Sales & Inventory Analysis (Nigeria, 2025)

**Question:** Which products drive a community pharmacy's revenue and profit, how does demand shift with the seasons, and which stock is at risk of running out or expiring?

> **Data note:** This project uses a **simulated** dataset (40 products, ~71,000 transactions, Jan-Dec 2025) generated in `generate_data.py` with realistic Nigerian prices, malaria-season and harmattan demand patterns, and deliberate data-quality problems. Findings describe the simulated pharmacy, not a real business. The analysis code runs unchanged on real, anonymised pharmacy data with the same columns.

**Tools:** Python (pandas, NumPy, Matplotlib), SQL

## Data cleaning
| Issue | Rows | Action |
|---|---|---|
| Duplicate transaction records (same `transaction_id`) | 40 | Removed |
| Inconsistent product names (UPPERCASE) | 673 | Standardised to inventory names |
| Missing quantity | 60 | Filled with product median |

Identical product/day/quantity rows were kept, because they are separate sales, not duplicates.

## Key findings
1. **Total revenue ₦128.8M, profit ₦41.6M (32.3% margin).**
2. **Revenue concentration:** 23 of 40 products (58%) generate 79% of revenue, so sales are spread fairly broadly, not a classic 80/20 pattern. Artemether/Lumefantrine is the single largest product (₦9.7M).
3. **Seasonality hides inside flat totals:** monthly revenue stays between ₦9.8M and ₦11.3M, but the mix changes. Antimalarial sales run about 2.5x higher in April-October than in the dry months, while cough/cold/allergy sales run about 2x higher in November-February.
4. **Margin vs. volume:** Vitamins/supplements have the best margin (40%) and Cough/Cold/Allergy follows (38%). Antidiabetics have the lowest (22%) because of insulin and test strips, which sell at thin margins but keep patients returning.
5. **Stock-out risk:** 8 products have less stock than their supplier lead time plus 3 days of safety stock requires. 4 of them are class A, including adult cough syrup, which is needed just as the harmattan season starts.
6. **Expiry risk:** 2 products hold more stock than can sell before expiry (Multivitamin, Glibenclamide), a potential write-off of about ₦341,000 at cost.

## Recommendations
- Place reorders now for the 8 at-risk products (`data/inventory_actions.csv`), starting with class A items.
- Pre-stock antimalarials before April and cough/cold products before November, using the seasonality index.
- Run a promotion or bundle on the Multivitamin and return or discount short-dated Glibenclamide to cut expiry loss.
- Review pricing on low-margin, high-volume lines (insulin, test strips) rather than discounting them further.

## Method notes
- Stock-out rule: `days of cover < lead time + 3 days safety stock`, using the average daily demand of the last 90 days.
- Expiry rule: `stock on hand > daily demand x days to expiry`.
- Limitation: demand is averaged over 90 days and ignores promotions or price changes. A next step would be a forecasting model per product.

## Files
`generate_data.py` · `analysis.py` · `sql/queries.sql` · `data/` (raw and output CSVs) · `charts/` (5 PNGs)

## Run it
```
pip install pandas numpy matplotlib
python generate_data.py
python analysis.py
```
