import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="God's Work, Our Hands 2026", layout="wide")

# ── Brand colors ──────────────────────────────────────────────────────────────
# Teal 3155:  #006778
# Green 3298: #006D55
# Lime 7490:  #6A963B
# Brown 7532: #665546

st.markdown("""
<style>
/* ── Card ── */
.project-card {
    border: 2px solid #006778;
    border-radius: 12px;
    padding: 20px;
    background-color: #ffffff;
    box-shadow: 0 4px 10px rgba(0, 103, 120, 0.15);
    height: 100%;
}

/* ── Card heading ── */
.project-card h3 {
    margin: 0 0 12px 0;
    font-size: 1.1rem;
    color: #006778;
}

/* ── Badges ── */
.project-card .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #ffffff;
}
.badge-category { background-color: #6A963B; }
.badge-day      { background-color: #665546; }

/* ── Service text ── */
.project-card .service {
    font-size: 0.9rem;
    color: #444;
    margin: 0;
}

/* ── View Details button ── */
div.stButton > button {
    background-color: #006D55 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
}
div.stButton > button:hover {
    background-color: #005a45 !important;
}

/* ── Dialog ── */
div[data-testid="stDialog"] h1 {
    color: #006778;
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
}
.detail-row {
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
}
.detail-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #006778;
    margin-bottom: 2px;
}
.detail-value {
    font-size: 0.92rem;
    color: #1a1a1a;
    padding: 6px 10px;
    background-color: #f5f9f9;
    border-left: 3px solid #6A963B;
    border-radius: 4px;
}
.detail-divider {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 8px 0;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #006778;
}

/* ── Sidebar background ── */
section[data-testid="stSidebar"] {
    background-color: #f0f6f7;
}

/* ── Sidebar filter labels ── */
section[data-testid="stSidebar"] label {
    color: #006778 !important;
    font-weight: 600 !important;
}

/* ── Multiselect tags ── */
span[data-baseweb="tag"] {
    background-color: #006778 !important;
    color: #ffffff !important;
}

/* ── Multiselect tag close button ── */
span[data-baseweb="tag"] span[role="presentation"] {
    color: #ffffff !important;
}

/* ── Sidebar divider ── */
section[data-testid="stSidebar"] hr {
    border-color: #006778;
    opacity: 0.3;
}
</style>
""", unsafe_allow_html=True)

# ── Callbacks ─────────────────────────────────────────────────────────────────
def on_view_details(row_index):
    st.session_state.selected_project = row_index

# ── Load data ─────────────────────────────────────────────────────────────────
sheet_url = st.secrets["sheet_url"]
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet=sheet_url)

# Named aliases for the columns we know about
COL_NAME  = "Project Name"
COL_DESC  = "Service"
COL_URL   = "Signup Link"

# ── Custom project card ───────────────────────────────────────────────────────
def project_card(row, row_index):
    st.markdown(f"""
    <div class="project-card">
        <h3>{row[COL_NAME]}</h3>
        <div class="badges">
            <span class="badge badge-category">🏷️ {row['Category']}</span>
            <span class="badge badge-day">📅 {row['Day']}</span>
        </div>
        <p class="service">{row[COL_DESC]}</p>
    </div>
    """, unsafe_allow_html=True)
    st.button(
        "View Details",
        key=f"view_{row_index}",
        use_container_width=True,
        on_click=on_view_details,
        args=(row_index,),
        type="primary",
    )

