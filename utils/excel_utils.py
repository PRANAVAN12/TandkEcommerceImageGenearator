import pandas as pd
from io import BytesIO

def read_excel(file):
    try:
        return pd.read_excel(file, engine="openpyxl")
    except Exception as e:
        return None

def write_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()
