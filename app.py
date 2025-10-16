import streamlit as st
import pandas as pd
from db import insert_product, get_all_products, delete_product, update_product, delete_column
from utils import write_excel, image_to_base64

st.set_page_config(page_title="Fast CRUD App", layout="wide")
st.title("📦 Fast CRUD App with MongoDB")

# -----------------------
# Upload Excel / Insert
# -----------------------
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    st.dataframe(df.head(10))

    if st.button("Insert to DB"):
        for _, row in df.iterrows():
            # Optional: convert local image paths to base64
            if "image_path" in row and pd.notna(row["image_path"]):
                row["image_base64"] = image_to_base64(row["image_path"])
            insert_product(row.to_dict())
        st.success("✅ Products added to DB")

# -----------------------
# View Products
# -----------------------
st.subheader("📝 View Products")
all_products = get_all_products()
if all_products:
    view_df = pd.DataFrame(all_products)
    st.dataframe(view_df.head(20))

    # Show images for first 20 rows
    for idx, row in view_df.head(20).iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            if "image_base64" in row and row["image_base64"]:
                st.image(row["image_base64"], width=100)
        with col2:
            st.write(row)

# -----------------------
# Delete Row
# -----------------------
st.subheader("🗑️ Delete Product by Code")
del_code = st.text_input("Enter product_code to delete")
if st.button("Delete Product"):
    delete_product(del_code)
    st.success(f"✅ Product with code {del_code} deleted")

# -----------------------
# Update Row
# -----------------------
st.subheader("✏️ Update Product")
update_code = st.text_input("Enter product_code to update")
if update_code:
    product = [p for p in all_products if p["product_code"] == update_code]
    if product:
        product = product[0]
        new_name = st.text_input("New Product Name", value=product.get("product_name", ""))
        new_price = st.number_input("New Price", value=float(product.get("price", 0)))
        if st.button("Update Product"):
            update_product(update_code, {"product_name": new_name, "price": new_price})
            st.success(f"✅ Product {update_code} updated")

# -----------------------
# Delete Column
# -----------------------
st.subheader("🗑️ Delete Column from DB")
col_to_delete = st.text_input("Enter column name to delete from all products")
if st.button("Delete Column"):
    delete_column(col_to_delete)
    st.success(f"✅ Column '{col_to_delete}' deleted from all products")

# -----------------------
# Download DB as Excel
# -----------------------
st.subheader("⬇️ Download DB")
if st.button("Download Excel"):
    df_all = pd.DataFrame(get_all_products())
    excel_bytes = write_excel(df_all)
    st.download_button("Download Excel", data=excel_bytes, file_name="products.xlsx")
