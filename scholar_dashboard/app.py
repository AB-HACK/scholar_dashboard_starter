import os
import time
import requests
import pandas as pd
import streamlit as st

API_KEY = st.secrets["SERPAPI_KEY"]

SERPAPI_URL = "https://serpapi.com/search.json"

st.set_page_config(page_title="University Research Analytics", page_icon="📚", layout="wide")
st.title("University Research Analytics Dashboard")
st.caption("Discover Google Scholar profiles and collect citation metrics for department staff.")

with st.sidebar:
    st.header("Configuration")
    default_key = st.secrets.get("SERPAPI_KEY", os.getenv("SERPAPI_API_KEY", ""))
    api_key = st.text_input(
        "SerpApi API key",
        value=default_key,
        type="password",
        help="Required for automated Google Scholar profile discovery.",
    )
    institution = st.text_input("Institution (optional)", placeholder="e.g. University of Lagos")
    st.info("Profile matches should be checked before using the results in official reports.")

uploaded = st.file_uploader("Upload staff Excel/CSV file", type=["xlsx", "xls", "csv"])


def read_staff(file):
    if file.name.lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_column(columns, terms):
    for col in columns:
        low = col.lower().strip()
        if any(term in low for term in terms):
            return col
    return None


def serpapi_search(params, key):
    params["api_key"] = key
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data


def discover_profiles(name, department, institution_name, key):
    query_parts = [str(name).strip()]
    if department and pd.notna(department):
        query_parts.append(str(department).strip())
    if institution_name.strip():
        query_parts.append(institution_name.strip())
    
    # Use google_scholar engine (google_scholar_profiles was discontinued by SerpApi)
    data = serpapi_search({"engine": "google_scholar", "q": " ".join(query_parts)}, key)
    
    profiles_data = data.get("profiles", {})
    if isinstance(profiles_data, dict):
        candidates = profiles_data.get("authors", [])
    elif isinstance(profiles_data, list):
        candidates = profiles_data
    else:
        candidates = []

    # Fallback to checking author links in organic results if no author banner appeared
    if not candidates:
        for item in data.get("organic_results", []):
            for author in item.get("publication_info", {}).get("authors", []):
                if author.get("author_id"):
                    candidates.append({
                        "name": author.get("name", ""),
                        "author_id": author.get("author_id", ""),
                        "link": author.get("link", ""),
                        "affiliations": "",
                        "email": "",
                    })

    cleaned = []
    seen_ids = set()
    for p in candidates[:5]:
        aid = p.get("author_id", "")
        if aid and aid in seen_ids:
            continue
        if aid:
            seen_ids.add(aid)
        cleaned.append({
            "name": p.get("name", ""),
            "affiliations": p.get("affiliations", ""),
            "email": p.get("email", ""),
            "author_id": aid,
            "profile_url": p.get("link", ""),
        })
    return cleaned


def get_metrics(author_id, key):
    data = serpapi_search({"engine": "google_scholar_author", "author_id": author_id, "hl": "en"}, key)
    table = (data.get("cited_by") or {}).get("table", [])
    result = {
        "citations_all": None, "citations_recent": None,
        "h_index_all": None, "h_index_recent": None,
        "i10_index_all": None, "i10_index_recent": None,
    }

    # SerpApi cited_by.table format:
    # [{'citations': {'all': 905, 'since_2021': 468}}, {'h_index': ...}, {'i10_index': ...}]
    for row in table:
        if not isinstance(row, dict):
            continue
        for metric, (all_key, recent_key) in [
            ("citations", ("citations_all", "citations_recent")),
            ("h_index", ("h_index_all", "h_index_recent")),
            ("i10_index", ("i10_index_all", "i10_index_recent")),
        ]:
            if metric in row and isinstance(row[metric], dict):
                sub = row[metric]
                result[all_key] = sub.get("all")
                for k, v in sub.items():
                    if k.startswith("since"):
                        result[recent_key] = v
                        break
    return result

