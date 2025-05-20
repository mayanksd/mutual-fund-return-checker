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
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Error fetching page: {e}")
        return {
            "fund_name": "Error",
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    soup = BeautifulSoup(response.content, "html.parser")

    # Locate the heading that contains "Compare performance"
    compare_heading = soup.find(lambda tag: tag.name in ["h2", "h3"] and "compare performance" in tag.text.lower())
    if not compare_heading:
        st.warning("⚠️ 'Compare performance' section not found.")
        return {
            "fund_name": "Section not found",
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    # Get the table right after the heading
    compare_table = compare_heading.find_next("table")
    rows = compare_table.find_all("tr")

    try:
        fund_name = soup.find("h1").text.strip()
        fund_cagr = rows[1].find_all("td")[2].text.strip()
        benchmark_name = rows[2].find_all("td")[0].text.strip().replace("Benchmark: ", "")
        benchmark_cagr = rows[2].find_all("td")[2].text.strip()
        category_avg = rows[3].find_all("td")[2].text.strip()
        category_rank = rows[4].find_all("td")[2].text.strip()
    except Exception as e:
        st.warning("⚠️ Table structure mismatch.")
        return {
            "fund_name": fund_name,
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    return {
        "fund_name": fund_name,
        "3y_cagr": fund_cagr,
        "benchmark": f"{benchmark_name} ({benchmark_cagr})",
        "category_avg": category_avg,
        "category_rank": category_rank
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
