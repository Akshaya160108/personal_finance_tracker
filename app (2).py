
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM STYLE ----------------
st.markdown("""
<style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 17px;
        color: #6b7280;
        margin-top: 0;
        margin-bottom: 25px;
    }
    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 18px;
        margin-bottom: 12px;
    }
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e5e7eb;
        padding: 18px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown(
    '<div class="main-title">💰 Personal Finance Data Analysis Dashboard</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Analyze income, expenses, savings, investments, budgets and financial health.</div>',
    unsafe_allow_html=True
)

# ---------------- DATA UPLOAD ----------------
st.sidebar.header("📂 Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload your personal finance dataset",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is None:
    st.info("👈 Upload your personal finance CSV or Excel file from the sidebar to start.")
    st.stop()

@st.cache_data
def load_data(file_name, file_bytes):
    import io
    data = io.BytesIO(file_bytes)
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(data)
    return pd.read_excel(data)

df = load_data(uploaded_file.name, uploaded_file.getvalue())

# ---------------- DATA PREPARATION ----------------
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["year_month"] = df["date"].dt.to_period("M")

# Use existing project features when available
if "monthly_income" in df.columns and "monthly_expense_total" in df.columns:
    df["remaining_cash"] = (
        df["monthly_income"] - df["monthly_expense_total"]
    )

if "budget_goal" in df.columns and "monthly_expense_total" in df.columns:
    df["budget_difference"] = (
        df["budget_goal"] - df["monthly_expense_total"]
    )

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.divider()
st.sidebar.header("🔎 Filters")

filtered = df.copy()

if "year" in df.columns:
    years = sorted(df["year"].dropna().unique())
    selected_years = st.sidebar.multiselect(
        "Year",
        years,
        default=years
    )
    if selected_years:
        filtered = filtered[filtered["year"].isin(selected_years)]

if "category" in df.columns:
    categories = sorted(df["category"].dropna().unique())
    selected_categories = st.sidebar.multiselect(
        "Category",
        categories,
        default=categories
    )
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]

st.sidebar.caption(f"Showing {len(filtered):,} of {len(df):,} records")

# ---------------- HELPER FUNCTIONS ----------------
def total(column):
    if column in filtered.columns:
        return filtered[column].sum()
    return 0

def average(column):
    if column in filtered.columns:
        return filtered[column].mean()
    return 0

# ---------------- FINANCIAL OVERVIEW ----------------
st.markdown('<div class="section-title">📊 Financial Overview</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

c1.metric("💰 Total Income", f"₹{total('monthly_income'):,.0f}")
c2.metric("💸 Total Expenses", f"₹{total('monthly_expense_total'):,.0f}")
c3.metric("🏦 Total Savings", f"₹{total('actual_savings'):,.0f}")
c4.metric("📈 Total Investment", f"₹{total('investment_amount'):,.0f}")

c5, c6, c7, c8 = st.columns(4)

c5.metric("Average Income", f"₹{average('monthly_income'):,.0f}")
c6.metric("Average Expenses", f"₹{average('monthly_expense_total'):,.0f}")
c7.metric("Average Savings", f"₹{average('actual_savings'):,.0f}")

if "savings_rate" in filtered.columns:
    avg_rate = average("savings_rate")
    # Values such as 0.23 represent 23%.
    if avg_rate <= 1:
        avg_rate = avg_rate * 100
    c8.metric("Average Savings Rate", f"{avg_rate:.2f}%")
else:
    income = total("monthly_income")
    savings = total("actual_savings")
    rate = (savings / income * 100) if income else 0
    c8.metric("Savings Rate", f"{rate:.2f}%")

st.divider()

# ---------------- FINANCIAL TRENDS ----------------
st.markdown('<div class="section-title">📈 Income, Expense & Savings Analysis</div>', unsafe_allow_html=True)

if "date" in filtered.columns:
    monthly = (
        filtered.dropna(subset=["date"])
        .groupby(filtered.dropna(subset=["date"])["date"].dt.to_period("M"))
        [["monthly_income", "monthly_expense_total", "actual_savings"]]
        .mean()
        .sort_index()
    )

    # Convert PeriodIndex to readable monthly labels.
    if not monthly.empty:
        monthly.index = monthly.index.astype(str)
        monthly = monthly.rename(columns={
            "monthly_income": "Income",
            "monthly_expense_total": "Expenses",
            "actual_savings": "Savings"
        })
        st.line_chart(monthly, height=380)
    else:
        st.warning("Not enough date information for the trend analysis.")

# ---------------- YEARLY ANALYSIS ----------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 💰 Year-wise Income")
    if "year" in filtered.columns:
        yearly = filtered.groupby("year")["monthly_income"].mean()
        st.bar_chart(yearly, height=300)

with col2:
    st.markdown("#### 💸 Year-wise Expenses")
    if "year" in filtered.columns:
        yearly = filtered.groupby("year")["monthly_expense_total"].mean()
        st.bar_chart(yearly, height=300)

with col3:
    st.markdown("#### 🏦 Year-wise Savings")
    if "year" in filtered.columns:
        yearly = filtered.groupby("year")["actual_savings"].mean()
        st.bar_chart(yearly, height=300)

st.divider()

# ---------------- SPENDING ANALYSIS ----------------
st.markdown('<div class="section-title">💸 Spending Analysis</div>', unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.markdown("#### Spending by Category")
    if "category" in filtered.columns and "monthly_expense_total" in filtered.columns:
        category_expense = (
            filtered.groupby("category")["monthly_expense_total"]
            .sum()
            .sort_values(ascending=False)
        )

        fig, ax = plt.subplots(figsize=(7, 5))
        category_expense.plot(kind="pie", autopct="%1.1f%%", ax=ax)
        ax.set_ylabel("")
        ax.set_title("Spending Distribution by Category")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with right:
    st.markdown("#### Essential vs Discretionary Spending")
    if "essential_spending" in filtered.columns and "discretionary_spending" in filtered.columns:
        spending = [
            filtered["essential_spending"].sum(),
            filtered["discretionary_spending"].sum()
        ]
        labels = ["Essential Spending", "Discretionary Spending"]

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.pie(spending, labels=labels, autopct="%1.1f%%")
        ax.set_title("Essential vs Discretionary Spending")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

st.divider()

# ---------------- SAVINGS & INVESTMENT ----------------
st.markdown('<div class="section-title">🏦 Savings & Investment Analysis</div>', unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.markdown("#### 🎯 Savings Goal Achievement")
    if "savings_goal_met" in filtered.columns:
        goal = filtered["savings_goal_met"].value_counts()

        fig, ax = plt.subplots(figsize=(7, 5))
        goal.plot(kind="pie", autopct="%1.1f%%", ax=ax)
        ax.set_ylabel("")
        ax.set_title("Savings Goal Achievement")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with right:
    st.markdown("#### 📈 Investment Trend")
    if "date" in filtered.columns and "investment_amount" in filtered.columns:
        investment = (
            filtered.dropna(subset=["date"])
            .groupby(filtered.dropna(subset=["date"])["date"].dt.to_period("M"))["investment_amount"]
            .mean()
            .sort_index()
        )
        investment.index = investment.index.astype(str)
        st.line_chart(investment, height=300)

st.divider()

# ---------------- BUDGET & FINANCIAL HEALTH ----------------
st.markdown('<div class="section-title">🎯 Budget & Financial Health</div>', unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.markdown("#### Budget Performance")

    if "budget_goal" in filtered.columns and "monthly_expense_total" in filtered.columns:
        difference = (
            filtered["budget_goal"] - filtered["monthly_expense_total"]
        )

        within = int((difference >= 0).sum())
        exceeded = int((difference < 0).sum())

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.pie(
            [within, exceeded],
            labels=["Within Budget", "Exceeded Budget"],
            autopct="%1.1f%%"
        )
        ax.set_title("Budget Performance")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        rate = within / len(filtered) * 100 if len(filtered) else 0
        b1, b2 = st.columns(2)
        b1.metric("Within Budget", f"{within:,}")
        b2.metric("Budget Success Rate", f"{rate:.1f}%")

with right:
    st.markdown("#### 😟 Financial Stress Level")

    if "financial_stress_level" in filtered.columns:
        stress = filtered["financial_stress_level"].value_counts()
        st.bar_chart(stress, height=300)

st.divider()

# ---------------- KEY INSIGHTS ----------------
st.markdown('<div class="section-title">💡 Key Financial Insights</div>', unsafe_allow_html=True)

income_total = total("monthly_income")
expense_total = total("monthly_expense_total")
saving_total = total("actual_savings")

if income_total > 0:
    expense_ratio = expense_total / income_total * 100
    saving_ratio = saving_total / income_total * 100
else:
    expense_ratio = 0
    saving_ratio = 0

insight1, insight2, insight3 = st.columns(3)

with insight1:
    st.info(
        f"**Expense Ratio**\n\n"
        f"{expense_ratio:.1f}% of total income was spent."
    )

with insight2:
    st.info(
        f"**Savings Ratio**\n\n"
        f"{saving_ratio:.1f}% of total income was saved."
    )

with insight3:
    if "investment_amount" in filtered.columns:
        investment_total = total("investment_amount")
        st.info(
            f"**Investment**\n\n"
            f"₹{investment_total:,.0f} was invested."
        )

# ---------------- DATA PREVIEW ----------------
with st.expander("🔍 View Processed Data"):
    st.dataframe(filtered, use_container_width=True)

st.caption(
    "Personal Finance Data Analysis | Python • Pandas • Matplotlib • Streamlit"
)
