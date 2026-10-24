"""Streamlit companion dashboard for University Research Analytics."""
import io
import time
import pandas as pd
import streamlit as st

from core.config import get_serpapi_key, save_serpapi_key
from core.parser import detect_columns, extract_staff_records, read_staff_dataframe
from core.scholar_client import ScholarClient
from core.analytics import compute_department_breakdown, compute_kpis, compute_leaderboard
from core.exporter import export_to_csv, export_to_excel

st.set_page_config(page_title="UniScholar Analytics", page_icon="📚", layout="wide")

# Banner linking to executive modern dashboard
st.info("💡 **Executive Modern Web Dashboard Available**: Run `python main.py` in your terminal to launch the full-featured interactive web dashboard at **http://127.0.0.1:8000** with dark mode, candidate disambiguation modal, and Chart.js analytics.")

st.title("📚 University Research Analytics Dashboard")
st.caption("Discover Google Scholar profiles and collect citation metrics for department staff.")

with st.sidebar:
    st.header("Configuration")
    default_key = get_serpapi_key()
    api_key = st.text_input(
        "SerpApi API key",
        value=default_key,
        type="password",
        help="Required for automated Google Scholar profile discovery.",
    )
    if api_key and api_key != default_key:
        save_serpapi_key(api_key)

    institution = st.text_input("Institution (optional)", value="University of Lagos", placeholder="e.g. University of Lagos")
    use_mock = st.checkbox("Demo / Mock Mode (Zero API credits)", value=(not bool(api_key)))
    st.info("Profile matches should be verified before using the results in official reports.")

uploaded = st.file_uploader("Upload staff Excel/CSV file", type=["xlsx", "xls", "csv"])

if uploaded:
    try:
        staff_df = read_staff_dataframe(uploaded.getvalue(), uploaded.name)
        st.subheader("Staff list preview")
        st.dataframe(staff_df.head(15), use_container_width=True)

        name_col, dept_col = detect_columns(list(staff_df.columns))
        col1, col2 = st.columns(2)
        with col1:
            if not name_col:
                name_col = st.selectbox("Select Staff-name column", options=list(staff_df.columns))
            else:
                st.write(f"Detected name column: **{name_col}**")
        with col2:
            if not dept_col:
                dept_col = st.selectbox("Department column (optional)", options=["(none)"] + list(staff_df.columns))
                if dept_col == "(none)":
                    dept_col = None
            else:
                st.write(f"Detected department column: **{dept_col}**")

        if not api_key and not use_mock:
            st.warning("Add your SerpApi key in the sidebar, or enable Demo Mode to preview.")
        else:
            if st.button("🚀 Discover profiles and collect metrics", type="primary"):
                records = extract_staff_records(staff_df, name_col, dept_col)
                client = ScholarClient(api_key=api_key, enable_cache=True)
                results = []
                progress = st.progress(0)
                status = st.empty()
                total = len(records)

                for idx, rec in enumerate(records):
                    name = rec["name"]
                    dept = rec["department"]
                    status.write(f"Searching ({idx + 1}/{total}): **{name}**...")
                    base = {
                        "id": rec["id"],
                        "staff_name": name,
                        "department": dept,
                        "match_status": "No profile found",
                        "profile_name": "",
                        "affiliation": "",
                        "profile_url": "",
                        "candidate_count": 0,
                        "citations_all": 0,
                        "citations_recent": 0,
                        "h_index_all": 0,
                        "h_index_recent": 0,
                        "i10_index_all": 0,
                        "i10_index_recent": 0
                    }
                    try:
                        cands = client.discover_candidates(name, dept, institution, use_mock=use_mock)
                        base["candidate_count"] = len(cands)
                        if cands:
                            top = cands[0]
                            aid = top.get("author_id", "")
                            metrics = client.get_metrics(aid, use_mock=use_mock) if aid else {}
                            base.update({
                                "match_status": "Needs verification",
                                "profile_name": top.get("name", ""),
                                "affiliation": top.get("affiliations", ""),
                                "profile_url": top.get("profile_url", ""),
                                **metrics
                            })
                    except Exception as e:
                        base["match_status"] = f"Error: {e}"

                    results.append(base)
                    progress.progress(min((idx + 1) / max(total, 1), 1.0))
                    time.sleep(0.05)

                status.success("Collection finished! Review matches below.")
                st.session_state["results"] = results

        if "results" in st.session_state:
            results = st.session_state["results"]
            kpis = compute_kpis(results)
            depts = compute_department_breakdown(results)

            # KPI metrics
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Faculty", kpis["total_staff"])
            m2.metric("Profiles Matched", f"{kpis['matched_count']} ({kpis['match_rate']}%)")
            m3.metric("Total Citations", f"{kpis['total_citations_all']:,}")
            m4.metric("Average h-index", kpis["avg_h_index"])

            st.subheader("Collection Results")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                csv_bytes = export_to_csv(results)
                st.download_button("📥 Download Results as CSV", data=csv_bytes, file_name="faculty_scholar_metrics.csv", mime="text/csv")
            with c2:
                excel_bytes = export_to_excel(results, kpis, depts)
                st.download_button("📊 Download Formatted Excel Report", data=excel_bytes, file_name="faculty_scholar_metrics.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as exc:
        st.error(f"Couldn't read file: {exc}")
else:
    st.markdown("### Expected Input Format")
    st.write("Upload an Excel file with at least a staff-name column. A department column is recommended.")
    st.dataframe(pd.DataFrame({"Names": ["Prof. Example A. Lecturer", "Dr. Example B. Researcher"], "Department": ["Chemistry", "Physics"]}), use_container_width=True, hide_index=True)

st.divider()
st.caption("Metrics are retrieved from Google Scholar via SerpApi. Verify every profile before official use.")
