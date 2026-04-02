import io

import pandas as pd
import streamlit as st

from splitter import process

st.set_page_config(page_title="MediaOcean Splitter", page_icon="📊")
st.title("MediaOcean Planned Report Splitter")
st.write("Upload a Media Ocean planned `.xls` export to split condensed buy lines into individual spot-per-day rows.")

uploaded = st.file_uploader("Upload .xls file", type=["xls"])

if uploaded is not None:
    try:
        df = pd.read_excel(uploaded, header=None)
        result, stats = process(df)

        st.success("Split complete!")

        col1, col2, col3 = st.columns(3)
        col1.metric("Original Lines", stats["orig_lines"])
        col2.metric("Split Rows", stats["split_rows"])
        col3.metric("Skipped (Added Value)", stats["skipped_g"])

        col4, col5, col6 = st.columns(3)
        col4.metric("Original Net Cost", f"${stats['orig_net']:,.2f}")
        col5.metric("Split Net Cost", f"${stats['split_net']:,.2f}")
        col6.metric("Difference", f"${stats['net_diff']:.2f}")

        st.dataframe(result, use_container_width=True, hide_index=True)

        buf = io.BytesIO()
        result.to_excel(buf, index=False, engine="openpyxl")

        out_name = uploaded.name.replace(".xls", " Split.xlsx")
        st.download_button(
            label="Download Split Report",
            data=buf.getvalue(),
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.error(f"Error processing file: {e}")
