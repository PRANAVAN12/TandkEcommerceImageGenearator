import os
import pymongo
from pymongo import MongoClient, errors, ASCENDING
from pymongo.collation import Collation
import streamlit as st
from dotenv import load_dotenv

# --------------------------
# Load environment variables (for local use)
# --------------------------
load_dotenv()

# --------------------------
# MongoDB Connection
# --------------------------

# Try to read from Streamlit secrets (for production)
try:
    MONGO_URI = st.secrets["MONGO"]["URI"]
except Exception:
    # Fallback for local .env
    MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ No MongoDB URI found. Set it in .env or Streamlit secrets.")

try:
    # Connect with TLS/SSL and timeout
    client = MongoClient(MONGO_URI, tls=True, serverSelectionTimeoutMS=10000)
    client.server_info()  # Force connection test

    DB_NAME = "fast_crud_db"
    COLLECTION_NAME = "products1"
    db = client[DB_NAME]
    products_col = db[COLLECTION_NAME]

    # Ensure case-insensitive unique index
    products_col.create_index(
        [("Item Description", ASCENDING)],
        unique=True,
        collation=Collation(locale="en", strength=2)
    )
    print(f"✅ Connected to MongoDB: DB='{DB_NAME}', Collection='{COLLECTION_NAME}'")

except errors.ServerSelectionTimeoutError as e:
    print("❌ Database connection failed:", e)
    client = None
    db = None
    products_col = None
except Exception as e:
    print("❌ Unexpected error:", e)
    client = None
    db = None
    products_col = None


# --------------------------
# Utility functions
# --------------------------

def normalize_desc(desc: str) -> str:
    return str(desc).strip().lower() if desc else ""


def insert_product(data: dict) -> bool:
    if products_col is None:
        print("⚠️ Database not connected.")
        return False
    item_desc = normalize_desc(data.get("Item Description", ""))
    if not item_desc:
        return False
    if products_col.find_one({"Item Description": {"$regex": f"^{item_desc}$", "$options": "i"}}):
        print(f"Duplicate found: '{item_desc}'")
        return False
    try:
        data["Item Description"] = item_desc
        products_col.insert_one(data)
        return True
    except errors.DuplicateKeyError:
        return False


def get_all_products() -> list:
    if products_col is None:
        return []
    return list(products_col.find({}, {"_id": 0}))


def delete_column(col_name: str):
    if products_col is not None:
        products_col.update_many({}, {"$unset": {col_name: ""}})


def rename_column(old_name: str, new_name: str):
    if products_col is not None:
        products_col.update_many({}, {"$rename": {old_name: new_name}})


def update_product(product_code: str, update_data: dict):
    if products_col is not None:
        products_col.update_one({"product_code": product_code}, {"$set": update_data})


def delete_product(product_code: str):
    if products_col is not None:
        products_col.delete_one({"product_code": product_code})
