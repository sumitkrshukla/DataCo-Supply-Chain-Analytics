
from pathlib import Path
from getpass import getpass

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "03_Python"
    / "output"
    / "Dataco_Cleaned_Improved.xlsx"
)

DATABASE = "dataco_supply_chain"
TABLE_NAME = "datacosupplychain_clean_sql"

HOST = "localhost"
PORT = 3306
USERNAME = "root"


# ------------------------------------------------
# 2. LOAD CLEANED DATASET
# ------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found: {INPUT_FILE}"
    )

df = pd.read_excel(INPUT_FILE)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ------------------------------------------------
# 3. MYSQL CONNECTION
# ------------------------------------------------

password = getpass("Enter MySQL root password: ")

connection_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=USERNAME,
    password=password,
    host=HOST,
    port=PORT,
    database=DATABASE
)

engine = create_engine(
    connection_url,
    pool_pre_ping=True
)


# ------------------------------------------------
# 4. TEST CONNECTION
# ------------------------------------------------

with engine.connect() as connection:
    connection.execute(text("SELECT 1"))

print("\nMySQL connection successful!")


# ------------------------------------------------
# 5. IMPORT DATA
# ------------------------------------------------

print("\nImporting dataset into MySQL...")

df.to_sql(
    name=TABLE_NAME,
    con=engine,
    if_exists="fail",
    index=False,
    chunksize=200
)

print("Dataset imported successfully!")


# ------------------------------------------------
# 6. VERIFY IMPORT
# ------------------------------------------------

with engine.connect() as connection:

    result = connection.execute(
        text(f"SELECT COUNT(*) FROM `{TABLE_NAME}`")
    )

    imported_rows = result.scalar()

print("\nIMPORT SUMMARY")
print("------------------------------")
print("Expected rows:", len(df))
print("Imported rows:", imported_rows)
print("Columns:", len(df.columns))

if imported_rows != len(df):
    raise ValueError("Imported row count does not match source!")

print("\nDATA IMPORT VERIFIED SUCCESSFULLY!")

engine.dispose()
