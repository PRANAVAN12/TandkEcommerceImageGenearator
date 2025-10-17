import streamlit as st
import pandas as pd
from db import insert_product, get_all_products, delete_column, products_col
from utils import write_excel, generate_product_image, generate_short_description, generate_long_description, init_gemini_client
from io import BytesIO
import base64

st.set_page_config(page_title="Fast CRUD App", layout="wide")
st.title("📦 Fast CRUD App - Image & Description Generator")

# -----------------------------
# Gemini API Key
# -----------------------------
api_key = st.text_input("Enter your Google Gemini API Key", type="password")
client = init_gemini_client(api_key) if api_key else None

# -----------------------------
# Sidebar Calculator
# -----------------------------
st.sidebar.header("💰 Gemini Cost Calculator")
num_products = st.sidebar.number_input("Number of products to generate", min_value=1, value=50)
image_cost_per_unit = st.sidebar.number_input("Cost per image ($)", min_value=0.0, value=0.05, step=0.01)
text_cost_per_unit = st.sidebar.number_input("Cost per short description ($)", min_value=0.0, value=0.01, step=0.01)
max_image_spend = st.sidebar.number_input("Max budget for image generation ($)", min_value=0.0, value=5.0, step=0.1)

# Calculate batch limit by max spend
allowed_by_budget = int(max_image_spend // image_cost_per_unit)
max_batch = min(num_products, 50, allowed_by_budget)

total_image_cost = num_products * image_cost_per_unit
total_text_cost = num_products * text_cost_per_unit
total_cost = total_image_cost + total_text_cost

st.sidebar.markdown("### 💸 Estimated Cost")
st.sidebar.write(f"Image Generation: ${total_image_cost:.2f}")
st.sidebar.write(f"Short Description Generation: ${total_text_cost:.2f}")
st.sidebar.write(f"**Total Estimated Cost: ${total_cost:.2f}**")
st.sidebar.write(f"Max products allowed by budget: {max_batch}")

# -----------------------------
# Session State
# -----------------------------
if "generated_products" not in st.session_state:
    st.session_state["generated_products"] = []
if "removed_columns" not in st.session_state:
    st.session_state["removed_columns"] = []
if "dashboard" not in st.session_state:
    st.session_state["dashboard"] = {"imported_count": 0}

# -----------------------------
# Upload Excel
# -----------------------------
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
if uploaded_file and client:
    df = pd.read_excel(uploaded_file, engine="openpyxl")

    # Remove undefined / all NaN columns
    removed_cols = [c for c in df.columns if df[c].isna().all()]
    df = df.drop(columns=removed_cols)
    st.session_state["removed_columns"] = removed_cols

    # Add Total Stock column if possible
    if "Stock" in df.columns and "Case Size" in df.columns:
        df["Total Stock"] = df["Stock"].fillna(0) * df["Case Size"].fillna(0)

    st.subheader("✅ Uploaded Data Preview")
    st.dataframe(df.head(10))

    if st.button(f"Generate Image & Descriptions (Max {max_batch} new products)"):
        generated_rows = []
        progress_bar = st.progress(0)

        # Collect new products (skip duplicates, case-insensitive)
        new_products = []
        for _, row in df.iterrows():
            product_dict = row.to_dict()
            item_desc = str(product_dict.get("Item Description", "")).strip().lower()
            product_dict["Item Description"] = item_desc
            if products_col.find_one({"Item Description": item_desc}):
                continue
            new_products.append(product_dict)

        if not new_products:
            st.info("⚠️ No new products to generate. All exist in DB.")
        else:
            # Limit batch by max_batch
            batch = new_products[:max_batch]

            for idx, product_dict in enumerate(batch):
                product_dict["image_base64"] = generate_product_image(client, product_dict)
                product_dict["short_description"] = generate_short_description(client, product_dict)
                product_dict["long_description"] = generate_long_description(product_dict)
                generated_rows.append(product_dict)
                progress_bar.progress((idx + 1) / len(batch))

            st.session_state["generated_products"] = generated_rows
            st.session_state["dashboard"]["imported_count"] = len(generated_rows)

            st.subheader("📝 Generated Products Preview")
            preview_df = pd.DataFrame(generated_rows).drop(columns=["image_base64"], errors="ignore")
            st.dataframe(preview_df)

            if removed_cols:
                st.info(f"Removed undefined columns during import: {removed_cols}")

# -----------------------------
# Insert Products
# -----------------------------
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

# -----------------------------
# Dashboard / Summary
# -----------------------------
st.subheader("📊 Dashboard Summary")
total_db_products = len(get_all_products())
imported_count = st.session_state["dashboard"]["imported_count"]
st.write(f"Total products in DB: {total_db_products}")
st.write(f"Products generated this session: {imported_count}")
st.write(f"Estimated cost for image generation: ${imported_count * image_cost_per_unit:.2f}")
st.write(f"Estimated cost for short description: ${imported_count * text_cost_per_unit:.2f}")
st.write(f"Total estimated cost: ${imported_count * (image_cost_per_unit + text_cost_per_unit):.2f}")

# -----------------------------
# View DB
# -----------------------------
st.subheader("📝 All Products in DB")
all_products = get_all_products()
if all_products:
    st.dataframe(pd.DataFrame(all_products))

columns = list(pd.DataFrame(all_products).columns) if all_products else []

# -----------------------------
# Delete Column (Dropdown)
# -----------------------------
st.subheader("🗑️ Delete Column from DB")
if columns:
    col_to_delete = st.selectbox("Select column to delete", options=columns)
    if st.button("Delete Column"):
        delete_column(col_to_delete)
        st.success(f"✅ Column '{col_to_delete}' deleted from all products")

# -----------------------------
# Rename Column (Dropdown + Input)
# -----------------------------
st.subheader("✏️ Rename Column in DB")
if columns:
    col_to_rename = st.selectbox("Select column to rename", options=columns, key="rename_select")
    new_col_name = st.text_input("Enter new column name")
    if st.button("Rename Column"):
        if new_col_name.strip():
            products_col.update_many({}, {"$rename": {col_to_rename: new_col_name.strip()}})
            st.success(f"✅ Column '{col_to_rename}' renamed to '{new_col_name.strip()}'")
        else:
            st.error("❌ New column name cannot be empty")

# -----------------------------
# Download DB
# -----------------------------
st.subheader("⬇️ Download DB as Excel")
if st.button("Download Excel"):
    excel_bytes = write_excel(pd.DataFrame(get_all_products()))
    st.download_button("Download Excel", data=excel_bytes, file_name="products.xlsx")
