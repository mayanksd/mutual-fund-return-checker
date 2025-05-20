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
    import requests
    from bs4 import BeautifulSoup

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        return {
            "fund_name": "Error fetching page",
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    soup = BeautifulSoup(response.content, "html.parser")
    fund_name = soup.find("h1").text.strip()

    # Find the "Compare performance" heading and table
    compare_heading = soup.find(lambda tag: tag.name == "h2" and "compare performance" in tag.text.lower())
    if not compare_heading:
        return {
            "fund_name": fund_name,
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    table = compare_heading.find_next("table")
    rows = table.find_all("tr")

    # Fix: header may use <th>, not <td>
    header_cells = rows[0].find_all(["td", "th"])
    cagr_col_index = next((i for i, cell in enumerate(header_cells) if "3 Y" in cell.text), None)
    if cagr_col_index is None:
        return {
            "fund_name": fund_name,
            "3y_cagr": "N/A",
            "benchmark": "N/A",
            "category_avg": "N/A",
            "category_rank": "N/A"
        }

    fund_cagr = benchmark_cagr = category_avg = category_rank = "N/A"
    benchmark_name = ""

    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) <= cagr_col_index:
            continue

        try:
            row_label = cells[0].text.strip().lower()
        except Exception:
            continue

        if row_label == "this fund":
            fund_cagr = cells[cagr_col_index].text.strip()
        elif row_label.startswith("benchmark"):
            benchmark_name = cells[0].text.strip().replace("Benchmark: ", "").strip()
            benchmark_cagr = cells[cagr_col_index].text.strip()
        elif row_label == "category average":
            category_avg = cells[cagr_col_index].text.strip()
        elif row_label == "category rank":
            category_rank = cells[cagr_col_index].text.strip()

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

# Load fund list from Excel
df_urls = pd.read_excel("fund_returns_urls.xlsx")
fund_names = df_urls["Fund Name"].dropna().tolist()

# Show dynamic dropdowns
st.markdown("### 🧮 Select Mutual Funds to Compare")
selected_funds = []
min_funds = 3
max_funds = 6

# Show the first three mandatory inputs
for i in range(min_funds):
    fund = st.selectbox(
        f"Fund {i+1}",
        fund_names,
        key=f"fund_select_{i}",
        placeholder="Start typing mutual fund name..."
    )
    selected_funds.append(fund)

# Optional: Add button to include more funds (up to 6)
if "extra_funds" not in st.session_state:
    st.session_state.extra_funds = 0

if st.session_state.extra_funds < (max_funds - min_funds):
    if st.button("➕ Add Another Fund"):
        st.session_state.extra_funds += 1

for i in range(st.session_state.extra_funds):
    fund = st.selectbox(
        f"Fund {min_funds + i + 1}",
        fund_names,
        key=f"extra_fund_select_{i}",
        placeholder="Start typing mutual fund name..."
    )
    selected_funds.append(fund)

# 6. Results (Placeholder for now)

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
