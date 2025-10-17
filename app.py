import streamlit as st
import pandas as pd
from db import insert_product, get_all_products, delete_column, products_col
from utils import write_excel, generate_product_image, generate_short_description, generate_long_description, init_gemini_client
from io import BytesIO
import base64
import math
import time

st.set_page_config(page_title="🛒 E-Commerce Product Manager", layout="wide")
st.title("🛍️ E-Commerce Product Management Dashboard")

# -----------------------------
# Helper utilities
# -----------------------------
def refresh_ui():
    st.rerun()


def safe_normalize(desc):
    return str(desc).strip().lower() if desc is not None else ""

def get_columns_from_db():
    prods = get_all_products()
    if prods:
        return list(pd.DataFrame(prods).columns)
    return []

def show_toast(msg, kind="info"):
    if kind == "success": st.success(msg)
    elif kind == "error": st.error(msg)
    elif kind == "warning": st.warning(msg)
    else: st.info(msg)

# -----------------------------
# Sidebar: Gemini config + calculator + budget
# -----------------------------
st.sidebar.header("🔧 Settings & Cost Calculator")

api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
client = init_gemini_client(api_key) if api_key else None
if not api_key:
    st.sidebar.info("Enter your Gemini API key to enable generation features.")

num_products = st.sidebar.number_input("Desired number of products to generate", min_value=1, value=50)
image_cost_per_unit = st.sidebar.number_input("Cost per image ($)", min_value=0.0, value=0.05, step=0.005)
text_cost_per_unit = st.sidebar.number_input("Cost per short description ($)", min_value=0.0, value=0.01, step=0.001)
max_image_spend = st.sidebar.number_input("Max budget for images ($)", min_value=0.0, value=5.0, step=0.1)
thumbnail_toggle = st.sidebar.checkbox("Show thumbnails in preview", value=False)
batch_limit_global = 50

