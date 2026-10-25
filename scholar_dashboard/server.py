"""FastAPI backend server linking modern dashboard UI with Scholar analytics engine."""
import asyncio
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import get_serpapi_key, save_serpapi_key
from core.parser import detect_columns, extract_staff_records, read_staff_dataframe
from core.scholar_client import ScholarClient
from core.analytics import compute_department_breakdown, compute_distribution, compute_kpis, compute_leaderboard
from core.exporter import export_to_csv, export_to_excel

app = FastAPI(title="UniScholar Analytics API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# In-memory session state for active dashboard session
dashboard_state: Dict[str, Any] = {
    "records": [],
    "is_running": False,
    "progress": 0.0,
    "current_status": "Ready",
    "institution": "University of Lagos"
}


class ConfigPayload(BaseModel):
    api_key: str
    institution: Optional[str] = "University of Lagos"


class VerifyPayload(BaseModel):
    staff_id: str
    author_id: Optional[str] = None
    profile_name: Optional[str] = None
    affiliation: Optional[str] = None
    status: str = "Verified"
    use_mock: bool = False


class DiscoveryPayload(BaseModel):
    records: List[Dict[str, Any]]
    institution: Optional[str] = ""
    api_key: Optional[str] = ""
    use_mock: bool = False


@app.get("/api/status")
async def get_system_status():
    configured_key = get_serpapi_key()
    has_key = bool(configured_key and len(configured_key) > 8)
    return {
        "status": "online",
        "has_api_key": has_key,
        "api_key_masked": (configured_key[:4] + "..." + configured_key[-4:]) if has_key else "",
        "institution": dashboard_state.get("institution", "University of Lagos"),
        "total_cached": len(dashboard_state.get("records", [])),
        "is_running": dashboard_state.get("is_running", False),
        "progress": dashboard_state.get("progress", 0.0),
        "current_status": dashboard_state.get("current_status", "Ready")
    }


@app.get("/api/account")
async def get_account_status(api_key: Optional[str] = None, use_mock: bool = False):
    """Retrieve SerpApi remaining credits, subscription tier, and quota status."""
    active_key = api_key.strip() if api_key else get_serpapi_key()
    client = ScholarClient(api_key=active_key)
    return client.get_account_info(use_mock=use_mock)


@app.post("/api/config")
async def update_config(payload: ConfigPayload):
    if payload.api_key:
        save_serpapi_key(payload.api_key)
    if payload.institution:
        dashboard_state["institution"] = payload.institution.strip()
    return {"message": "Configuration updated successfully"}


@app.post("/api/upload")
async def upload_staff_file(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = read_staff_dataframe(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    name_col, dept_col = detect_columns(list(df.columns))
    preview_rows = df.head(10).to_dict(orient="records")

    records = []
    if name_col:
        records = extract_staff_records(df, name_col, dept_col)

    return {
        "filename": file.filename,
        "total_rows": len(df),
        "columns": list(df.columns),
        "detected_name_col": name_col,
        "detected_dept_col": dept_col,
        "preview": preview_rows,
        "extracted_count": len(records),
        "extracted_records": records
    }


@app.get("/api/sample")
async def get_sample_faculty():
    """Provide realistic sample academic department data for immediate testing."""
    sample_records = [
        {"id": "staff_1", "name": "Prof. Oluwatoyin Temitayo Ogundipe", "department": "Botany", "raw_index": 0},
        {"id": "staff_2", "name": "Prof. Folasade Tolulope Ogunsola", "department": "Medical Microbiology", "raw_index": 1},
        {"id": "staff_3", "name": "Prof. Babajide Alo", "department": "Chemistry", "raw_index": 2},
        {"id": "staff_4", "name": "Prof. Kehinde Olayinka", "department": "Chemistry", "raw_index": 3},
        {"id": "staff_5", "name": "Dr. Chika Yinka-Banjo", "department": "Computer Sciences", "raw_index": 4},
        {"id": "staff_6", "name": "Prof. Elijah Ayolabi", "department": "Geosciences", "raw_index": 5},
        {"id": "staff_7", "name": "Dr. Isaac A. Omoleke", "department": "Public Administration", "raw_index": 6},
        {"id": "staff_8", "name": "Prof. Lucian Obinna Chukwu", "department": "Marine Sciences", "raw_index": 7},
        {"id": "staff_9", "name": "Dr. Mary Kehinde Ladapo", "department": "Pharmacology", "raw_index": 8},
        {"id": "staff_10", "name": "Prof. Sunday Adebisi", "department": "Business Administration", "raw_index": 9},
        {"id": "staff_11", "name": "Dr. Hakeem Olanrewaju Amuda", "department": "Metallurgical & Materials", "raw_index": 10},
        {"id": "staff_12", "name": "Dr. Grace O. Babafemi", "department": "Biochemistry", "raw_index": 11}
    ]
    return {
        "filename": "faculty_sample_chemistry_sciences.xlsx",
        "total_rows": len(sample_records),
        "columns": ["Name", "Department"],
        "detected_name_col": "Name",
        "detected_dept_col": "Department",
        "preview": sample_records[:5],
        "extracted_count": len(sample_records),
        "extracted_records": sample_records
    }


@app.post("/api/discover")
async def run_discovery(payload: DiscoveryPayload):
    """Run batch discovery for staff records, updating progress and session state."""
    active_key = payload.api_key.strip() if payload.api_key else get_serpapi_key()
    institution = payload.institution.strip() if payload.institution else dashboard_state.get("institution", "")
    use_mock = payload.use_mock or (not active_key)

    client = ScholarClient(api_key=active_key, enable_cache=True)
    total = len(payload.records)
    if total == 0:
        raise HTTPException(status_code=400, detail="No staff records provided for discovery.")

    if not use_mock and active_key:
        acc_info = client.get_account_info(use_mock=False)
        left = acc_info.get("total_searches_left")
        if left is not None and left <= 0:
            raise HTTPException(
                status_code=400,
                detail="SerpApi credit quota is 0. Live searches cannot be executed. Please enable Demo / Mock Mode or recharge your plan."
            )

    dashboard_state["is_running"] = True
    dashboard_state["progress"] = 0.0
    dashboard_state["current_status"] = f"Starting discovery for {total} staff..."

    results = []
    for idx, item in enumerate(payload.records):
        name = item.get("name", "").strip()
        dept = item.get("department", "").strip()
        staff_id = item.get("id", f"staff_{idx + 1}")

        dashboard_state["current_status"] = f"Processing ({idx + 1}/{total}): {name}"
        dashboard_state["progress"] = round(((idx + 1) / total) * 100, 1)

        base_res = {
            "id": staff_id,
            "staff_name": name,
            "department": dept,
            "match_status": "No profile found",
            "profile_name": "",
            "affiliation": "",
            "profile_url": "",
            "author_id": "",
            "candidate_count": 0,
            "candidates": [],
            "citations_all": 0,
            "citations_recent": 0,
            "h_index_all": 0,
            "h_index_recent": 0,
            "i10_index_all": 0,
            "i10_index_recent": 0,
            "interests": []
        }

        try:
            candidates = client.discover_candidates(name, dept, institution, use_mock=use_mock)
            base_res["candidates"] = candidates
            base_res["candidate_count"] = len(candidates)

            if not candidates:
                base_res["match_status"] = "No profile found"
            else:
                top_cand = candidates[0]
                aid = top_cand.get("author_id", "")
                metrics = client.get_metrics(aid, use_mock=use_mock) if aid else {}

                base_res.update({
                    "match_status": "Needs verification",
                    "profile_name": top_cand.get("name", ""),
                    "affiliation": top_cand.get("affiliations", ""),
                    "profile_url": top_cand.get("profile_url", ""),
                    "author_id": aid,
                    **metrics
                })
        except Exception as exc:
            base_res["match_status"] = f"Error: {str(exc)[:50]}"

        results.append(base_res)
        # Small breath to allow event loop responsiveness
        await asyncio.sleep(0.05)

    dashboard_state["records"] = results
    dashboard_state["is_running"] = False
    dashboard_state["progress"] = 100.0
    dashboard_state["current_status"] = "Discovery completed successfully!"

    return {
        "status": "success",
        "total": len(results),
        "records": results,
        "analytics": get_analytics_payload(results),
        "account": client.get_account_info(use_mock=use_mock)
    }


def get_analytics_payload(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    kpis = compute_kpis(records)
    departments = compute_department_breakdown(records)
    leaderboard = compute_leaderboard(records, top_n=8)
    distribution = compute_distribution(records)
    return {
        "kpis": kpis,
        "departments": departments,
        "leaderboard": leaderboard,
        "distribution": distribution
    }


@app.get("/api/analytics")
async def get_analytics():
    records = dashboard_state.get("records", [])
    return get_analytics_payload(records)


@app.post("/api/verify")
async def verify_profile(payload: VerifyPayload):
    """Update verification status or swap selected candidate profile."""
    records = dashboard_state.get("records", [])
    matched_idx = next((i for i, r in enumerate(records) if r["id"] == payload.staff_id), None)
    if matched_idx is None:
        raise HTTPException(status_code=404, detail="Staff ID not found in current session.")

    record = records[matched_idx]
    active_key = get_serpapi_key()
    client = ScholarClient(api_key=active_key, enable_cache=True)

    if payload.author_id:
        # Re-fetch or assign metrics for chosen candidate
        metrics = client.get_metrics(payload.author_id, use_mock=payload.use_mock or not active_key)
        record["author_id"] = payload.author_id
        record["profile_name"] = payload.profile_name or record.get("profile_name", "")
        record["affiliation"] = payload.affiliation or record.get("affiliation", "")
        record["profile_url"] = f"https://scholar.google.com/citations?user={payload.author_id}"
        record.update(metrics)

    record["match_status"] = payload.status
    records[matched_idx] = record
    dashboard_state["records"] = records

    return {
        "status": "updated",
        "record": record,
        "analytics": get_analytics_payload(records)
    }


@app.get("/api/export/csv")
async def export_csv():
    records = dashboard_state.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No active records to export.")
    csv_bytes = export_to_csv(records)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="scholar_analytics_report.csv"'}
    )


@app.get("/api/export/excel")
async def export_excel():
    records = dashboard_state.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No active records to export.")
    analytics = get_analytics_payload(records)
    excel_bytes = export_to_excel(records, analytics["kpis"], analytics["departments"])
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="scholar_analytics_report.xlsx"'}
    )


# Serve static web dashboard files
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
