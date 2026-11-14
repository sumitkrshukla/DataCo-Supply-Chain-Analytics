
"""
DataCo Supply Chain Analytics
Improved Data Cleaning, Validation and Exploratory Data Analysis

Input: 01_Data_Sample/Dataco_sample..xlsx
Outputs: 03_Python/output/
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "01_Data_Sample" / "Dataco_sample..xlsx"

OUTPUT_DIR = PROJECT_ROOT / "03_Python" / "output"
CHART_DIR = OUTPUT_DIR / "visualizations"

CLEANED_FILE = OUTPUT_DIR / "Dataco_Cleaned_Improved.xlsx"
QUALITY_REPORT = OUTPUT_DIR / "Data_Quality_Report.xlsx"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="deep")


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\n" + "=" * 60)
print("DATACO SUPPLY CHAIN ANALYTICS")
print("=" * 60)

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input dataset not found: {INPUT_FILE}")

df = pd.read_excel(INPUT_FILE)

print(f"\nDataset loaded successfully.")
print(f"Original rows: {df.shape[0]:,}")
print(f"Original columns: {df.shape[1]}")


# ============================================================
# 3. INITIAL DATA QUALITY ASSESSMENT
# ============================================================

initial_shape = df.shape

missing_before = df.isnull().sum()
duplicate_count = int(df.duplicated().sum())

print("\n--- Initial Data Quality ---")
print(f"Missing values: {missing_before.sum():,}")
print(f"Duplicate rows: {duplicate_count:,}")

print("\nDataset information:")
df.info()

print("\nDescriptive statistics:")
print(df.describe(include="all").T)


# ============================================================
# 4. VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [
    "Order Id",
    "Customer Id",
    "Delivery Status",
    "Late_delivery_risk",
    "Shipping Mode",
    "Sales",
    "Order Item Total",
    "Order Item Discount",
    "Order Item Product Price",
    "Order Item Quantity",
    "Order Profit Per Order",
    "Benefit per order",
    "order date (DateOrders)",
    "shipping date (DateOrders)"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns missing from dataset: {missing_columns}"
    )


# ============================================================
# 5. REMOVE UNNECESSARY AND SENSITIVE COLUMNS
# ============================================================

columns_to_remove = [
    "Product Description",
    "Order Zipcode",
    "Customer Email",
    "Customer Password",
    "Product Image",
    "Customer Street"
]

existing_columns_to_remove = [
    column for column in columns_to_remove
    if column in df.columns
]

df = df.drop(columns=existing_columns_to_remove)

print("\n--- Column Removal ---")
print("Removed columns:", existing_columns_to_remove)
print(f"Remaining columns: {df.shape[1]}")


# ============================================================
# 6. HANDLE MISSING VALUES
# ============================================================

if "Customer Lname" in df.columns:
    df["Customer Lname"] = df["Customer Lname"].fillna("Unknown")

remaining_missing = df.isnull().sum()

print("\n--- Missing Values After Cleaning ---")
print(remaining_missing[remaining_missing > 0])

if remaining_missing.sum() > 0:
    print(
        "\nNote: Remaining missing values have been reported "
        "and are not automatically filled."
    )


# ============================================================
# 7. CONVERT AND VALIDATE DATE COLUMNS
# ============================================================

date_columns = [
    "order date (DateOrders)",
    "shipping date (DateOrders)"
]

date_conversion_errors = {}

for column in date_columns:
    original_non_null = df[column].notna()

    df[column] = pd.to_datetime(
        df[column],
        format="mixed",
        errors="coerce"
    )

    invalid_count = int(
        (original_non_null & df[column].isna()).sum()
    )

    date_conversion_errors[column] = invalid_count

    if invalid_count > 0:
        raise ValueError(
            f"{invalid_count} invalid dates found in {column}"
        )

print("\n--- Date Validation ---")

for column in date_columns:
    print(f"{column}: {df[column].dtype}")
    print(f"Missing dates: {df[column].isna().sum()}")


# ============================================================
# 8. DUPLICATE AND ORDER-LEVEL VALIDATION
# ============================================================

# Duplicate rows are reported, not automatically deleted.
# This avoids removing potentially valid transactions.

duplicate_count_after = int(df.duplicated().sum())

order_consistency_columns = [
    "Customer Id",
    "Shipping Mode",
    "Delivery Status",
    "Late_delivery_risk"
]

order_consistency = (
    df.groupby("Order Id")[order_consistency_columns]
    .nunique()
)

inconsistent_orders = int(
    (order_consistency > 1).any(axis=1).sum()
)

total_orders = int(df["Order Id"].nunique())

print("\n--- Order-Level Validation ---")
print(f"Unique orders: {total_orders:,}")
print(f"Rows / order items: {len(df):,}")
print(f"Duplicate rows: {duplicate_count_after:,}")
print(f"Orders with inconsistent attributes: {inconsistent_orders:,}")


# ============================================================
# 9. FINANCIAL VALIDATION
# ============================================================

gross_sales_calculated = (
    df["Order Item Product Price"] * df["Order Item Quantity"]
)

sales_matches = (
    df["Sales"].round(2) == gross_sales_calculated.round(2)
)

profit_matches = (
    df["Order Profit Per Order"].round(2)
    == df["Benefit per order"].round(2)
)

financial_validation = {
    "Sales matches price × quantity": int(sales_matches.sum()),
    "Profit matches benefit per order": int(profit_matches.sum()),
    "Total rows": len(df)
}

print("\n--- Financial Validation ---")
print(
    f"Sales formula matches: "
    f"{sales_matches.sum():,}/{len(df):,}"
)
print(
    f"Profit formula matches: "
    f"{profit_matches.sum():,}/{len(df):,}"
)

# Report the discount relationship without assuming exact equality.
discount_difference = (
    gross_sales_calculated
    - df["Order Item Discount"]
    - df["Order Item Total"]
)

print(
    "Maximum absolute discount calculation difference:",
    round(discount_difference.abs().max(), 2)
)


# ============================================================
# 10. EXPORT CLEANED DATA
# ============================================================

df.to_excel(CLEANED_FILE, index=False)

print("\nCleaned dataset exported:")
print(CLEANED_FILE)


# ============================================================
# 11. ORDER-LEVEL ANALYSIS
# ============================================================

# One row per Order Id for order-level charts.
# First, verify the attributes are consistent within each order.

if inconsistent_orders > 0:
    raise ValueError(
        "Order-level attributes are inconsistent. "
        "Review the affected orders before aggregating."
    )

orders = (
    df.groupby("Order Id", as_index=False)
    .agg({
        "Customer Id": "first",
        "Delivery Status": "first",
        "Late_delivery_risk": "first",
        "Shipping Mode": "first"
    })
)

print("\n--- Order-Level Summary ---")
print(f"Total unique orders: {len(orders):,}")

print("\nDelivery status distribution:")
print(orders["Delivery Status"].value_counts())

print("\nShipping mode distribution:")
print(orders["Shipping Mode"].value_counts())

print("\nLate delivery risk distribution:")
print(orders["Late_delivery_risk"].value_counts())


# ============================================================
# 12. VISUALIZATION 1: DELIVERY STATUS DISTRIBUTION
# ============================================================

delivery_counts = (
    orders["Delivery Status"]
    .value_counts()
    .sort_values(ascending=False)
)

plt.figure(figsize=(9, 5))

sns.barplot(
    x=delivery_counts.index,
    y=delivery_counts.values
)

plt.title("Order Distribution by Delivery Status")
plt.xlabel("Delivery Status")
plt.ylabel("Number of Unique Orders")
plt.xticks(rotation=15, ha="right")

plt.tight_layout()

plt.savefig(
    CHART_DIR / "Delivery_Status_Distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 13. VISUALIZATION 2: LATE DELIVERY RISK
# ============================================================

risk_counts = (
    orders["Late_delivery_risk"]
    .value_counts()
    .reindex([0, 1], fill_value=0)
)

risk_labels = ["No Risk", "Late Risk"]

late_risk_percentage = (
    orders["Late_delivery_risk"].mean() * 100
)

print(f"Late Delivery Risk: {late_risk_percentage:.2f}%")

plt.figure(figsize=(7, 5))

sns.barplot(
    x=risk_labels,
    y=risk_counts.values
)

plt.title("Late Delivery Risk Distribution")
plt.xlabel("Delivery Risk")
plt.ylabel("Number of Unique Orders")

plt.tight_layout()

plt.savefig(
    CHART_DIR / "Late_Delivery_Risk.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 14. VISUALIZATION 3: SHIPPING MODE DISTRIBUTION
# ============================================================

shipping_counts = (
    orders["Shipping Mode"]
    .value_counts()
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))

sns.barplot(
    x=shipping_counts.index,
    y=shipping_counts.values
)

plt.title("Order Distribution by Shipping Mode")
plt.xlabel("Shipping Mode")
plt.ylabel("Number of Unique Orders")
plt.xticks(rotation=15, ha="right")

plt.tight_layout()

plt.savefig(
    CHART_DIR / "Shipping_Mode_Distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 15. VISUALIZATION 4: GROSS SALES DISTRIBUTION
# ============================================================

plt.figure(figsize=(9, 5))

sns.histplot(
    data=df,
    x="Sales",
    bins=30,
    kde=True
)

plt.title("Gross Sales Distribution at Order-Item Level")
plt.xlabel("Gross Sales")
plt.ylabel("Number of Order Items")

plt.tight_layout()

plt.savefig(
    CHART_DIR / "Sales_Distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 16. DATA QUALITY REPORT
# ============================================================

quality_summary = pd.DataFrame({
    "Metric": [
        "Original Rows",
        "Original Columns",
        "Rows After Cleaning",
        "Columns After Cleaning",
        "Missing Values Before Cleaning",
        "Missing Values After Cleaning",
        "Duplicate Rows",
        "Unique Orders",
        "Inconsistent Orders",
        "Invalid Order Dates",
        "Invalid Shipping Dates",
        "Sales Formula Matches",
        "Profit Formula Matches"
    ],
    "Value": [
        initial_shape[0],
        initial_shape[1],
        df.shape[0],
        df.shape[1],
        int(missing_before.sum()),
        int(df.isnull().sum().sum()),
        duplicate_count_after,
        total_orders,
        inconsistent_orders,
        date_conversion_errors[date_columns[0]],
        date_conversion_errors[date_columns[1]],
        financial_validation["Sales matches price × quantity"],
        financial_validation["Profit matches benefit per order"]
    ]
})

with pd.ExcelWriter(QUALITY_REPORT) as writer:
    quality_summary.to_excel(
        writer,
        sheet_name="Quality Summary",
        index=False
    )

    missing_before.rename("Missing Values").to_frame().to_excel(
        writer,
        sheet_name="Missing Before"
    )

    df.isnull().sum().rename("Missing Values").to_frame().to_excel(
        writer,
        sheet_name="Missing After"
    )

    order_consistency.to_excel(
        writer,
        sheet_name="Order Consistency"
    )


# ============================================================
# 17. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("PYTHON PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 60)

print(f"Cleaned dataset: {CLEANED_FILE}")
print(f"Quality report: {QUALITY_REPORT}")
print(f"Visualizations: {CHART_DIR}")

print("\nFinal dataset shape:", df.shape)
print("Unique orders:", total_orders)
print("Total gross sales:", round(df["Sales"].sum(), 2))
print("Total discount-adjusted item value:", round(df["Order Item Total"].sum(), 2))
print("Total profit:", round(df["Order Profit Per Order"].sum(), 2))
