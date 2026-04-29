"""
RapidAPI integrations for SwarmBharat.

This module is intentionally defensive because RapidAPI providers often change
host names, paths, and response formats. Every wrapper supports env overrides
so you can align quickly with the exact endpoint shown in your RapidAPI dashboard.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

load_dotenv()


class RapidAPIError(Exception):
    """Raised when RapidAPI request configuration or response is invalid."""


class RapidAPIClient:
    """Small async RapidAPI client with host/path override support."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 20.0):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY", "").strip()
        self.timeout = timeout
        if not self.api_key:
            raise RapidAPIError("RAPIDAPI_KEY is missing in .env")

    async def request(
        self,
        *,
        host: str,
        path: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"https://{host}{path if path.startswith('/') else '/' + path}"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": host,
        }
        if extra_headers:
            headers.update(extra_headers)

        response = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=self.timeout + (attempt * 8)) as client:
                    response = await client.request(
                        method.upper(),
                        url,
                        params=params,
                        json=json_body,
                        data=data,
                        headers=headers,
                    )
                break
            except httpx.TimeoutException as exc:
                if attempt == 1:
                    raise RapidAPIError(f"RapidAPI request timed out for {host}{path}") from exc
                continue
        if response is None:
            raise RapidAPIError(f"RapidAPI request failed before receiving a response for {host}{path}")

        # Return richer error context for quick endpoint fixing.
        if response.status_code >= 400:
            body_preview = response.text[:300]
            raise RapidAPIError(
                f"RapidAPI call failed ({response.status_code}) for {host}{path}. "
                f"Response: {body_preview}"
            )

        # Most RapidAPI providers return JSON. Keep fallback when not JSON.
        ctype = (response.headers.get("content-type") or "").lower()
        if "application/json" in ctype:
            return response.json()

        return {
            "raw_text": response.text,
            "status_code": response.status_code,
            "content_type": ctype,
        }


