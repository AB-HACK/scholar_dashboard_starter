"""Analytics calculation engine for departmental metrics and executive KPIs."""
from typing import Any, Dict, List
import pandas as pd


def compute_kpis(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute executive KPI cards data from roster results."""
    total_staff = len(records)
    if total_staff == 0:
        return {
            "total_staff": 0,
            "matched_count": 0,
            "match_rate": 0.0,
            "verified_count": 0,
            "needs_verification_count": 0,
            "unmatched_count": 0,
            "total_citations_all": 0,
            "total_citations_recent": 0,
            "avg_h_index": 0.0,
            "max_h_index": 0,
            "avg_i10_index": 0.0
        }

    df = pd.DataFrame(records)
    matched = df[df.get("match_status", "").str.lower() != "no profile found"] if "match_status" in df else df
    verified = df[df.get("match_status", "").str.lower() == "verified"] if "match_status" in df else pd.DataFrame()
    needs_ver = df[df.get("match_status", "").str.lower() == "needs verification"] if "match_status" in df else pd.DataFrame()

    citations_all = pd.to_numeric(matched.get("citations_all", 0), errors="coerce").fillna(0)
    citations_recent = pd.to_numeric(matched.get("citations_recent", 0), errors="coerce").fillna(0)
    h_indices = pd.to_numeric(matched.get("h_index_all", 0), errors="coerce").fillna(0)
    i10_indices = pd.to_numeric(matched.get("i10_index_all", 0), errors="coerce").fillna(0)

    matched_count = len(matched)
    return {
        "total_staff": total_staff,
        "matched_count": matched_count,
        "match_rate": round((matched_count / total_staff) * 100, 1) if total_staff else 0.0,
        "verified_count": len(verified),
        "needs_verification_count": len(needs_ver),
        "unmatched_count": total_staff - matched_count,
        "total_citations_all": int(citations_all.sum()),
        "total_citations_recent": int(citations_recent.sum()),
        "avg_h_index": round(float(h_indices.mean()), 1) if matched_count else 0.0,
        "max_h_index": int(h_indices.max()) if matched_count else 0,
        "avg_i10_index": round(float(i10_indices.mean()), 1) if matched_count else 0.0
    }


def compute_department_breakdown(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate metrics grouped by department for visual comparison."""
    if not records:
        return []

    df = pd.DataFrame(records)
    if "department" not in df.columns:
        df["department"] = "Unassigned"
    df["department"] = df["department"].fillna("Unassigned").replace("", "Unassigned")

    departments = []
    for dept_name, group in df.groupby("department"):
        matched = group[group.get("match_status", "").str.lower() != "no profile found"] if "match_status" in group else group
        cits = pd.to_numeric(matched.get("citations_all", 0), errors="coerce").fillna(0)
        cits_rec = pd.to_numeric(matched.get("citations_recent", 0), errors="coerce").fillna(0)
        h_idx = pd.to_numeric(matched.get("h_index_all", 0), errors="coerce").fillna(0)

        # Top researcher in department
        top_name = "N/A"
        if not matched.empty and cits.max() > 0:
            top_idx = cits.idxmax()
            top_name = matched.loc[top_idx].get("staff_name", "N/A")

        departments.append({
            "department": dept_name,
            "staff_count": len(group),
            "matched_count": len(matched),
            "total_citations": int(cits.sum()),
            "recent_citations": int(cits_rec.sum()),
            "avg_h_index": round(float(h_idx.mean()), 1) if len(matched) else 0.0,
            "top_researcher": top_name
        })

    # Sort descending by total citations
    departments.sort(key=lambda d: d["total_citations"], reverse=True)
    return departments


def compute_leaderboard(records: List[Dict[str, Any]], top_n: int = 8) -> List[Dict[str, Any]]:
    """Return top researchers sorted by total citations."""
    if not records:
        return []

    df = pd.DataFrame(records)
    if "citations_all" not in df.columns:
        return []

    matched = df[df.get("match_status", "").str.lower() != "no profile found"].copy()
    matched["citations_all"] = pd.to_numeric(matched["citations_all"], errors="coerce").fillna(0).astype(int)
    matched["h_index_all"] = pd.to_numeric(matched.get("h_index_all", 0), errors="coerce").fillna(0).astype(int)
    matched["i10_index_all"] = pd.to_numeric(matched.get("i10_index_all", 0), errors="coerce").fillna(0).astype(int)

    sorted_df = matched.sort_values(by="citations_all", ascending=False).head(top_n)
    leaderboard = []
    for rank, (_, row) in enumerate(sorted_df.iterrows(), start=1):
        leaderboard.append({
            "rank": rank,
            "staff_name": row.get("staff_name", ""),
            "department": row.get("department", ""),
            "profile_name": row.get("profile_name", ""),
            "citations_all": int(row.get("citations_all", 0)),
            "citations_recent": int(row.get("citations_recent", 0)),
            "h_index_all": int(row.get("h_index_all", 0)),
            "profile_url": row.get("profile_url", "")
        })
    return leaderboard


def compute_distribution(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate bucketed distribution of h-indices for visualization."""
    if not records:
        return {"labels": [], "counts": []}

    h_buckets = {"0": 0, "1 - 5": 0, "6 - 10": 0, "11 - 20": 0, "21 - 40": 0, "40+": 0}
    for r in records:
        if str(r.get("match_status", "")).lower() == "no profile found":
            h_buckets["0"] += 1
            continue
        try:
            val = int(r.get("h_index_all") or 0)
        except Exception:
            val = 0

        if val == 0:
            h_buckets["0"] += 1
        elif 1 <= val <= 5:
            h_buckets["1 - 5"] += 1
        elif 6 <= val <= 10:
            h_buckets["6 - 10"] += 1
        elif 11 <= val <= 20:
            h_buckets["11 - 20"] += 1
        elif 21 <= val <= 40:
            h_buckets["21 - 40"] += 1
        else:
            h_buckets["40+"] += 1

    return {
        "labels": list(h_buckets.keys()),
        "counts": list(h_buckets.values())
    }
