import pymongo
from pymongo import MongoClient, errors, ASCENDING
from pymongo.collation import Collation
import os
import streamlit as st

# --------------------------
# MongoDB Connection
# --------------------------


MONGO_URI = st.secrets["MONGO"]["URI"]




try:
    # Connect with TLS/SSL and timeout
    client = MongoClient(MONGO_URI, tls=True, serverSelectionTimeoutMS=10000)
    client.server_info()  # Force connection test

    # Database & Collection
    DB_NAME = "fast_crud_db"
    COLLECTION_NAME = "products"
    db = client[DB_NAME]
    products_col = db[COLLECTION_NAME]

    # Ensure case-insensitive unique index on Item Description
    products_col.create_index(
        [("Item Description", ASCENDING)],
        unique=True,
        collation=Collation(locale='en', strength=2)
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
    """Normalize string (lowercase + strip)"""
    return str(desc).strip().lower() if desc else ""


def insert_product(data: dict) -> bool:
    """Insert a product if it does not exist (case-insensitive)"""
    if products_col is None:
        print("⚠️ Database not connected. Skipping insert.")
        return False

    item_desc = normalize_desc(data.get("Item Description", ""))
    if not item_desc:
        return False

    if products_col.find_one({"Item Description": {"$regex": f"^{item_desc}$", "$options": "i"}}):
        print(f"Duplicate found: '{item_desc}' — skipping.")
        return False

    try:
        data["Item Description"] = item_desc
        products_col.insert_one(data)
        return True
    except errors.DuplicateKeyError:
        return False


def get_all_products() -> list:
    """Return all products as a list of dicts (exclude _id)"""
    if products_col is None:
        return []
    return list(products_col.find({}, {"_id": 0}))


def delete_column(col_name: str):
    """Delete a column from all documents"""
    if products_col is not None:
        products_col.update_many({}, {"$unset": {col_name: ""}})


def rename_column(old_name: str, new_name: str):
    """Rename a column across all documents"""
    if products_col is not None:
        products_col.update_many({}, {"$rename": {old_name: new_name}})


def update_product(product_code: str, update_data: dict):
    """Update a product by its product_code"""
    if products_col is not None:
        products_col.update_one({"product_code": product_code}, {"$set": update_data})


def delete_product(product_code: str):
    """Delete a product by its product_code"""
    if products_col is not None:
        products_col.delete_one({"product_code": product_code})