# ── Project details dialog ────────────────────────────────────────────────────
@st.dialog("Project Details", width="medium")
def show_project_details(row):
    st.title(str(row[COL_NAME]))

    DISPLAY_COLS = [
        "Service",
        "Day",
        "Start Time",
        "End Time",
        "Minimum Age",
        "Volunteer Requirements",
        "Address",
    ]

    rows_html = ""
    for col in DISPLAY_COLS:
        value = row[col]
        if pd.isna(value) if not isinstance(value, str) else value == "":
            value = "—"
        rows_html += f"""
        <div class="detail-row">
            <span class="detail-label">{col}</span>
            <span class="detail-value">{value}</span>
        </div>
        """

    st.markdown(rows_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.link_button(
        "Sign Up",
        url=str(row[COL_URL]),
        type="primary",
        use_container_width=False,
    )

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

# Columns to skip from filters (free-text or URL-like columns)
SKIP_COLS = {COL_NAME, COL_DESC, COL_URL, "Volunteers Requested", "Category", "Day", "Minimum Age"}

filtered_data = data.copy()

# ── Category filter (explicit) ─────────────────────────────────────────────
category_vals = sorted(data["Category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    label="Category",
    options=category_vals,
    default=category_vals,
)
if selected_categories:
    filtered_data = filtered_data[filtered_data["Category"].isin(selected_categories)]

# ── Day filter (explicit) ──────────────────────────────────────────────────
day_vals = sorted(data["Day"].dropna().unique().tolist())
selected_days = st.sidebar.multiselect(
    label="Day",
    options=day_vals,
    default=day_vals,
)
if selected_days:
    filtered_data = filtered_data[filtered_data["Day"].isin(selected_days)]

for col in data.columns:
    if col in SKIP_COLS:
        continue

    series = data[col].dropna()

    # ── Low-cardinality object column → multiselect ───────────────────────
    if pd.api.types.is_object_dtype(series):
        unique_vals = sorted(series.unique().tolist())

        if 2 <= len(unique_vals) <= 30:
            selected_vals = st.sidebar.multiselect(
                label=str(col),
                options=unique_vals,
                default=unique_vals,
            )
            if selected_vals:
                filtered_data = filtered_data[
                    filtered_data[col].isin(selected_vals)
                ]

st.sidebar.markdown("---")
st.sidebar.caption(f"Showing **{len(filtered_data)}** of **{len(data)}** projects")

# ── Metrics ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: #f0f6f7;
    border: 1px solid #006778;
    border-radius: 10px;
    padding: 12px 16px;
}
div[data-testid="stMetric"] label {
    color: #006778 !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #006D55 !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Row 1: Total Projects (emphasized) ───────────────────────────────────────
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #006778, #006D55);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 24px;
">
    <div>
        <div style="color: rgba(255,255,255,0.75); font-size: 0.78rem; font-weight: 700;
                    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
            Total Projects
        </div>
        <div style="color: #ffffff; font-size: 3rem; font-weight: 900; line-height: 1;">
            {len(filtered_data)}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Row 2: per-day counts ─────────────────────────────────────────────────────
day_counts  = filtered_data["Day"].value_counts()
active_days = [d for d in sorted(data["Day"].dropna().unique().tolist()) if day_counts.get(d, 0) > 0]

day_cols = st.columns(len(active_days))
for day, col in zip(active_days, day_cols):
    with col:
        st.metric(f"{day}", day_counts.get(day, 0))

# ── Row 3: per-category counts ────────────────────────────────────────────────
category_counts   = filtered_data["Category"].value_counts()
active_categories = [c for c in sorted(data["Category"].dropna().unique().tolist()) if category_counts.get(c, 0) > 0]

cat_cols = st.columns(len(active_categories)) if active_categories else []
for category, col in zip(active_categories, cat_cols):
    with col:
        st.metric(category, category_counts.get(category, 0))

st.markdown("---")

# ── Project cards (2-column grid, dynamic) ────────────────────────────────────
if filtered_data.empty:
    st.info("No projects match the selected filters.")
else:
    rows = [filtered_data.iloc[i : i + 2] for i in range(0, len(filtered_data), 2)]

    for row_df in rows:
        cols = st.columns(len(row_df), gap="medium")
        for col_ui, (row_index, row) in zip(cols, row_df.iterrows()):
            with col_ui:
                project_card(row, row_index)

# ── Open dialog after cards are rendered so first click is caught same run ────
if "selected_project" in st.session_state:
    idx = st.session_state.pop("selected_project")
    show_project_details(data.loc[idx])