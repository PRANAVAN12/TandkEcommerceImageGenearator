from pymongo import MongoClient, errors

client = MongoClient("mongodb://localhost:27017/")
db = client["fast_crud_db"]
products_col = db["products2"]

# Ensure 'Item Description' is unique (case-insensitive)
products_col.create_index([("Item Description", 1)], unique=True)

def normalize_desc(desc):
    return desc.strip().lower() if desc else ""

# Insert product (avoid duplicates)
def insert_product(data):
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

def get_all_products():
    return list(products_col.find({}, {"_id": 0}))

def delete_column(col_name):
    products_col.update_many({}, {"$unset": {col_name: ""}})

def rename_column(old_name, new_name):
    products_col.update_many({}, {"$rename": {old_name: new_name}})

def update_product(product_code, update_data):
    products_col.update_one({"product_code": product_code}, {"$set": update_data})

def delete_product(product_code):
    products_col.delete_one({"product_code": product_code})