allowed_by_budget = int(max_image_spend // image_cost_per_unit) if image_cost_per_unit > 0 else batch_limit_global
effective_batch = min(num_products, batch_limit_global, max(0, allowed_by_budget))

st.sidebar.markdown("---")
st.sidebar.markdown("### 💸 Cost estimate")
st.sidebar.write(f"Images: ${image_cost_per_unit:.4f} × {num_products} = ${image_cost_per_unit * num_products:.2f}")
st.sidebar.write(f"Short desc: ${text_cost_per_unit:.4f} × {num_products} = ${text_cost_per_unit * num_products:.2f}")
st.sidebar.write(f"**Total est:** ${ (image_cost_per_unit + text_cost_per_unit) * num_products:.2f}")
st.sidebar.write(f"Max products allowed by budget: **{effective_batch}**")
st.sidebar.markdown("---")

# -----------------------------
# Session state defaults
# -----------------------------
if "generated_products" not in st.session_state:
    st.session_state["generated_products"] = []
if "dashboard" not in st.session_state:
    st.session_state["dashboard"] = {"last_generated": 0, "last_inserted": 0}
if "oplog" not in st.session_state:
    st.session_state["oplog"] = []

# -----------------------------
# Dashboard metrics
# -----------------------------
col1, col2, col3 = st.columns(3)
total_db_products = len(get_all_products())
col1.metric("Total products in DB", total_db_products)
col2.metric("Generated (session)", len(st.session_state["generated_products"]))
col3.metric("Image Gen Limit", effective_batch)

with st.expander("🧾 Operation Log"):
    for msg in reversed(st.session_state["oplog"][-10:]):
        st.write(msg)

# -----------------------------
# Upload & prepare
# -----------------------------
st.header("1️⃣ Upload & Prepare")
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
uploaded_df = None
if uploaded_file:
    try:
        uploaded_df = pd.read_excel(uploaded_file, engine="openpyxl")
        st.dataframe(uploaded_df.head(10))
    except Exception as e:
        st.error(f"Failed to read file: {e}")

if uploaded_df is not None:
    # Drop empty columns
    removed_cols = [c for c in uploaded_df.columns if uploaded_df[c].isna().all()]
    if removed_cols:
        uploaded_df = uploaded_df.drop(columns=removed_cols)
        show_toast(f"Removed empty columns: {removed_cols}", "info")

    # Compute Total Stock
    if "Stock" in uploaded_df.columns and "Case Size" in uploaded_df.columns:
        uploaded_df["Total Stock"] = uploaded_df["Stock"].fillna(0) * uploaded_df["Case Size"].fillna(0)

    st.markdown("### Cleaned Preview")
    st.dataframe(uploaded_df.head(10))

    # Generate button
    st.markdown("---")
    st.header("2️⃣ Generate (Images & Descriptions)")
    colA, colB = st.columns([3, 1])
    with colA:
        st.write("Duplicates skipped (case-insensitive). Batch limited to budget.")
    with colB:
        gen_btn = st.button("Generate Preview")

    if gen_btn:
        if not client:
            show_toast("Please enter Gemini API key.", "error")
        else:
            new_products = []
            for _, row in uploaded_df.iterrows():
                prod = row.to_dict()
                item_desc = safe_normalize(prod.get("Item Description", ""))
                if not item_desc:
                    continue
                if products_col and products_col.find_one({"Item Description": item_desc}):
                    continue
                new_products.append(prod)

            batch = new_products[:effective_batch]
            st.session_state["generated_products"] = []
            pb = st.progress(0)
            for i, prod in enumerate(batch):
                try:
                    prod["image_base64"] = generate_product_image(client, prod)
                    prod["short_description"] = generate_short_description(client, prod)
                    prod["long_description"] = generate_long_description(prod)
                    st.session_state["generated_products"].append(prod)
                except Exception as e:
                    st.session_state["oplog"].append(f"Failed: {e}")
                pb.progress((i + 1) / len(batch))
            show_toast(f"Generated {len(batch)} products (preview below)", "success")

# -----------------------------
# Preview & Verify
# -----------------------------
st.markdown("---")
st.header("3️⃣ Preview Before Insert")
if st.session_state["generated_products"]:
    gen_df = pd.DataFrame(st.session_state["generated_products"])
    st.dataframe(gen_df.drop(columns=["image_base64"], errors="ignore"))
    if st.button("Insert Generated Products to DB"):
        inserted = 0
        for p in list(st.session_state["generated_products"]):
            if insert_product(p):
                inserted += 1
        show_toast(f"Inserted {inserted} products to DB.", "success")
        st.session_state["generated_products"] = []
        refresh_ui()
else:
    st.info("No generated products yet.")


# -----------------------------
# DB View (Pagination + Search + Filters)
# -----------------------------
st.markdown("---")
st.header("4️⃣ Database Management & Viewer")

all_products = get_all_products()
if all_products:
    df_db = pd.DataFrame(all_products)

    # --- Filters ---
    st.subheader("🔍 Search & Filter")
    search_term = st.text_input("Search by Item Description or Category").lower().strip()
    category_col = "Category" if "Category" in df_db.columns else None

    if search_term:
        df_db = df_db[df_db.apply(lambda x: search_term in str(x).lower(), axis=1)]

    if category_col:
        categories = ["All"] + sorted(df_db[category_col].dropna().unique().tolist())
        selected_category = st.selectbox("Filter by Category", categories)
        if selected_category != "All":
            df_db = df_db[df_db[category_col] == selected_category]

    # --- Pagination ---
    items_per_page = st.number_input("Items per page", 5, 50, 20)
    total_pages = max(1, math.ceil(len(df_db) / items_per_page))
    page = st.number_input("Page", 1, total_pages, 1)

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    st.write(f"Showing {start_idx + 1}–{min(end_idx, len(df_db))} of {len(df_db)}")
    st.dataframe(df_db.iloc[start_idx:end_idx])

else:
    df_db = pd.DataFrame()  # <-- Always define df_db even if empty
    st.info("Database is empty.")

# -----------------------------
# Delete / Rename Column
# -----------------------------
st.markdown("---")
st.header("5️⃣ Column Operations")

columns = list(df_db.columns) if not df_db.empty else []

if columns:
    with st.expander("🗑️ Delete Column"):
        del_col = st.selectbox("Select column to delete", options=columns, key="del_col_select")
        if st.button("Delete Column"):
            delete_column(del_col)
            show_toast(f"Deleted column '{del_col}'.", "success")
            refresh_ui()

    with st.expander("✏️ Rename Column"):
        rename_col = st.selectbox("Select column to rename", options=columns, key="rename_col_select")
        new_name = st.text_input("New column name")
        if st.button("Rename Column"):
            if not new_name.strip():
                show_toast("New column name cannot be empty.", "error")
            else:
                products_col.update_many({}, {"$rename": {rename_col: new_name.strip()}})
                show_toast(f"Renamed '{rename_col}' to '{new_name.strip()}'", "success")
                refresh_ui()


# -----------------------------
# Export
# -----------------------------
st.markdown("---")
st.header("6️⃣ Export / Backup")

if st.button("Download DB as Excel"):
    excel_bytes = write_excel(pd.DataFrame(get_all_products()))
    st.download_button("Download Excel", data=excel_bytes, file_name="products.xlsx")

st.markdown("✅ **Notes:** All 'Item Descriptions' are normalized (lowercased) to avoid duplicates. Pagination, filters, and column operations are included for large datasets.")
