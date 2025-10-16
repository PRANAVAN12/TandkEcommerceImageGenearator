from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["fast_crud_db"]
products_col = db["products"]

# Insert product
def insert_product(data):
    products_col.insert_one(data)

# Get all products
def get_all_products():
    return list(products_col.find({}, {"_id": 0}))

# Delete a column from all products
def delete_column(col_name):
    products_col.update_many({}, {"$unset": {col_name: ""}})

# Update a product by product_code
def update_product(product_code, update_data):
    products_col.update_one({"product_code": product_code}, {"$set": update_data})

# Delete product by code
def delete_product(product_code):
    products_col.delete_one({"product_code": product_code})
