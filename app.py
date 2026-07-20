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

    # Apply 30% reduction to incentive calculations
    for df in [df_avg, df_cold]:
        if "Total incentive - NEW" in df.columns:
            df["Total incentive - NEW"] *= 0.70
        if "ESCs replacement" in df.columns:
            df["ESCs replacement"] *= 0.70
        if "PRCs replacement" in df.columns:
            df["PRCs replacement"] *= 0.70

    return df_avg, df_cold


try:
    df_avg, df_cold = load_data(EXCEL_FILE)
except Exception as e:
    st.error(f"Error loading {EXCEL_FILE}: {e}")
    st.stop()

# 3. Sidebar Filters
debar = st.sidebar
debar.header("Filter Options")

# Climate Zone Selection
zone_choice = debar.radio("Select Climate Zone:", ("Average Zone", "Cold Zone"))
active_df = df_avg if zone_choice == "Average Zone" else df_cold
eligibility_col = (
    "ELIGIBLE_MIXED" if zone_choice == "Average Zone" else "ELIGIBLE_COLD"
)

debar.markdown("---")

# Filter Options Selection
s = sorted(active_df["Brand"].dropna().unique().astype(str))
ted_brands = debar.multiselect("Select Brand(s):", s)

gs = sorted(active_df["Configuration1"].dropna().unique().astype(str))
ted_configs = debar.multiselect("Select Type:", gs)

eligibility_options = active_df[eligibility_col].dropna().unique().astype(str)
ted_eligibility = debar.multiselect("Eligibility Status:", eligibility_options)

min_kw = float(active_df["C-Total Cool Rated"].min())
max_kw = float(active_df["C-Total Cool Rated"].max())
ted_kw = debar.number_input(
    "Cooling Capacity (kW):",
    min_value=min_kw,
    max_value=max_kw,
    value=min_kw,
    step=0.1,
)

model_search = debar.text_input("Model Search (e.g., FDYA, PEA-M):")

# 4. Apply Filters
filtered_df = active_df.copy()

if ted_brands:
    filtered_df = filtered_df[filtered_df["Brand"].isin(ted_brands)]
if ted_configs:
    filtered_df = filtered_df[filtered_df["Configuration1"].isin(ted_configs)]
if ted_eligibility:
    filtered_df = filtered_df[filtered_df[eligibility_col].isin(ted_eligibility)]

filtered_df = filtered_df[
    (filtered_df["C-Total Cool Rated"] >= ted_kw - 0.1)
    & (filtered_df["C-Total Cool Rated"] <= ted_kw + 0.1)
]

if model_search:
    filtered_df = filtered_df[
        filtered_df["Model_No"]
        .astype(str)
        .str.contains(model_search, case=False, na=False)
        | filtered_df["Brand"]
        .astype(str)
        .str.contains(model_search, case=False, na=False)
    ]

# 5. Display Counts & Summary
st.markdown(f"## Model Results ({zone_choice})")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Matching Models", len(filtered_df))
col2.metric(
    "Eligible Units",
    len(filtered_df[filtered_df[eligibility_col] == "ELIGIBLE"]),
)

if not filtered_df.empty:
    col3.metric(
        "Max New Incentive",
        f"${filtered_df['Total incentive - NEW'].max():,.2f}",
    )
    col4.metric(
        "Max Repl. Incentive", f"${filtered_df['ESCs replacement'].max():,.2f}"
    )
else:
    col3.metric("Max New Incentive", "$0.00")
    col4.metric("Max Repl. Incentive", "$0.00")

st.markdown("---")

# 6. Display Interactive Table
display_cols = [
    "Model_No",
    "Brand",
    "Configuration1",
    "C-Total Cool Rated",
    eligibility_col,
    "Total incentive - NEW",
    "ESCs replacement",
]

st.dataframe(
    filtered_df[display_cols].rename(columns={eligibility_col: "Eligibility"}),
    use_container_width=True,
    height=450,
)

# 7. Download Filtered Data as CSV
st.download_button(
    label="Download Filtered Data as CSV",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="nsw_rebate_filtered.csv",
    mime="text/csv",
)
