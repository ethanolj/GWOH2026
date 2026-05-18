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

# Named aliases for the columns we know about (adjust if your sheet differs)
COL_NAME  = data.columns[4]   # project name
COL_DESC  = data.columns[5]   # description
COL_URL   = data.columns[11]  # sign-up URL

# ── Parse date/time columns (columns 8 & 9 in the sheet) ─────────────────────
# Google Sheets exports dates in M/D/YYYY H:MM format (e.g. "9/12/2026 9:00")
GSHEETS_DT_FORMAT = "%m/%d/%Y %H:%M"
DATE_COL_INDICES = [8, 9]

for idx in DATE_COL_INDICES:
    col = data.columns[idx]
    data[col] = pd.to_datetime(data[col], format=GSHEETS_DT_FORMAT, errors="coerce")

# ── Project details dialog ────────────────────────────────────────────────────
@st.dialog("Project Details", width="medium")
def show_project_details(row):
    st.title(str(row[COL_NAME]))

    for col in data.columns:
        value = row[col]

        # Format datetimes cleanly
        if pd.api.types.is_datetime64_any_dtype(data[col]) and pd.notna(value):
            value = pd.Timestamp(value).strftime("%B %d, %Y %I:%M %p")
        elif pd.isna(value) if not isinstance(value, str) else value == "":
            value = "—"

        st.header(f"**{col}**")
        st.write(value)
        st.divider()

    st.link_button(
        "Sign Up",
        url=str(row[COL_URL]),
        type="primary",
        use_container_width=True,
    )

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

# Columns to skip from filters (free-text or URL-like columns)
SKIP_COLS = {COL_NAME, COL_DESC, COL_URL}

filtered_data = data.copy()

for col in data.columns:
    if col in SKIP_COLS:
        continue

    series = data[col].dropna()

    # ── Datetime column → date + time range picker ────────────────────────
    if pd.api.types.is_datetime64_any_dtype(series):
        dt_min = series.min().to_pydatetime()
        dt_max = series.max().to_pydatetime()

        if dt_min == dt_max:            # nothing to filter
            continue

        st.sidebar.markdown(f"**{col}**")

        start_date = st.sidebar.date_input(
            label=f"{col} — from date",
            value=dt_min.date(),
            min_value=dt_min.date(),
            max_value=dt_max.date(),
            key=f"{col}_start_date",
        )
        start_time = st.sidebar.time_input(
            label=f"{col} — from time",
            value=dt_min.time(),
            step=datetime.timedelta(minutes=30),
            key=f"{col}_start_time",
        )

        end_date = st.sidebar.date_input(
            label=f"{col} — to date",
            value=dt_max.date(),
            min_value=dt_min.date(),
            max_value=dt_max.date(),
            key=f"{col}_end_date",
        )
        end_time = st.sidebar.time_input(
            label=f"{col} — to time",
            value=dt_max.time(),
            step=datetime.timedelta(minutes=30),
            key=f"{col}_end_time",
        )

        start_dt = datetime.datetime.combine(start_date, start_time)
        end_dt   = datetime.datetime.combine(end_date,   end_time)

        if start_dt > end_dt:
            st.sidebar.warning(f"'{col}': start is after end — filter ignored.")
        else:
            filtered_data = filtered_data[
                filtered_data[col].between(pd.Timestamp(start_dt), pd.Timestamp(end_dt))
            ]

    # ── Numeric column → range slider ─────────────────────────────────────
    elif pd.api.types.is_numeric_dtype(series):
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

# ── Product cards (2-column grid, dynamic) ────────────────────────────────────
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