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
# Title
st.markdown("### 🧮 Select Mutual Funds to Compare")

# Ensure session state is initialized
if "num_funds" not in st.session_state:
    st.session_state["num_funds"] = 3  # Default to 3

if "add_triggered" not in st.session_state:
    st.session_state["add_triggered"] = False

df_urls = pd.read_excel("fund_returns_urls.xlsx")
df_urls = df_urls.dropna(subset=["Fund Name", "URL"])
df_urls["Fund Name"] = df_urls["Fund Name"].str.strip()
df_urls["URL"] = df_urls["URL"].str.strip()

fund_names = df_urls["Fund Name"].tolist()

# Add button + hint
cols = st.columns([1, 3])
with cols[0]:
    if st.session_state["num_funds"] < 6:
        if st.button("➕ Add Another Fund"):
            st.session_state["add_triggered"] = True
with cols[1]:
    st.markdown("<span style='font-size: 0.85em; color: gray;'>Add up to 6 funds to compare</span>", unsafe_allow_html=True)

# If button was clicked
if st.session_state["add_triggered"]:
    if st.session_state["num_funds"] < 6:
        st.session_state["num_funds"] += 1
    st.session_state["add_triggered"] = False

# Fund selection dropdowns
selected_funds = []
selected_funds_so_far = []

for i in range(st.session_state["num_funds"]):
    available_options = [f for f in fund_names if f not in selected_funds_so_far]
    
    fund_input = st.selectbox(
        f"Select Fund {i+1}",
        available_options,
        index=None,
        key=f"fund_select_{i}",
        placeholder="Start typing mutual fund name..."
    )

    if fund_input != "Start typing mutual fund name...":
        selected_funds_so_far.append(fund_input)
        selected_funds.append(fund_input)
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
