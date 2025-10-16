import streamlit as st
import pandas as pd
from db import insert_product, get_all_products, delete_column
from utils import write_excel, generate_short_description, generate_long_description, generate_product_image

st.set_page_config(page_title="Fast CRUD App - Image & Description Generator", layout="wide")
st.title("📦 Fast CRUD App - Image & Description Generator")

# -----------------------
# Upload Excel
# -----------------------
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.fillna("", inplace=True)  # Fill NaNs
    st.subheader("📄 Imported Products Preview")
    st.dataframe(df.head(20))

    # Keep only new products (avoid duplicates in DB)
    db_products = get_all_products()
    existing_names = [p["Item Description"] for p in db_products]
    new_products = df[~df["Item Description"].isin(existing_names)]
    st.info(f"🆕 {len(new_products)} new products to generate")

# -----------------------
# Generate Image / Descriptions
# -----------------------
if uploaded_file and not new_products.empty:
    action = st.selectbox(
        "Select action for new products",
        ["Generate Image", "Generate Short Description", "Generate Long Description"]
    )

    if st.button("Start Generation"):
        progress_bar = st.progress(0)
        for i, row in new_products.iterrows():
            update_data = {}

            if action == "Generate Image":
                # Better prompt for Gemini/OpenAI
              
                img_base64 = generate_product_image(row['Item Description'])
                update_data["image_base64"] = img_base64

            elif action == "Generate Short Description":
                short_desc = generate_short_description(row)
                update_data["short_description"] = short_desc

            elif action == "Generate Long Description":
                long_desc = generate_long_description(row)
                update_data["long_description"] = long_desc

            # Update DataFrame directly
            for key, val in update_data.items():
                new_products.at[i, key] = val

            progress_bar.progress((i+1)/len(new_products))
        st.success(f"✅ {action} generation completed!")

        # Show updated table with images
        st.subheader("🖼️ Generated Results Preview")
        def render_image(val):
            if val:
                return f'<img src="{val}" width="80"/>'
            return ""
        display_df = new_products.copy()
        st.write(display_df.to_html(escape=False, formatters={"image_base64": render_image}), unsafe_allow_html=True)

# -----------------------
# Insert Generated Products to DB
# -----------------------
if uploaded_file and not new_products.empty:
    if st.button("Insert Generated Products into DB"):
        for _, row in new_products.iterrows():
            row_dict = row.fillna("").to_dict()
            insert_product(row_dict)
        st.success("✅ Products inserted into DB!")

        # Show DB after insertion
        db_products = get_all_products()
        st.subheader("🗄️ Database Products")
        st.dataframe(pd.DataFrame(db_products))

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
