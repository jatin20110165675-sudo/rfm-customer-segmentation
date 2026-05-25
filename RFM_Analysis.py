import pandas as pd

#----loads the dataset----

df=pd.read_excel('Online Retail.xlsx')

#---Basic Exploration of the data set----

print("Shape:", df.shape)           # rows & columns
print("Columns:", df.columns.tolist())
print("First 5 rows:")
print(df.head())
print("Data types:")
print(df.dtypes)
print("Missing values:")
print(df.isnull().sum())

# ── Data Cleaning ─────────────────────────────

# 1. Drop rows with no CustomerID (can't segment them)
df = df.dropna(subset=['CustomerID'])
print(f"After removing nulls: {len(df)} rows")

# 2. Remove negative quantities (returns/cancellations)
df = df[df['Quantity'] > 0]
print(f"After removing returns: {len(df)} rows")

# 3. Remove negative/zero prices
df = df[df['UnitPrice'] > 0]
print(f"After removing bad prices: {len(df)} rows")

# 4. Convert CustomerID to integer
df['CustomerID'] = df['CustomerID'].astype(int)

# 5. Add TotalPrice column
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']

print(f"Clean dataset: {len(df)} rows, {df['CustomerID'].nunique()} unique customers")

import datetime as dt

# ── RFM Calculation ───────────────────────────

# Reference date = 1 day after last invoice
snapshot_date = df['InvoiceDate'].max() + dt.timedelta(days=1)

# Group by customer and calculate R, F, M
rfm = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days, # Recency
    'InvoiceNo':   'nunique',   # Frequency
    'TotalPrice':  'sum'        # Monetary
}).reset_index()

# Rename columns
rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
rfm['Monetary'] = rfm['Monetary'].round(2)

print("RFM Table (first 5 rows):")
print(rfm.head())
print(f"Total customers: {len(rfm)}")
# ── RFM Scoring (1-3 scale) ───────────────────

# Recency: lower days = better = score 3
rfm['R_Score'] = pd.qcut(rfm['Recency'],
                          q=3,
                          labels=[3, 2, 1])

# Frequency: higher = better = score 3
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'),
                          q=3,
                          labels=[1, 2, 3])

# Monetary: higher = better = score 3
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'),
                          q=3,
                          labels=[1, 2, 3])

# Total RFM score (3 to 9)
rfm['RFM_Score'] = (rfm['R_Score'].astype(int) +
                    rfm['F_Score'].astype(int) +
                    rfm['M_Score'].astype(int))

# Assign segment labels
def assign_segment(score):
    if score >= 7:
        return 'High Value'
    elif score >= 5:
        return 'Mid Value'
    else:
        return 'Low Value'

rfm['Segment'] = rfm['RFM_Score'].apply(assign_segment)

# Print segment distribution
print("Segment Distribution:")
print(rfm['Segment'].value_counts())
print("Average RFM by Segment:")
print(rfm.groupby('Segment')[['Recency','Frequency','Monetary']].mean().round(1))

# ── Export to CSV ─────────────────────────────
rfm.to_csv('rfm_segments.csv', index=False)
print("✓ Saved: rfm_segments.csv")

# ── Export to MySQL ───────────────────────────
from sqlalchemy import create_engine

engine = create_engine(
    'mysql+pymysql://root:Jatin123@localhost/rfm_analysis'
)

# Create database first in MySQL Workbench:
# CREATE DATABASE rfm_analysis;

rfm.to_sql('rfm_segments',
           con=engine,
           if_exists='replace',
           index=False)
print("✓ Saved to MySQL: rfm_analysis.rfm_segments")