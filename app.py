# 1. Imports
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 2. Page Configuration
st.set_page_config(
    page_title="Mutual Fund Return Performance Checker",
    layout="wide"
)

# 3. Scraper Utility Functions 
def fetch_returns_from_moneycontrol(url):
    debug_output = []  # Store debug logs

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        return {
            "fund_name": f"Error fetching page: {e}",
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")

    # Add log of number of tables found
    debug_output.append(f"Number of tables found: {len(tables)}")

    for i, table in enumerate(tables):
        if "Compare performance" in table.get_text():
            debug_output.append(f"✅ 'Compare performance' found in Table {i}")
            break
    else:
        debug_output.append("❌ 'Compare performance' not found in any table.")

    # Show debug logs in Streamlit
    st.markdown("### 🔍 Debug Info")
    for line in debug_output:
        st.markdown(f"- {line}")

    return {
        "fund_name": "Debug mode",
        "3y_cagr": "N/A",
        "benchmark": "N/A",
        "category_avg": "N/A",
        "category_rank": "N/A"
    }

# 4. Session State Initialization
if "num_funds" not in st.session_state:
    st.session_state["num_funds"] = 3

# 5. UI: Fund Selection
st.title("📈 Mutual Fund Return Performance Checker")
st.markdown("Compare your mutual fund's 3-year CAGR with its benchmark and category.")

# Simulated fund list for now
fund_list = [
    "Nippon India Small Cap Fund - Direct Plan",
    "Axis Bluechip Fund - Direct Plan",
    "HDFC Flexi Cap Fund - Direct Plan",
    "Parag Parikh Flexi Cap Fund"
]

selected_funds = []
for i in range(st.session_state["num_funds"]):
    fund = st.selectbox(f"Select Fund {i+1}", fund_list, key=f"fund{i}")
    selected_funds.append(fund)

if st.session_state["num_funds"] < 6:
    if st.button("➕ Add Another Fund"):
        st.session_state["num_funds"] += 1

# 6. Results (Placeholder for now)
url_map = {
    "Nippon India Small Cap Fund - Direct Plan": "https://www.moneycontrol.com/mutual-funds/nav/nippon-india-small-cap-fund-direct-plan/returns/MRC935",
    "Tata Small Cap Fund - Direct Plan": "https://www.moneycontrol.com/mutual-funds/nav/tata-small-cap-fund-direct-plan/returns/MTA1305",
    "Axis Small Cap Fund - Direct Plan": "https://www.moneycontrol.com/mutual-funds/nav/axis-small-cap-fund-direct-plan/returns/MAA316"
}

if st.button("🧮 Calculate Return Score"):
    st.markdown("### 📊 Results")
    for fund in selected_funds:
        # Use placeholder return function for now
        data = fetch_returns_from_moneycontrol(url_map[fund])       
        st.markdown(f"**{data['fund_name']}**")
        st.markdown(f"- 3Y CAGR: {data['3y_cagr']}")
        st.markdown(f"- Benchmark: {data['benchmark']}")
        st.markdown(f"- Category Avg: {data['category_avg']}")
        st.markdown(f"- Rank: {data['category_rank']}")
        st.markdown("---")
