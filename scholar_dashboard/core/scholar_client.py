"""Google Scholar API client via SerpApi with local caching and mock fallback."""
import json
import os
from pathlib import Path
import random
import time
from typing import Any, Dict, List, Optional
import requests

SERPAPI_URL = "https://serpapi.com/search.json"
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "cache.json"


class ScholarClient:
    def __init__(self, api_key: str = "", enable_cache: bool = True):
        self.api_key = api_key.strip()
        self.enable_cache = enable_cache
        self.cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if self.enable_cache and CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        if not self.enable_cache:
            return
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send authenticated request to SerpApi with retry mechanism."""
        if not self.api_key:
            raise ValueError("SerpApi key is required. Please set your key in Configuration.")

        cache_key = json.dumps(params, sort_keys=True)
        if self.enable_cache and cache_key in self.cache:
            return self.cache[cache_key]

        req_params = dict(params)
        req_params["api_key"] = self.api_key

        last_error = None
        for attempt in range(3):
            try:
                resp = requests.get(SERPAPI_URL, params=req_params, timeout=35)
                resp.raise_for_status()
                data = resp.json()
                if data.get("error"):
                    raise RuntimeError(data["error"])

                if self.enable_cache:
                    self.cache[cache_key] = data
                    self._save_cache()
                return data
            except requests.RequestException as e:
                last_error = e
                time.sleep(1.0 * (attempt + 1))

        raise RuntimeError(f"SerpApi request failed after 3 attempts: {last_error}")

    def discover_candidates(
        self,
        name: str,
        department: str = "",
        institution: str = "",
        use_mock: bool = False
    ) -> List[Dict[str, Any]]:
        """Search Google Scholar for author profiles matching name and affiliations."""
        if use_mock or not self.api_key:
            return self._generate_mock_candidates(name, department, institution)

        query_parts = [str(name).strip()]
        if department and str(department).strip():
            query_parts.append(str(department).strip())
        if institution and str(institution).strip():
            query_parts.append(str(institution).strip())

        query = " ".join(query_parts)
        data = self._request({"engine": "google_scholar", "q": query})

        candidates_raw = []
        profiles_data = data.get("profiles", {})
        if isinstance(profiles_data, dict):
            candidates_raw = profiles_data.get("authors", [])
        elif isinstance(profiles_data, list):
            candidates_raw = profiles_data

        if not candidates_raw:
            for item in data.get("organic_results", []):
                for author in item.get("publication_info", {}).get("authors", []):
                    if author.get("author_id"):
                        candidates_raw.append({
                            "name": author.get("name", ""),
                            "author_id": author.get("author_id", ""),
                            "link": author.get("link", ""),
                            "affiliations": "",
                            "email": "",
                        })

        cleaned: List[Dict[str, Any]] = []
        seen_ids = set()
        for p in candidates_raw[:6]:
            aid = p.get("author_id", "")
            if aid and aid in seen_ids:
                continue
            if aid:
                seen_ids.add(aid)
            cleaned.append({
                "author_id": aid,
                "name": p.get("name", ""),
                "affiliations": p.get("affiliations", ""),
                "email": p.get("email", ""),
                "profile_url": p.get("link", "") or (f"https://scholar.google.com/citations?user={aid}" if aid else ""),
                "thumbnail": p.get("thumbnail", "")
            })
        return cleaned

    def get_metrics(self, author_id: str, use_mock: bool = False) -> Dict[str, Any]:
        """Fetch citations, h-index, and i10-index for an author."""
        if not author_id:
            return {
                "citations_all": 0, "citations_recent": 0,
                "h_index_all": 0, "h_index_recent": 0,
                "i10_index_all": 0, "i10_index_recent": 0,
                "interests": []
            }

        if use_mock or not self.api_key:
            return self._generate_mock_metrics(author_id)

        data = self._request({
            "engine": "google_scholar_author",
            "author_id": author_id,
            "hl": "en"
        })

        table = (data.get("cited_by") or {}).get("table", [])
        result = {
            "citations_all": 0, "citations_recent": 0,
            "h_index_all": 0, "h_index_recent": 0,
            "i10_index_all": 0, "i10_index_recent": 0,
            "interests": [item.get("title", "") for item in data.get("interests", []) if isinstance(item, dict)]
        }

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
                    result[all_key] = int(sub.get("all") or 0)
                    for k, v in sub.items():
                        if k.startswith("since"):
                            result[recent_key] = int(v or 0)
                            break
        return result

    def _generate_mock_candidates(self, name: str, department: str, institution: str) -> List[Dict[str, Any]]:
        """Generate realistic synthetic candidates for demo and testing without API costs."""
        # Deterministic seed based on name
        seed = sum(ord(c) for c in name)
        rng = random.Random(seed)

        # 88% chance of finding profiles
        if rng.random() < 0.12:
            return []

        count = 1 if rng.random() > 0.4 else (2 if rng.random() > 0.3 else 3)
        candidates = []
        affil_base = f"{department or 'Department of Science'}, {institution or 'University'}"

        for i in range(count):
            aid = f"mock_{seed}_{i+1}"
            cand_name = name if i == 0 else f"{name} ({['Jr.', 'Ph.D', 'Univ'][i-1]})"
            affil = affil_base if i == 0 else f"{department or 'Faculty of Science'}, Regional Institute"
            candidates.append({
                "author_id": aid,
                "name": cand_name,
                "affiliations": affil,
                "email": f"verified at {institution.lower().replace(' ', '') or 'edu'}.org",
                "profile_url": f"https://scholar.google.com/citations?user={aid}",
                "thumbnail": ""
            })
        return candidates

    def _generate_mock_metrics(self, author_id: str) -> Dict[str, Any]:
        """Generate realistic citation metrics for mock author IDs."""
        seed = sum(ord(c) for c in author_id)
        rng = random.Random(seed)

        citations_all = rng.randint(45, 6200)
        recent_ratio = rng.uniform(0.35, 0.75)
        citations_recent = int(citations_all * recent_ratio)

        h_index_all = max(1, int((citations_all ** 0.45) * rng.uniform(0.7, 1.3)))
        h_index_recent = max(1, int(h_index_all * rng.uniform(0.5, 0.9)))

        i10_index_all = max(0, int(h_index_all * rng.uniform(0.8, 1.8)))
        i10_index_recent = max(0, int(i10_index_all * rng.uniform(0.4, 0.85)))

        sample_topics = [
            "Analytical Chemistry", "Machine Learning", "Organic Synthesis", 
            "Material Science", "Renewable Energy", "Computational Biology",
            "Data Science", "Public Health", "Environmental Science"
        ]
        topics = rng.sample(sample_topics, k=min(3, len(sample_topics)))

        return {
            "citations_all": citations_all,
            "citations_recent": citations_recent,
            "h_index_all": h_index_all,
            "h_index_recent": h_index_recent,
            "i10_index_all": i10_index_all,
            "i10_index_recent": i10_index_recent,
            "interests": topics
        }
