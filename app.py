import html
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Vendor Outreach Tracker",
    page_icon="📋",
    layout="wide",
)

STATUS_ORDER = [
    "Not contacted",
    "Contacted",
    "Follow-up needed",
    "Interested",
    "Quoted",
    "Onboarding",
    "Onboarded",
    "Rejected",
]

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1200px;}
    .demo-note {font-size: .88rem; color: #8b949e; margin-top: -.4rem;}
    .table-wrap {overflow-x:auto; -webkit-overflow-scrolling:touch; border:1px solid rgba(128,128,128,.22); border-radius:12px; margin:.4rem 0 1rem 0;}
    table.demo-table {border-collapse:collapse; width:100%; min-width:760px; font-size:.9rem;}
    .demo-table th {text-align:left; padding:11px 12px; background:rgba(128,128,128,.12); white-space:nowrap;}
    .demo-table td {padding:10px 12px; border-top:1px solid rgba(128,128,128,.16); vertical-align:top;}
    .pill {display:inline-block; padding:3px 8px; border-radius:999px; background:rgba(128,128,128,.16); font-size:.78rem; white-space:nowrap;}
    .pipeline-row {display:grid; grid-template-columns:145px 1fr 38px; gap:10px; align-items:center; margin:10px 0;}
    .pipeline-track {height:12px; background:rgba(128,128,128,.18); border-radius:999px; overflow:hidden;}
    .pipeline-fill {height:100%; background:#ff4b4b; border-radius:999px;}
    @media (max-width: 700px) {
      .block-container {padding-left:1rem; padding-right:1rem;}
      .pipeline-row {grid-template-columns:112px 1fr 26px; font-size:.86rem;}
      div[data-testid="stMetricValue"] {font-size:1.65rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_default():
    df = pd.read_csv("sample_vendors.csv")
    for col in ["Last Contact", "Next Follow-up"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def normalize_dates(df):
    out = df.copy()
    for col in ["Last Contact", "Next Follow-up"]:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def due_label(row, today):
    if row["Status"] in ["Onboarded", "Rejected"]:
        return "Closed"
    next_followup = row.get("Next Follow-up")
    if pd.isna(next_followup):
        return "No date"
    next_date = pd.Timestamp(next_followup).date()
    if next_date < today:
        return "Overdue"
    if next_date == today:
        return "Due today"
    return "Upcoming"


def display_value(value):
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d %b %Y")
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}"
    return str(value)


def render_table(frame, columns):
    if frame.empty:
        st.info("No records to show.")
        return
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in columns)
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for col in columns:
            value = display_value(row[col])
            if col in ["Status", "Follow-up Flag"]:
                value = f'<span class="pill">{html.escape(value)}</span>'
            else:
                value = html.escape(value)
            cells.append(f"<td>{value}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    table = (
        '<div class="table-wrap"><table class="demo-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )
    st.markdown(table, unsafe_allow_html=True)


if "vendors" not in st.session_state:
    st.session_state.vendors = load_default()

st.title("Vendor Outreach Tracker")
st.markdown(
    '<div class="demo-note">Working demo for vendor outreach, follow-ups, qualification and onboarding.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload vendor CSV", type=["csv"])
    if uploaded is not None:
        try:
            uploaded_df = pd.read_csv(uploaded)
            required = [
                "Vendor ID", "Vendor Name", "Contact Person", "Phone", "Email",
                "Location", "Products", "Printing Methods", "Price / Unit (₹)",
                "Monthly Capacity", "Status", "Last Contact", "Next Follow-up", "Notes",
            ]
            missing = [c for c in required if c not in uploaded_df.columns]
            if missing:
                st.error("Missing columns: " + ", ".join(missing))
            else:
                st.session_state.vendors = normalize_dates(uploaded_df[required])
                st.success("Vendor file loaded")
        except Exception as exc:
            st.error(f"Could not read file: {exc}")

    if st.button("Reset to sample data"):
        st.session_state.vendors = load_default()
        st.rerun()


df = normalize_dates(st.session_state.vendors)
today = date.today()
df["Follow-up Flag"] = df.apply(lambda row: due_label(row, today), axis=1)

total = len(df)
contacted = int((df["Status"] != "Not contacted").sum())
open_pipeline = int((~df["Status"].isin(["Onboarded", "Rejected"])).sum())
onboarding = int((df["Status"] == "Onboarding").sum())
overdue = int((df["Follow-up Flag"] == "Overdue").sum())

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total vendors", total)
m2.metric("Contacted", contacted)
m3.metric("Open pipeline", open_pipeline)
m4.metric("Onboarding", onboarding)
m5.metric("Overdue follow-ups", overdue)

tabs = st.tabs(["Follow-ups", "Vendor List", "Vendor Detail", "Pipeline", "Add Vendor"])

with tabs[0]:
    st.subheader("Follow-up queue")
    follow = df[df["Follow-up Flag"].isin(["Overdue", "Due today"])].copy()
    follow["Days Since Last Contact"] = (pd.Timestamp(today) - follow["Last Contact"]).dt.days
    follow = follow.sort_values(
        by=["Follow-up Flag", "Next Follow-up", "Days Since Last Contact"],
        ascending=[True, True, False],
    )
    if follow.empty:
        st.success("No follow-ups are due today.")
    else:
        render_table(
            follow,
            ["Vendor Name", "Contact Person", "Location", "Status", "Last Contact", "Next Follow-up", "Follow-up Flag", "Notes"],
        )

with tabs[1]:
    st.subheader("Vendor list")
    c1, c2, c3 = st.columns(3)
    with c1:
        statuses = st.multiselect("Filter by status", STATUS_ORDER)
    with c2:
        locations = st.multiselect(
            "Filter by location",
            sorted(df["Location"].dropna().astype(str).unique().tolist()),
        )
    with c3:
        search = st.text_input("Search vendor/product")

    filtered = df.copy()
    if statuses:
        filtered = filtered[filtered["Status"].isin(statuses)]
    if locations:
        filtered = filtered[filtered["Location"].isin(locations)]
    if search:
        query = search.lower()
        filtered = filtered[
            filtered.astype(str).apply(
                lambda row: row.str.lower().str.contains(query).any(), axis=1
            )
        ]

    display_cols = [
        "Vendor Name", "Location", "Products", "Printing Methods", "Price / Unit (₹)",
        "Monthly Capacity", "Status", "Next Follow-up", "Follow-up Flag",
    ]
    render_table(filtered, display_cols)

    export = filtered.drop(columns=["Follow-up Flag"]).copy()
    for col in ["Last Contact", "Next Follow-up"]:
        export[col] = export[col].dt.strftime("%Y-%m-%d").fillna("")
    st.download_button(
        "Download filtered CSV",
        data=export.to_csv(index=False).encode("utf-8"),
        file_name="vendor_pipeline_export.csv",
        mime="text/csv",
    )

with tabs[2]:
    st.subheader("Vendor detail")
    names = df["Vendor Name"].tolist()
    selected = st.selectbox("Choose a vendor", names)
    row = df[df["Vendor Name"] == selected].iloc[0]

    left, right = st.columns([1, 1])
    with left:
        st.markdown(f"### {row['Vendor Name']}")
        st.write(f"**Contact:** {row['Contact Person']}")
        st.write(f"**Phone:** {row['Phone']}")
        st.write(f"**Email:** {row['Email']}")
        st.write(f"**Location:** {row['Location']}")
        st.write(f"**Products:** {row['Products']}")
        st.write(f"**Printing methods:** {row['Printing Methods']}")
    with right:
        st.write(f"**Status:** {row['Status']}")
        st.write(f"**Price / unit:** ₹{row['Price / Unit (₹)']}")
        st.write(f"**Monthly capacity:** {int(row['Monthly Capacity']):,}")
        st.write("**Last contact:** " + (row["Last Contact"].strftime("%d %b %Y") if pd.notna(row["Last Contact"]) else "Not contacted"))
        st.write("**Next follow-up:** " + (row["Next Follow-up"].strftime("%d %b %Y") if pd.notna(row["Next Follow-up"]) else "Not scheduled"))
        st.write(f"**Follow-up:** {row['Follow-up Flag']}")
    st.info(row["Notes"] if str(row["Notes"]).strip() else "No notes added.")

with tabs[3]:
    st.subheader("Pipeline summary")
    status_counts = df["Status"].value_counts().reindex(STATUS_ORDER, fill_value=0)
    max_count = max(int(status_counts.max()), 1)
    pipeline_html = []
    for status, count in status_counts.items():
        width = max(4, int((int(count) / max_count) * 100)) if int(count) else 0
        pipeline_html.append(
            f'<div class="pipeline-row"><div>{html.escape(status)}</div>'
            f'<div class="pipeline-track"><div class="pipeline-fill" style="width:{width}%"></div></div>'
            f'<div>{int(count)}</div></div>'
        )
    st.markdown("".join(pipeline_html), unsafe_allow_html=True)

    st.subheader("Vendor comparison")
    compare = df[~df["Status"].isin(["Rejected"])][
        ["Vendor Name", "Location", "Price / Unit (₹)", "Monthly Capacity", "Status"]
    ].sort_values(["Price / Unit (₹)", "Monthly Capacity"], ascending=[True, False])
    render_table(compare, ["Vendor Name", "Location", "Price / Unit (₹)", "Monthly Capacity", "Status"])

with tabs[4]:
    st.subheader("Add a vendor")
    with st.form("add_vendor_form", clear_on_submit=True):
        a, b = st.columns(2)
        with a:
            vendor_name = st.text_input("Vendor name")
            contact_person = st.text_input("Contact person")
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            location = st.text_input("Location")
            products = st.text_input("Products")
            methods = st.text_input("Printing methods")
        with b:
            price = st.number_input("Price / unit (₹)", min_value=0.0, step=1.0)
            capacity = st.number_input("Monthly capacity", min_value=0, step=100)
            status = st.selectbox("Status", STATUS_ORDER)
            last_contact = st.date_input("Last contact", value=None)
            next_follow = st.date_input("Next follow-up", value=None)
            notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add vendor")

        if submitted:
            if not vendor_name.strip():
                st.error("Vendor name is required.")
            else:
                existing = st.session_state.vendors.copy()
                next_num = len(existing) + 1
                new_row = {
                    "Vendor ID": f"V{next_num:03d}",
                    "Vendor Name": vendor_name.strip(),
                    "Contact Person": contact_person.strip(),
                    "Phone": phone.strip(),
                    "Email": email.strip(),
                    "Location": location.strip(),
                    "Products": products.strip(),
                    "Printing Methods": methods.strip(),
                    "Price / Unit (₹)": price,
                    "Monthly Capacity": capacity,
                    "Status": status,
                    "Last Contact": pd.to_datetime(last_contact) if last_contact else pd.NaT,
                    "Next Follow-up": pd.to_datetime(next_follow) if next_follow else pd.NaT,
                    "Notes": notes.strip(),
                }
                st.session_state.vendors = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Vendor added.")
                st.rerun()

st.divider()
st.caption("Demo uses synthetic data only. A production version could connect to the team's existing Google Sheet or CRM.")
