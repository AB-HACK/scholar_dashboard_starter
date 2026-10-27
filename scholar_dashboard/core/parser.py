"""Staff file ingestion and column detection engine."""
import io
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd


NAME_TERMS = ["name", "staff", "lecturer", "researcher", "faculty", "professor", "author", "full name", "employee"]
DEPT_TERMS = ["department", "dept", "unit", "discipline", "division", "school", "faculty"]


def read_staff_dataframe(file_source: Any, filename: str) -> pd.DataFrame:
    """Read CSV or Excel file content into a sanitized pandas DataFrame."""
    lower_name = filename.lower()
    
    if isinstance(file_source, bytes):
        buffer = io.BytesIO(file_source)
    else:
        buffer = file_source

    if lower_name.endswith(".csv"):
        try:
            df = pd.read_csv(buffer, encoding="utf-8")
        except UnicodeDecodeError:
            if hasattr(buffer, "seek"):
                buffer.seek(0)
            df = pd.read_csv(buffer, encoding="latin-1")
    elif lower_name.endswith(".xlsx"):
        df = pd.read_excel(buffer, engine="openpyxl")
    elif lower_name.endswith(".xls"):
        df = pd.read_excel(buffer, engine="xlrd")
    elif lower_name.endswith(".json"):
        import json
        raw = buffer.getvalue() if hasattr(buffer, "getvalue") else buffer.read()
        content_str = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
        data = json.loads(content_str)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            for k in ["staff", "records", "faculty", "data", "members"]:
                if k in data and isinstance(data[k], list):
                    df = pd.DataFrame(data[k])
                    break
            else:
                df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()
    elif lower_name.endswith(".txt"):
        raw = buffer.getvalue() if hasattr(buffer, "getvalue") else buffer.read()
        content_str = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
        lines = [line.strip() for line in content_str.splitlines() if line.strip()]
        if lines and ("\t" in lines[0] or "," in lines[0]):
            if hasattr(buffer, "seek"):
                buffer.seek(0)
            df = pd.read_csv(buffer, sep=None, engine="python")
        else:
            df = pd.DataFrame({"Name": lines})
    else:
        # Fallback trial
        try:
            df = pd.read_excel(buffer)
        except Exception:
            if hasattr(buffer, "seek"):
                buffer.seek(0)
            df = pd.read_csv(buffer)

    df.columns = [str(c).strip() for c in df.columns]
    # Remove totally empty rows
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def find_column(columns: List[str], terms: List[str]) -> Optional[str]:
    """Find the first column matching any of the candidate terms."""
    for col in columns:
        low = col.lower().strip()
        if any(term in low for term in terms):
            return col
    return None


def detect_columns(columns: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Detect staff name and department columns automatically."""
    name_col = find_column(columns, NAME_TERMS)
    dept_col = find_column(columns, DEPT_TERMS)
    # Ensure they aren't the exact same column if terms overlap
    if name_col and dept_col and name_col.lower() == dept_col.lower():
        dept_col = None
    return name_col, dept_col


def extract_staff_records(df: pd.DataFrame, name_col: str, dept_col: Optional[str] = None) -> List[Dict[str, str]]:
    """Extract clean staff records ready for discovery."""
    records = []
    for idx, row in df.iterrows():
        val = row.get(name_col)
        if pd.isna(val) or not str(val).strip():
            continue
        name_str = str(val).strip()
        dept_str = str(row.get(dept_col, "")).strip() if dept_col and pd.notna(row.get(dept_col)) else ""
        if dept_str.lower() == "nan":
            dept_str = ""
        records.append({
            "id": f"staff_{idx + 1}",
            "name": name_str,
            "department": dept_str,
            "raw_index": idx
        })
    return records


def extract_department_from_affiliation(affiliation: str) -> str:
    """Intelligently infer department from academic affiliation text if available."""
    if not affiliation or not isinstance(affiliation, str):
        return ""
    import re
    # Patterns like "Department of Chemistry", "Dept. of Computer Science", "Faculty of Law"
    m = re.search(r"(?:department|dept\.?)\s+of\s+([^,;.]+)", affiliation, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"faculty\s+of\s+([^,;.]+)", affiliation, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?:professor|prof\.?|dr\.?|lecturer|reader|assoc\.?\s+prof\.?)\s+of\s+([^,;.]+)", affiliation, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Match common direct department/discipline keywords
    KNOWN_DEPTS = [
        "Chemistry", "Computer Science", "Computer Sciences", "Botany", "Microbiology",
        "Medical Microbiology", "Geosciences", "Public Administration", "Marine Sciences",
        "Pharmacology", "Business Administration", "Biochemistry", "Physics", "Economics",
        "Law", "Mathematics", "Zoology", "Engineering", "Civil Engineering", "Philosophy"
    ]
    for d in KNOWN_DEPTS:
        if re.search(r"\b" + re.escape(d) + r"\b", affiliation, re.IGNORECASE):
            return d
    return ""
