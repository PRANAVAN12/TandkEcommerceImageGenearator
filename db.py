from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"  # change if using Atlas
client = MongoClient(MONGO_URI)
db = client["fast_crud_db"]
collection = db["productwws"]

def insert_product(product: dict):
    """Insert product if it doesn't exist"""
    unique_field = "Item Description"  # replace with your unique column
    if not products_col.find_one({unique_field: product[unique_field]}):
        products_col.insert_one(product)

def get_all_products():
    return list(collection.find({}, {"_id": 0}))

def update_product(product_name: str, update_data: dict):
    collection.update_one({"product_name": product_name}, {"$set": update_data})

def delete_column(column_name: str):
    collection.update_many({}, {"$unset": {column_name: ""}})
