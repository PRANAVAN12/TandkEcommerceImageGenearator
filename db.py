from pymongo import MongoClient, errors

client = MongoClient("mongodb://localhost:27017/")
db = client["fast_crud_db"]
products_col = db["products2"]

# Ensure Item Description is unique
products_col.create_index("Item Description", unique=True)

def insert_product(data):
    """Insert product if not duplicate (case-insensitive)."""
    item_desc = data.get("Item Description", "").strip().lower()
    if not item_desc:
        return False
    data["Item Description"] = item_desc
    try:
        products_col.insert_one(data)
        return True
    except errors.DuplicateKeyError:
        return False

def get_all_products():
    return list(products_col.find({}, {"_id": 0}))

def delete_column(col_name):
    products_col.update_many({}, {"$unset": {col_name: ""}})

def update_product(product_code, update_data):
    products_col.update_one({"product_code": product_code}, {"$set": update_data})

def delete_product(product_code):
    products_col.delete_one({"product_code": product_code})
