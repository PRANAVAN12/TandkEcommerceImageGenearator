import streamlit as st
import pandas as pd
from db import insert_product, get_all_products, delete_column, update_product
from utils import write_excel, image_to_base64, generate_short_description, generate_long_description, generate_product_image

st.set_page_config(page_title="Fast CRUD App", layout="wide")
st.title("📦 Fast CRUD App - Image & Description Generator")

# -----------------------
# Upload Excel / Insert
# -----------------------
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    st.dataframe(df.head(10))

    if st.button("Insert to DB"):
        for _, row in df.iterrows():
            # Only insert if product_code doesn't exist
            insert_product(row.to_dict())
        st.success("✅ Products added to DB")

# -----------------------
# View Products
# -----------------------
st.subheader("📝 View Products")
all_products = get_all_products()
if all_products:
    df_all = pd.DataFrame(all_products)
    st.dataframe(df_all.head(20))

    # Dropdown to select action
    action = st.selectbox(
        "Select action to perform for imported products:",
        ["Generate Image", "Generate Short Description", "Generate Long Description"]
    )

    # Handle missing columns safely
    image_col = df_all.get("image_base64", pd.Series([None]*len(df_all)))
    short_desc_col = df_all.get("short_description", pd.Series([None]*len(df_all)))
    long_desc_col = df_all.get("long_description", pd.Series([None]*len(df_all)))

    # Filter rows needing generation
    rows_to_generate = df_all[
   
    ((action == "Generate Image") & (image_col.isna())) |
    ((action == "Generate Short Description") & (short_desc_col.isna())) |
    ((action == "Generate Long Description") & (long_desc_col.isna()))


    ]

    st.info(f"✅ {len(rows_to_generate)} products need {action.lower()} generation")

    if st.button(f"Start {action} Generation"):
        progress_bar = st.progress(0)
        for i, row in rows_to_generate.iterrows():
            product_code = row["Item Description"]
            update_data = {}

            if action == "Generate Image":
                img_base64 = generate_product_image(row)
                update_data["image_base64"] = img_base64

            elif action == "Generate Short Description":
                short_desc = generate_short_description(row)
                update_data["short_description"] = short_desc

            elif action == "Generate Long Description":
                long_desc = generate_long_description(row)
                update_data["long_description"] = long_desc

            # Update DB
            update_product(product_code, update_data)
            progress_bar.progress((i+1)/len(rows_to_generate))

        st.success(f"✅ {action} generation completed!")

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
