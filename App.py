import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_product_card import product_card

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="God's Work, Our Hands 2026", layout="wide")

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

    for col in DISPLAY_COLS:
        value = row[col]

        if pd.isna(value) if not isinstance(value, str) else value == "":
            value = "—"

        st.header(f"**{col}**")
        st.write(value)
        st.divider()

    st.link_button(
        "Sign Up",
        url=str(row[COL_URL]),
        type="primary",
        use_container_width=False,
    )

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

# Columns to skip from filters (free-text or URL-like columns)
SKIP_COLS = {COL_NAME, COL_DESC, COL_URL, "Volunteers Requested", "Category", "Day"}

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

    # ── Numeric column → range slider ─────────────────────────────────────
    if pd.api.types.is_numeric_dtype(series):
        col_min = float(series.min())
        col_max = float(series.max())

        if col_min == col_max:          # nothing to filter
            continue

        selected_range = st.sidebar.slider(
            label=str(col),
            min_value=col_min,
            max_value=col_max,
            value=(col_min, col_max),
        )
        filtered_data = filtered_data[
            filtered_data[col].between(selected_range[0], selected_range[1])
        ]

    # ── Low-cardinality object column → multiselect ───────────────────────
    elif pd.api.types.is_object_dtype(series):
        unique_vals = sorted(series.unique().tolist())

        # Only show multiselect when there are between 2 and 30 distinct values
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

# ── Project cards (2-column grid, dynamic) ────────────────────────────────────
if filtered_data.empty:
    st.info("No projects match the selected filters.")
else:
    rows = [filtered_data.iloc[i : i + 2] for i in range(0, len(filtered_data), 2)]

    for row_df in rows:
        cols = st.columns(len(row_df), gap="medium")
        for col_ui, (row_index, row) in zip(cols, row_df.iterrows()):
            with col_ui:
                product_card(
                    product_name=str(row[COL_NAME]),
                    description=str(row[COL_DESC]),
                    button_text="View Details",
                    on_button_click=lambda idx=row_index: on_view_details(idx),
                    styles={"button": {"background-color": "green", "color": "white"}},
                )

# ── Open dialog after cards are rendered so first click is caught same run ────
if "selected_project" in st.session_state:
    idx = st.session_state.pop("selected_project")
    show_project_details(data.loc[idx])