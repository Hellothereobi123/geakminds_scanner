from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import pandas as pd
import streamlit as st
import os

endpoint = os.environ["OPENAI_DOC_ENDPOINT"]
key = os.environ["OPENAI_DOC_API_KEY"]

client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

with open("table_lol2.pdf", "rb") as f:
    poller = client.begin_analyze_document("prebuilt-layout", document=f)
    result = poller.result()

# Extract and display tables

for idx, table in enumerate(result.tables):
    # Initialize empty table with dimensions
    rows = table.row_count
    cols = table.column_count
    data = [["" for _ in range(cols)] for _ in range(rows)]

    # Fill data from cells
    for cell in table.cells:
        data[cell.row_index][cell.column_index] = cell.content

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df = df.replace({r":selected:|:unselected:": ""}, regex=True)
    count = 0

    # Show in Streamlit
    st.subheader(f"Table {idx + 1}")
    st.table(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
   "Press to Download",
   csv,
   "file.csv",
   "text/csv",
   key=f'download-csv-{idx}'
    )
    count+=1