async def _request_with_fallbacks(
    client: RapidAPIClient,
    *,
    candidates: List[Tuple[str, str]],
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    errors: List[str] = []
    for host, path in candidates:
        try:
            return await client.request(
                host=host,
                path=path,
                method=method,
                params=params,
                json_body=json_body,
                data=data,
                extra_headers=extra_headers,
            )
        except RapidAPIError as exc:
            errors.append(str(exc))
            continue

    error_summary = " | ".join(errors[-3:]) if errors else "No candidates were provided"
    raise RapidAPIError(f"All candidate endpoints failed. {error_summary}")


def _cfg(name: str, default_host: str, default_path: str) -> Tuple[str, str]:
    upper = name.upper()
    host = os.getenv(f"RAPIDAPI_{upper}_HOST", default_host).strip()
    path = os.getenv(f"RAPIDAPI_{upper}_PATH", default_path).strip()
    if not path.startswith("/"):
        path = f"/{path}"
    return host, path


def _first(data: Any, keys: List[str], default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def _as_list(data: Any, keys: List[str]) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


# ---------------------------------------------------------------------------
# Core wrappers used directly by your existing test snippet
# ---------------------------------------------------------------------------


async def jsearch_jobs(query: str, location: str = "India", page: int = 1) -> Dict[str, Any]:
    """Search jobs via JSearch RapidAPI."""
    client = RapidAPIClient()
    host, path = _cfg("JSEARCH", "jsearch.p.rapidapi.com", "/search")

    payload = await client.request(
        host=host,
        path=path,
        params={
            "query": f"{query} in {location}",
            "page": str(page),
            "num_pages": "1",
            "date_posted": "all",
        },
    )

    raw_jobs = _as_list(payload, ["data", "jobs", "results"])
    jobs: List[Dict[str, Any]] = []
    for j in raw_jobs:
        jobs.append(
            {
                "title": _first(j, ["job_title", "title"], "Unknown role"),
                "company": _first(j, ["employer_name", "company_name", "company"], "Unknown company"),
                "location": _first(j, ["job_city", "job_location", "location"], location),
                "salary_min": _first(j, ["job_min_salary", "salary_min", "min_salary"]),
                "salary_max": _first(j, ["job_max_salary", "salary_max", "max_salary"]),
                "apply_link": _first(j, ["job_apply_link", "apply_link", "url"]),
            }
        )

    return {
        "status": "success",
        "total_found": len(jobs),
        "jobs": jobs,
    }


async def jsearch_salary(job_title: str, location: str = "India") -> Dict[str, Any]:
    """Fetch salary estimates for a role via JSearch salary endpoint."""
    client = RapidAPIClient()
    host, path = _cfg("JSEARCH_SALARY", "jsearch.p.rapidapi.com", "/estimated-salary")

    payload = await client.request(
        host=host,
        path=path,
        params={
            "job_title": job_title,
            "location": location,
            "location_type": "ANY",
            "years_of_experience": "ALL",
        },
    )

    rows = _as_list(payload, ["data", "results"])
    if not rows:
        return {"status": "success", "role": job_title, "location": location, "message": "No salary data returned"}

    top = rows[0]
    return {
        "status": "success",
        "role": job_title,
        "location": location,
        "publisher": _first(top, ["publisher_name", "source", "publisher"]),
        "salary_min": _first(top, ["min_salary", "salary_min"]),
        "salary_max": _first(top, ["max_salary", "salary_max"]),
        "salary_period": _first(top, ["salary_period", "period"]),
    }


async def get_weather(city: str) -> Dict[str, Any]:
    """Get current weather via RapidAPI Open Weather subscription."""
    client = RapidAPIClient()

    host, path_template = _cfg("OPEN_WEATHER", "open-weather13.p.rapidapi.com", "/city")
    path = path_template.replace("{city}", quote(city))

    payload = await _request_with_fallbacks(
        client,
        candidates=[
            (host, path),
            ("open-weather13.p.rapidapi.com", "/city"),
            ("open-weather13.p.rapidapi.com", f"/city/{quote(city)}"),
            ("open-weather13.p.rapidapi.com", f"/city/{quote(city)}/EN"),
        ],
        params={"city": city, "q": city},
    )

    main = payload.get("main", {}) if isinstance(payload, dict) else {}
    weather_arr = payload.get("weather", []) if isinstance(payload, dict) else []
    weather_0 = weather_arr[0] if weather_arr and isinstance(weather_arr[0], dict) else {}

    temp = main.get("temp")
    humidity = main.get("humidity")
    condition = weather_0.get("main") or weather_0.get("description") or "Unknown"

    advice: List[str] = []
    if isinstance(temp, (int, float)):
        if temp >= 35:
            advice.append("High heat: irrigate early morning or evening to reduce evaporation.")
        elif temp <= 15:
            advice.append("Low temperature: protect seedlings and avoid overwatering.")
    if isinstance(humidity, (int, float)) and humidity >= 80:
        advice.append("High humidity: monitor crops for fungal disease risk.")
    if not advice:
        advice = ["Weather looks stable. Continue regular field checks."]

    return {
        "status": "success",
        "city": payload.get("name", city) if isinstance(payload, dict) else city,
        "temperature": f"{temp} C" if temp is not None else "N/A",
        "condition": condition,
        "humidity": humidity,
        "farming_advice": advice,
    }


async def amazon_search(query: str, country: str = "IN", page: int = 1) -> Dict[str, Any]:
    """Search products via Real-Time Amazon Data API."""
    client = RapidAPIClient()
    host, path = _cfg("REALTIME_AMAZON", "real-time-amazon-data.p.rapidapi.com", "/search")

    payload = await client.request(
        host=host,
        path=path,
        params={
            "query": query,
            "country": country,
            "page": str(page),
            "sort_by": "RELEVANCE",
            "product_condition": "ALL",
        },
    )

    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    products_raw = _as_list(data, ["products", "items", "results"])

    products = []
    for p in products_raw:
        products.append(
            {
                "name": _first(p, ["product_title", "title", "name"], "Unknown product"),
                "price": _first(p, ["product_price", "price", "offer_price"], "N/A"),
                "rating": _first(p, ["product_star_rating", "rating"]),
                "url": _first(p, ["product_url", "url"]),
            }
        )

    return {
        "status": "success",
        "count": len(products),
        "products": products,
    }


async def search_courses(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search Coursera courses via RapidAPI collection API."""
    client = RapidAPIClient()
    host, path = _cfg(
        "COURSERA",
        "collection-for-coursera-courses.p.rapidapi.com",
        "/rapidapi/course/get_course.php",
    )

    payload = await _request_with_fallbacks(
        client,
        candidates=[
            (host, path),
            ("collection-for-coursera-courses.p.rapidapi.com", "/rapidapi/course/get_course.php"),
            ("collection-for-coursera-courses.p.rapidapi.com", "/rapidapi/course/get_institution.php"),
        ],
        params={"query": query, "q": query, "page_no": "1"},
        extra_headers={"Content-Type": "application/json"},
    )
    rows = _as_list(payload, ["reviews", "courses", "data", "results"])

    courses = []
    if rows:
        query_l = query.strip().lower()
        query_terms = [x for x in query_l.split() if x]
        filtered = rows
        if query_terms:
            def _match(row: Dict[str, Any]) -> bool:
                text = " ".join(
                    [
                        str(_first(row, ["course_name", "name", "title"], "")),
                        str(_first(row, ["course_institution", "partner_name", "provider", "institution"], "")),
                    ]
                ).lower()
                return any(term in text for term in query_terms)
            matched = [r for r in rows if _match(r)]
            if matched:
                filtered = matched

        for c in filtered[:limit]:
            courses.append(
                {
                    "name": _first(c, ["course_name", "name", "title"], "Unknown course"),
                    "provider": _first(c, ["course_institution", "partner_name", "provider", "institution"]),
                    "price": _first(c, ["price", "course_price"], "Free/Unknown"),
                    "url": _first(c, ["url", "course_url"]),
                }
            )
    elif isinstance(payload, list):
        # Institution endpoint returns a list of strings.
        institutions = [str(x) for x in payload if isinstance(x, str)]
        for inst in institutions[:limit]:
            courses.append(
                {
                    "name": f"Top courses from {inst}",
                    "provider": inst,
                    "price": "Unknown",
                    "url": "",
                }
            )

    return {
        "status": "success",
        "total": len(courses),
        "courses": courses,
    }


async def imdb_search(query: str) -> List[Dict[str, Any]]:
    """Search movies/series via IMDb RapidAPI provider."""
    client = RapidAPIClient()
    host, path = _cfg("IMDB", "imdb236.p.rapidapi.com", "/api/imdb/search")

    payload = await _request_with_fallbacks(
        client,
        candidates=[
            (host, path),
            ("imdb236.p.rapidapi.com", "/api/imdb/search"),
            ("imdb236.p.rapidapi.com", "/imdb/search"),
        ],
        params={"originalTitle": query, "query": query},
    )
    rows = _as_list(payload, ["results", "data", "titles"])

    parsed = []
    for item in rows:
        parsed.append(
            {
                "title": _first(item, ["primaryTitle", "title", "name"], "Unknown title"),
                "year": _first(item, ["startYear", "year"]),
                "rating": _first(item, ["averageRating", "rating", "imdbRating"], "N/A"),
                "id": _first(item, ["id", "tconst"]),
            }
        )

    return parsed


async def google_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search the web via RapidAPI Google Search subscription."""
    client = RapidAPIClient()
    host, path = _cfg("GOOGLE_SEARCH", "google-search74.p.rapidapi.com", "/")

    payload = await _request_with_fallbacks(
        client,
        candidates=[
            (host, path),
            ("google-search74.p.rapidapi.com", "/"),
            ("google-search72.p.rapidapi.com", "/"),
            ("google-search72.p.rapidapi.com", "/search"),
        ],
        params={
            "query": query,
            "q": query,
            "limit": str(limit),
            "num": str(limit),
            "lr": "en-IN",
            "gl": "in",
        },
    )

    rows = _as_list(payload, ["items", "results", "data"])
    results = []
    for r in rows:
        results.append(
            {
                "title": _first(r, ["title"]),
                "link": _first(r, ["link", "url"]),
                "snippet": _first(r, ["snippet", "description"]),
            }
        )

    return {
        "status": "success",
        "total": len(results),
        "results": results,
    }


async def deep_translate(text: str, source: str = "auto", target: str = "te") -> str:
    """Translate text via Deep Translate RapidAPI."""
    client = RapidAPIClient()
    host, path = _cfg("DEEP_TRANSLATE", "deep-translate1.p.rapidapi.com", "/language/translate/v2")

    payload = await client.request(
        host=host,
        path=path,
        method="POST",
        json_body={
            "q": text,
            "source": source,
            "target": target,
        },
        extra_headers={"Content-Type": "application/json"},
    )

    # Common deep-translate response shape.
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    translations = data.get("translations", {}) if isinstance(data, dict) else {}
    translated = translations.get("translatedText") if isinstance(translations, dict) else None

    if not translated and isinstance(payload, dict):
        translated = payload.get("translatedText")
    return translated or ""


async def translate_to_telugu(text: str) -> str:
    return await deep_translate(text, source="auto", target="te")


async def check_phone_number(phone_number: str, country_code: str = "IN") -> Dict[str, Any]:
    """Validate/lookup phone via Truecaller Data API (fallback friendly)."""
    client = RapidAPIClient()
    host, path_template = _cfg("TRUECALLER", "truecaller-data2.p.rapidapi.com", "/search/{phone}")

    digits = "".join(ch for ch in str(phone_number) if ch.isdigit())
    if not digits:
        raise RapidAPIError("Phone number is empty or invalid")

    country_digits = "".join(ch for ch in str(country_code) if ch.isdigit())
    if not country_digits and str(country_code).upper() == "IN":
        country_digits = "91"
    phone_with_country = digits
    if country_digits and not digits.startswith(country_digits) and len(digits) <= 10:
        phone_with_country = f"{country_digits}{digits}"

    configured_path = path_template.replace("{phone}", phone_with_country)

    payload = await _request_with_fallbacks(
        client,
        candidates=[
            (host, configured_path),
            ("truecaller-data2.p.rapidapi.com", f"/search/{phone_with_country}"),
            ("truecaller-data2.p.rapidapi.com", f"/search/{digits}"),
            ("truecaller-data.p.rapidapi.com", f"/search/{phone_with_country}"),
            ("truecaller4.p.rapidapi.com", f"/search/{phone_with_country}"),
        ],
        params={
            "phone": phone_with_country,
            "number": phone_with_country,
            "countryCode": country_code,
            "country_code": country_code,
        },
        extra_headers={"Content-Type": "application/json"},
    )

    # Keep parser lenient because provider schemas vary heavily.
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    if isinstance(data, dict) and "basicInfo" in data:
        basic_info = data.get("basicInfo", {}) if isinstance(data.get("basicInfo"), dict) else {}
        phone_info = data.get("phoneInfo", {}) if isinstance(data.get("phoneInfo"), dict) else {}
        name_info = basic_info.get("name", {}) if isinstance(basic_info.get("name"), dict) else {}
        spam_type = phone_info.get("spamType") or ""
        is_valid = spam_type != "INVALID"
        name = (
            name_info.get("fullName")
            or basic_info.get("jobTitle")
            or _first(data, ["name", "fullName", "display_name"], "Unknown")
        )
        carrier = phone_info.get("carrier") or _first(data, ["carrier", "operator"], "Unknown")
        warning = "Number looks valid"
        if spam_type:
            warning = f"Number classification: {spam_type}"
        return {
            "status": "success",
            "phone": phone_with_country,
            "valid": is_valid,
            "name": name or "Unknown",
            "carrier": carrier,
            "warning": warning,
        }

    is_valid = bool(_first(data, ["valid", "is_valid", "success"], True))
    name = _first(data, ["name", "fullName", "display_name"], "Unknown")
    carrier = _first(data, ["carrier", "operator"], "Unknown")

    return {
        "status": "success",
        "phone": phone_with_country,
        "valid": is_valid,
        "name": name,
        "carrier": carrier,
        "warning": "Number looks valid" if is_valid else "Number may be invalid or unavailable",
    }


# ---------------------------------------------------------------------------
# Optional wrappers for additional subscriptions from your RapidAPI dashboard
# ---------------------------------------------------------------------------


async def geodb_cities(prefix: str, country_ids: str = "IN", limit: int = 10) -> Dict[str, Any]:
    client = RapidAPIClient()
    host, path = _cfg("GEODB", "wft-geo-db.p.rapidapi.com", "/v1/geo/cities")
    payload = await client.request(
        host=host,
        path=path,
        params={
            "namePrefix": prefix,
            "countryIds": country_ids,
            "limit": str(limit),
            "sort": "-population",
        },
    )
    rows = _as_list(payload, ["data", "results"])
    return {"status": "success", "count": len(rows), "cities": rows}


async def youtube_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    client = RapidAPIClient()
    host, path = _cfg("YOUTUBE", "youtube-v31.p.rapidapi.com", "/search")
    payload = await client.request(
        host=host,
        path=path,
        params={"q": query, "part": "snippet", "maxResults": str(max_results)},
    )
    rows = _as_list(payload, ["items", "data", "results"])
    return {"status": "success", "count": len(rows), "videos": rows}


async def linkedin_job_search(query: str, location: str = "India", page: int = 1) -> Dict[str, Any]:
    client = RapidAPIClient()
    host, path = _cfg("LINKEDIN_JOBS", "linkedin-job-search-api.p.rapidapi.com", "/active-jb-24h")
    payload = await client.request(
        host=host,
        path=path,
        params={"query": query, "location": location, "page": str(page)},
    )
    rows = _as_list(payload, ["data", "jobs", "results"])
    return {"status": "success", "count": len(rows), "jobs": rows}


async def naukri_market_intelligence(query: str, location: str = "India") -> Dict[str, Any]:
    client = RapidAPIClient()
    host, path = _cfg(
        "NAUKRI_MARKET",
        "naukri-job-market-intelligence-api.p.rapidapi.com",
        "/search",
    )
    payload = await client.request(host=host, path=path, params={"query": query, "location": location})
    rows = _as_list(payload, ["data", "results", "jobs"])
    return {"status": "success", "count": len(rows), "results": rows}


async def rapidapi_healthcheck() -> Dict[str, Any]:
    """Quick local check for key presence and basic config."""
    key_present = bool(os.getenv("RAPIDAPI_KEY", "").strip())
    return {
        "rapidapi_key_configured": key_present,
        "message": "RAPIDAPI_KEY loaded" if key_present else "Missing RAPIDAPI_KEY in .env",
    }
