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

# --- Portfolio Rank Calculation ---

def get_portfolio_rank_score(rank_list):
    """
    Input: rank_list like ['1/20', '3/15']
    Output:
        - relative_rank_pct: Combined average percentile rank
        - label: Emoji + Category label based on performance
    """

    total_rank = 0
    total_count = 0
    cleaned_list = []

    for rank in rank_list:
        try:
            if rank == "N/A" or "0" in rank:
                continue  # ✅ Skip zero or N/A ranks
            r, t = map(int, rank.split("/"))
            total_rank += r
            total_count += t
            cleaned_list.append(rank)
        except:
            continue  # Skip invalid formats

    if total_count == 0:
        return None, "❓ Unknown"

    is_champion = all(r.split("/")[0] == "1" for r in cleaned_list)

    if is_champion:
        return 0.0, "🏆 Champion Portfolio 💪"

    relative_rank_pct = total_rank / total_count

    if relative_rank_pct <= 0.15:
        label = "⭐ Top Quartile"
    elif relative_rank_pct <= 0.45:
        label = "👍 Above Average (Can do better)"
    elif relative_rank_pct <= 0.55:
        label = "😐 Average (Meh!)"
    elif relative_rank_pct <= 0.75:
        label = "😞 Below Average (Not Good, Take Action)"
    else:
        label = "❌ Bottom Quartile (The Worst Performer!)"

    return relative_rank_pct * 100, label

# 📈 Portfolio Outperformance Calculator (Handles Edge Case 1)
def get_portfolio_outperformance(data_list):
    diffs = []
    for d in data_list:
        try:
            fund_cagr = float(d["3y_cagr"].replace("%", "").strip())
            benchmark_cagr = float(d["benchmark"].split("(")[-1].replace(")", "").replace("%", "").strip())

            # 🛑 Skip funds with 0% fund or benchmark return
            if fund_cagr == 0.0 or benchmark_cagr == 0.0:
                continue

            diffs.append(fund_cagr - benchmark_cagr)
        except Exception:
            continue

    if not diffs:
        return None, "⚠️ Not Available", ""

    avg_diff = sum(diffs) / len(diffs)

    # 🎯 Bucket logic with your updated labels and emojis
    if avg_diff > 5:
        label, emoji, desc = "🚀 Crushing It 🏆 🕺 💃", "🚀", "Champion Portfolio! Top Quartile! 👏👏."
    elif avg_diff > 1.5:
        label, emoji, desc = "✅ Beating the Bench", "👍", "Decent outperformance, can do better."
    elif avg_diff > -1:
        label, emoji, desc = "😐 Neck and Neck", "👎", "Performing in line with benchmarks. Nothing exciting, can do much better."
    else:
        label, emoji, desc = "📉 Dragging Behind 😭", "🚨", "Lagging noticeably, needs a relook."

    return avg_diff, f"{label} {emoji}", desc

# 5. UI: Fund Selection
st.title("📈 Mutual Fund Portfolio Performance Checker")
st.markdown("See your mutual fund portfolio's performance relative with its benchmark and category.")

# Load fund list from Excel
df_urls = pd.read_excel("fund_returns_urls.xlsx")
fund_names = df_urls["Fund Name"].dropna().tolist()

# Show dynamic dropdowns
# Title
st.markdown("### 🖱️ Select Mutual Funds to Compare")

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

# Add button + hint (simplified, no extra click needed to hide)
cols = st.columns([1, 3])

# Ensure session state is initialized
if "num_funds" not in st.session_state:
    st.session_state["num_funds"] = 3  # default

# Button only appears if fewer than 6 funds
if st.session_state["num_funds"] < 6:
    with cols[0]:
        add_clicked = st.button("➕ Add Another Fund")
    with cols[1]:
        st.markdown("<span style='font-size: 0.85em; color: gray;'>Add up to 6 funds to compare</span>", unsafe_allow_html=True)

    if add_clicked:
        st.session_state["num_funds"] += 1
        
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
        placeholder="Click and start typing 🔍..."
    )

    if fund_input != "Start typing mutual fund name...":
        selected_funds_so_far.append(fund_input)
        selected_funds.append(fund_input)

# 6. URL Map Construction Block
url_map = {row["Fund Name"]: row["URL"] for _, row in df_urls.iterrows()}

# 7. Calculate Return Score Block
# 7. Calculate Return Score Block
if st.button("🧮 Calculate Return Score"):
    with st.spinner("🔄 Fetching live data..."):
        performance_data = []
        
        for fund in selected_funds:
            data = fetch_returns_from_moneycontrol(url_map[fund])
            performance_data.append(data)

        # 🏆 Portfolio Summary FIRST
        rank_list = [d["category_rank"] for d in performance_data if d["category_rank"]]
        portfolio_rank_value, rank_label = get_portfolio_rank_score(rank_list)

        st.markdown("### 🏆 Portfolio Performance Summary")
        st.markdown(f"**Relative Category Rank:** {rank_label}")

        outperf_value, outperf_label, outperf_desc = get_portfolio_outperformance(performance_data)

        if outperf_value is not None:
            st.markdown(f"**Benchmark Comparison:** {outperf_label}")
            st.markdown(
                f"<span style='color: gray; font-size: 0.9em;'>({outperf_value:+.2f}% vs benchmark) – {outperf_desc}</span>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("**Benchmark Comparison:** Not Available")

        # 📊 Individual Fund Performance
        st.markdown("### 📊 Individual MF Performance")
        for data in performance_data:
            st.markdown(f"**{data['fund_name']}**")
            st.markdown(f"- 3Y CAGR: {data['3y_cagr']}")
            st.markdown(f"- Benchmark: {data['benchmark']}")
            st.markdown(f"- Category Avg: {data['category_avg']}")
            st.markdown(f"- Rank: {data['category_rank']}")
            st.markdown("---")
