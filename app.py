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

# Dropdown for Cooling Capacity
cooling_capacities = sorted(
 active_df["C-Total Cool Rated"].dropna().unique().tolist()
)
selected_cooling = debar.selectbox(
 "Cooling Capacity (kW):", options=["All"] + cooling_capacities
)

# Optional Heating Capacity 
