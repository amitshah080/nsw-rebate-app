import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="NSW PDRS HVAC Incentive Finder",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ NSW HVAC Rebate & Eligibility Finder")
st.caption("Smart filtering tool for NSW PDRS & ESS Air Conditioning Claims")

# 2. File Loading Function
EXCEL_FILE = "claim DOC-20260701-WA0006.xlsx"

@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    df_avg = pd.read_excel(xls, sheet_name="Average Zone")
    df_cold = pd.read_excel(xls, sheet_name="Cold Zone")
    df_postcodes = pd.read_excel(xls, sheet_name="POSTCODES")
    return df_avg, df_cold, df_postcodes

try:
    df_avg, df_cold, df_postcodes = load_data(EXCEL_FILE)
except Exception as e:
    st.error(f"Error loading {EXCEL_FILE}: {e}")
    st.stop()

# 3. Sidebar Filters
st.sidebar.header("🔍 Filter Options")

# Climate Zone Selection
zone_choice = st.sidebar.radio("Select Climate Zone:", ["Average Zone", "Cold Zone"])
active_df = df_avg.copy() if zone_choice == "Average Zone" else df_cold.copy()
eligibility_col = "ELIGIBLE_MIXED" if zone_choice == "Average Zone" else "ELIGIBLE_COLD"

# Postcode Quick Lookup Tool
st.sidebar.markdown("---")
st.sidebar.subheader("📍 Postcode Zone Checker")
postcode_input = st.sidebar.number_input("Enter Postcode:", min_value=2000, max_value=2999, step=1, value=2000)
matched_postcode = df_postcodes[df_postcodes["Postcode"] == postcode_input]

if not matched_postcode.empty:
    detected_zone = matched_postcode["NSW ESS Climate Zone"].values[0]
    st.sidebar.success(f"Postcode {postcode_input} is in **{detected_zone} Zone**")
else:
    st.sidebar.warning("Postcode not found in list.")

st.sidebar.markdown("---")

# Filter Options
brands = sorted(active_df["Brand"].dropna().astype(str).unique())
selected_brands = st.sidebar.multiselect("Select Brand(s):", brands, default=[])

configs = sorted(active_df["Configuration1"].dropna().astype(str).unique())
selected_configs = st.sidebar.multiselect("Select Type:", configs, default=[])

eligibility_options = active_df[eligibility_col].dropna().unique()
selected_eligibility = st.sidebar.multiselect("Eligibility Status:", eligibility_options, default=["ELIGIBLE"])

# Cooling Capacity Slider
min_kw = float(active_df["C-Total Cool Rated"].min())
max_kw = float(active_df["C-Total Cool Rated"].max())
selected_kw = st.sidebar.slider("Cooling Capacity Range (kW):", min_kw, max_kw, (2.0, 15.0), step=0.5)

# Text Search
search_term = st.sidebar.text_input("Model Search (e.g., FDYA, PEA-M):")

# 4. Apply Filters
filtered_df = active_df.copy()

if selected_brands:
    filtered_df = filtered_df[filtered_df["Brand"].astype(str).isin(selected_brands)]

if selected_configs:
    filtered_df = filtered_df[filtered_df["Configuration1"].astype(str).isin(selected_configs)]

if selected_eligibility:
    filtered_df = filtered_df[filtered_df[eligibility_col].isin(selected_eligibility)]

filtered_df = filtered_df[
    (filtered_df["C-Total Cool Rated"] >= selected_kw[0]) & 
    (filtered_df["C-Total Cool Rated"] <= selected_kw[1])
]

if search_term:
    filtered_df = filtered_df[
        filtered_df["Model_No"].astype(str).str.contains(search_term, case=False, na=False)
    ]

# 5. Key Metrics Summary
col1, col2, col3, col4 = st.columns(4)
col1.metric("Matching Models", len(filtered_df))
col2.metric("Eligible Units", len(filtered_df[filtered_df[eligibility_col] == "ELIGIBLE"]))
col3.metric("Max New Incentive", f"${filtered_df['Total incentive - NEW'].max():,.2f}" if not filtered_df.empty else "$0.00")
col4.metric("Max Repl. Incentive", f"${filtered_df['Total incentive - REPLACEMENT'].max():,.2f}" if not filtered_df.empty else "$0.00")

st.markdown("---")

# 6. Display Interactive Table
st.subheader(f"📋 Model Results ({zone_choice})")

display_cols = [
    "Model_No", "Brand", "Configuration1", "C-Total Cool Rated", "H-Total Heat Rated",
    eligibility_col, "Total incentive - NEW", "Total incentive - REPLACEMENT",
    "ESCs replacement", "PRCs replacement"
]

st.dataframe(
    filtered_df[display_cols].rename(columns={eligibility_col: "Eligibility"}),
    use_container_width=True,
    height=450
)

# 7. Download Filtered Data
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name=f"NSW_Rebate_Filtered_{zone_choice}.csv",
    mime="text/csv"
)