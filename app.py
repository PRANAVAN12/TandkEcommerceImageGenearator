import streamlit as st
import pandas as pd
from db import insert_product, get_all_products, delete_column, products_col
from utils import write_excel, generate_short_description, generate_long_description, generate_product_image

st.set_page_config(page_title="Fast CRUD App", layout="wide")
st.title("📦 Fast CRUD App - Image & Description Generator")

if "generated_products" not in st.session_state:
    st.session_state["generated_products"] = []

# -----------------------
# Upload Excel
# -----------------------
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    st.dataframe(df.head(10))

    if st.button("Generate Image & Descriptions"):
        generated_rows = []
        progress_bar = st.progress(0)

        for idx, row in df.iterrows():
            product_dict = row.to_dict()
            item_desc = product_dict.get("Item Description", "").strip().lower()
            product_dict["Item Description"] = item_desc

            # Skip if duplicate in DB
            if products_col.find_one({"Item Description": item_desc}):
                progress_bar.progress((idx + 1) / len(df))
                continue

            # Generate descriptions & image
            product_dict["image_base64"] = generate_product_image(product_dict)
            product_dict["short_description"] = generate_short_description(product_dict)
            product_dict["long_description"] = generate_long_description(product_dict)

            generated_rows.append(product_dict)
            progress_bar.progress((idx + 1) / len(df))

        if generated_rows:
            st.session_state["generated_products"] = generated_rows
            st.success(f"✅ Generated {len(generated_rows)} new products")

            # Preview table
            preview_df = pd.DataFrame(generated_rows).drop(columns=["image_base64"], errors="ignore")
            st.subheader("📝 Generated Products Preview")
            st.dataframe(preview_df)
        else:
            st.info("⚠️ No new products to generate. All exist in DB.")

# -----------------------
# Insert Generated Products
# -----------------------
if st.session_state["generated_products"]:
    if st.button("Insert Generated Products to DB"):
        inserted_count = 0
        skipped_count = 0
        for prod in st.session_state["generated_products"]:
            if insert_product(prod):
                inserted_count += 1
            else:
                skipped_count += 1
        st.success(f"✅ Inserted: {inserted_count}, Skipped (duplicates): {skipped_count}")
        st.session_state["generated_products"] = []

# -----------------------
# View DB
# -----------------------
st.subheader("📝 All Products in DB")
all_products = get_all_products()
if all_products:
    db_df = pd.DataFrame(all_products)
    st.dataframe(db_df)

# -----------------------
# Delete Column
# -----------------------
st.subheader("🗑️ Delete Column from DB")
col_to_delete = st.text_input("Enter column name to delete from all products")
if st.button("Delete Column"):
    delete_column(col_to_delete)
    st.success(f"✅ Column '{col_to_delete}' deleted from all products")

# -----------------------
# Download DB
# -----------------------
st.subheader("⬇️ Download DB as Excel")
if st.button("Download Excel"):
    excel_bytes = write_excel(pd.DataFrame(get_all_products()))
    st.download_button("Download Excel", data=excel_bytes, file_name="products.xlsx")