if uploaded:
    try:
        staff_df = read_staff(uploaded)
        st.subheader("Staff list preview")
        st.dataframe(staff_df.head(20), use_container_width=True)
        name_col = find_column(staff_df.columns, ["name", "staff", "lecturer", "researcher", "full name"])
        dept_col = find_column(staff_df.columns, ["department", "dept"])
        if not name_col:
            st.error("I couldn't identify the staff-name column. Rename it to 'Name' or select it below.")
            name_col = st.selectbox("Staff-name column", options=list(staff_df.columns))
        if not dept_col:
            dept_col = st.selectbox("Department column (optional)", options=["(none)"] + list(staff_df.columns))
            if dept_col == "(none)":
                dept_col = None
        st.write(f"Detected name column: **{name_col}**" + (f" · Department column: **{dept_col}**" if dept_col else ""))

        if not api_key:
            st.warning("Add your SerpApi key in the sidebar to enable automatic profile discovery. The dashboard preview works without it.")
        else:
            if st.button("Discover profiles and collect metrics", type="primary"):
                results = []
                progress = st.progress(0)
                status = st.empty()
                total = len(staff_df)
                for idx, row in staff_df.iterrows():
                    name = str(row.get(name_col, "")).strip()
                    dept = row.get(dept_col, "") if dept_col else ""
                    if not name or name.lower() == "nan":
                        continue
                    status.write(f"Searching for {name} ({len(results) + 1}/{total})…")
                    base = {"Staff Name": name, "Department": str(dept) if pd.notna(dept) else ""}
                    try:
                        candidates = discover_profiles(name, dept, institution, api_key)
                        if not candidates:
                            results.append({**base, "Match Status": "No profile found", "Profile Name": "", "Affiliation": "", "Profile URL": "", "Candidate Count": 0})
                        else:
                            # Use top search result as a candidate, but flag it for human confirmation.
                            candidate = candidates[0]
                            metrics = get_metrics(candidate["author_id"], api_key) if candidate.get("author_id") else {}
                            results.append({
                                **base,
                                "Match Status": "Needs verification",
                                "Profile Name": candidate.get("name", ""),
                                "Affiliation": candidate.get("affiliations", ""),
                                "Profile URL": candidate.get("profile_url", ""),
                                "Candidate Count": len(candidates),
                                **metrics,
                            })
                    except Exception as exc:
                        results.append({**base, "Match Status": f"Error: {exc}", "Profile Name": "", "Affiliation": "", "Profile URL": ""})
                    progress.progress(min((idx + 1) / max(total, 1), 1.0))
                    time.sleep(0.2)
                status.write("Collection finished. Review profile matches before using metrics.")
                st.session_state["results"] = pd.DataFrame(results)

        if "results" in st.session_state:
            results_df = st.session_state["results"]
            st.subheader("Collection results")
            st.caption("All discovered matches are marked for verification; confirm that the profile belongs to the intended staff member.")
            st.dataframe(results_df, use_container_width=True, hide_index=True)
            csv = results_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Download results as CSV", data=csv, file_name="chemistry_staff_metrics.csv", mime="text/csv")
            try:
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    results_df.to_excel(writer, index=False, sheet_name="Staff Metrics")
                st.download_button("Download results as Excel", data=buffer.getvalue(), file_name="chemistry_staff_metrics.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception:
                st.info("Excel export requires openpyxl. CSV export is available meanwhile.")
    except Exception as exc:
        st.error(f"Couldn't read this file: {exc}")
else:
    st.markdown("### Expected input format")
    st.write("Upload an Excel file with at least a staff-name column. A department column is recommended.")
    st.dataframe(pd.DataFrame({"Names": ["Prof. Example A. Lecturer", "Dr. Example B. Researcher"], "Department": ["Chemistry", "Chemistry"]}), use_container_width=True, hide_index=True)

st.divider()
st.caption("Metrics are retrieved from a third-party Google Scholar data provider. Availability, accuracy, pricing, and permitted use depend on that provider and Google Scholar's access policies. Verify every profile before official use.")
