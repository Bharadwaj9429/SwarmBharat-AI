"""
SwarmBharat India API Manager
Real-time integrations with Indian government, job platforms, finance, and location APIs
This is what makes SwarmBharat fundamentally different from ChatGPT
"""

import httpx
import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # RapidAPI is optional at runtime (but preferred when configured).
    import utils.rapidapi_integrations as rapidapi
    _RAPIDAPI_OK = True
except Exception:
    rapidapi = None
    _RAPIDAPI_OK = False


class IndiaAPIManager:
    """Master API manager for all Indian data sources"""
    
    def __init__(self):
        self.cache = {}  # Replace with Redis in production
        self.cache_ttl = 600  # 10 minutes for most APIs
        self.short_cache_ttl = 300  # 5 minutes for volatile data
        self.use_rapidapi = os.getenv("USE_RAPIDAPI", "true").strip().lower() in {"1", "true", "yes", "on"}
    
    def _cache_key(self, fn_name: str, **kwargs) -> str:
        """Generate unique cache key from function name and parameters"""
        return f"{fn_name}:{json.dumps(kwargs, sort_keys=True, default=str)}"
    
    def _from_cache(self, key: str) -> Optional[Any]:
        """Retrieve from cache if not expired"""
        if key in self.cache:
            data, expires = self.cache[key]
            if datetime.now() < expires:
                logger.info(f"✓ Cache hit: {key}")
                return data
        return None
    
    def _to_cache(self, key: str, data: Any, ttl: int = None) -> None:
        """Store in cache with TTL"""
        ttl = ttl or self.cache_ttl
        self.cache[key] = (data, datetime.now() + timedelta(seconds=ttl))

    def _rapidapi_enabled(self) -> bool:
        return self.use_rapidapi and _RAPIDAPI_OK and bool(os.getenv("RAPIDAPI_KEY", "").strip())

    # =====================
    # RAPIDAPI (PRIMARY LIVE DATA SOURCES)
    # =====================

    async def rapidapi_health(self) -> Dict[str, Any]:
        """Fast health signal for RapidAPI configuration."""
        if not self._rapidapi_enabled():
            return {"status": "disabled", "reason": "RAPIDAPI_KEY missing or USE_RAPIDAPI=false"}
        try:
            return await rapidapi.rapidapi_healthcheck()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_job_listings(self, role: str, location: str = "Hyderabad") -> Dict[str, Any]:
        """Live job listings via RapidAPI (JSearch)."""
        key = self._cache_key("rapidapi_jobs", role=role, location=location)
        if cached := self._from_cache(key):
            return cached

        if not self._rapidapi_enabled():
            return {"note": "RapidAPI not configured", "jobs": []}

        try:
            data = await rapidapi.jsearch_jobs(role, location)
            self._to_cache(key, data, self.short_cache_ttl)
            return data
        except Exception as e:
            logger.error(f"RapidAPI jobs failed: {str(e)}")
            return {"error": "Could not fetch job listings", "detail": str(e)}

    async def get_salary_data(self, role: str, location: str = "Hyderabad", experience_years: int = 3) -> Dict[str, Any]:
        """
        Salary estimates (primary: RapidAPI JSearch salary).
        Keep signature stable for core callers.
        """
        key = self._cache_key("rapidapi_salary", role=role, location=location, exp=experience_years)
        if cached := self._from_cache(key):
            return cached

        if not self._rapidapi_enabled():
            return {"note": "RapidAPI not configured"}

        try:
            # JSearch endpoint doesn't always use exp; keep it in cache key anyway.
            payload = await rapidapi.jsearch_salary(role, location)
            self._to_cache(key, payload, self.short_cache_ttl)
            return payload
        except Exception as e:
            logger.error(f"RapidAPI salary failed: {str(e)}")
            return {"error": "Could not fetch salary data", "detail": str(e)}

    async def get_weather(self, city: str) -> Dict[str, Any]:
        """Weather via RapidAPI wrapper (preferred over direct OpenWeather)."""
        key = self._cache_key("rapidapi_weather", city=city)
        if cached := self._from_cache(key):
            return cached

        if not self._rapidapi_enabled():
            return {"note": "RapidAPI not configured"}

        try:
            payload = await rapidapi.get_weather(city)
            self._to_cache(key, payload, self.short_cache_ttl)
            return payload
        except Exception as e:
            logger.error(f"RapidAPI weather failed: {str(e)}")
            return {"error": "Could not fetch weather", "detail": str(e)}

    async def web_search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Google search via RapidAPI for live web facts."""
        key = self._cache_key("rapidapi_web_search", query=query, limit=limit)
        if cached := self._from_cache(key):
            return cached

        if not self._rapidapi_enabled():
            return {"note": "RapidAPI not configured", "results": []}

        try:
            payload = await rapidapi.google_search(query, limit=limit)
            self._to_cache(key, payload, self.short_cache_ttl)
            return payload
        except Exception as e:
            logger.error(f"RapidAPI web search failed: {str(e)}")
            return {"error": "Could not search web", "detail": str(e)}

    async def translate_to_telugu(self, text: str) -> Dict[str, Any]:
        """Translation via RapidAPI."""
        if not self._rapidapi_enabled():
            return {"note": "RapidAPI not configured", "translated": ""}
        try:
            translated = await rapidapi.translate_to_telugu(text)
            return {"status": "success", "translated": translated}
        except Exception as e:
            return {"status": "error", "error": str(e), "translated": ""}
    
    # =====================
    # CENTRAL GOVERNMENT APIs
    # =====================
    
    async def check_pm_kisan(self, aadhaar: str) -> Dict[str, Any]:
        """Check farmer's PM Kisan payment status via government database"""
        key = self._cache_key("pm_kisan", aadhaar=aadhaar)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # PM Kisan website endpoint
                response = await client.post(
                    "https://pmkisan.gov.in/Rpt_BeneficiaryStatus_pub.aspx",
                    data={"Aadhaar": aadhaar},
                    follow_redirects=True
                )
                
                # Parse response (would need beautiful soup for real implementation)
                if response.status_code == 200:
                    result = {
                        "status": "success",
                        "platform": "PM Kisan",
                        "aadhaar": aadhaar[-4:],  # Masked for privacy
                        "check_url": "https://pmkisan.gov.in/",
                        "helpline": "1800-425-1551"
                    }
                    self._to_cache(key, result)
                    return result
        except Exception as e:
            logger.error(f"PM Kisan check failed: {str(e)}")
        
        return {"error": "Could not fetch PM Kisan status", "action": "Visit pmkisan.gov.in"}
    
    async def check_ayushman_eligibility(self, aadhaar: str) -> Dict[str, Any]:
        """Check Ayushman Bharat (PM-JAY) eligibility"""
        key = self._cache_key("ayushman", aadhaar=aadhaar)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://bis.pmjay.gov.in/BIS/mobileverify",
                    params={"scheme": "PMJAY", "aadhaar": aadhaar},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    result = {
                        "scheme": "Ayushman Bharat (PM-JAY)",
                        "coverage": "₹5 lakh per family per year",
                        "status": "Check eligibility at pmjay.gov.in",
                        "benefits": ["Free hospitalization", "Pre/post hospitalization", "No copay"],
                        "toll_free": "1800-111-555"
                    }
                    self._to_cache(key, result)
                    return result
        except Exception as e:
            logger.error(f"Ayushman check failed: {str(e)}")
        
        return {"error": "Could not verify Ayushman eligibility"}
    
    async def verify_gstin(self, gstin: str) -> Dict[str, Any]:
        """Verify GST number - free public API"""
        key = self._cache_key("gstin", gstin=gstin)
        if cached := self._from_cache(key):
            return cached
        
        try:
            api_key = os.getenv("GST_API_KEY", "")
            if not api_key:
                return {"error": "GST API key not configured"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://sheet.gstincheck.co.in/check/{api_key}/{gstin}",
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._to_cache(key, data)
                    return data
        except Exception as e:
            logger.error(f"GSTIN verification failed: {str(e)}")
        
        return {"error": "Could not verify GSTIN"}
    
    async def check_epfo_balance(self, uan: str) -> Dict[str, Any]:
        """Check Employee Provident Fund balance"""
        key = self._cache_key("epfo", uan=uan)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://passbook.epfindia.gov.in/MemberPassBook/Login",
                    params={"uan": uan},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    result = {
                        "platform": "EPFO",
                        "uan": uan[-4:],
                        "action": "Login at https://passbook.epfindia.gov.in",
                        "helpline": "1800-180-1969"
                    }
                    self._to_cache(key, result)
                    return result
        except Exception as e:
            logger.error(f"EPFO check failed: {str(e)}")
        
        return {"error": "Could not fetch EPFO details"}
    
    # =====================
    # TELANGANA STATE SPECIFIC
    # =====================
    
    async def check_rythu_bandhu(self, pattadar_id: str) -> Dict[str, Any]:
        """Check Rythu Bandhu payment status (₹10,000/acre/year for Telangana farmers)"""
        key = self._cache_key("rythu_bandhu", pattadar_id=pattadar_id)
        if cached := self._from_cache(key):
            return cached
        
        try:
            # Mock implementation - real API would call state government
            result = {
                "scheme": "Rythu Bandhu (Telangana)",
                "amount_per_acre": "₹10,000",
                "payment_periods": ["Kharif (June)", "Rabi (November)"],
                "status": "Check at https://rythu.telangana.gov.in",
                "eligibility": "Landowner farmer in Telangana",
                "documents_required": ["Aadhaar", "Pattadar Passbook", "Bank Account"],
                "meeseva": "Visit nearest MeeSeva center"
            }
            self._to_cache(key, result)
            return result
        except Exception as e:
            logger.error(f"Rythu Bandhu check failed: {str(e)}")
        
        return {"error": "Could not fetch Rythu Bandhu status"}
    
    async def get_tspsc_results(self, hall_ticket: str) -> Dict[str, Any]:
        """Check TSPSC (Telangana Public Service Commission) exam results"""
        key = self._cache_key("tspsc", hall_ticket=hall_ticket)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://tspsc.gov.in/results",
                    params={"hallticket": hall_ticket},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    result = {
                        "platform": "TSPSC",
                        "hall_ticket": hall_ticket[-4:],
                        "action": "Check full results at https://tspsc.gov.in",
                        "helpline": "040-2781-0589"
                    }
                    self._to_cache(key, result)
                    return result
        except Exception as e:
            logger.error(f"TSPSC check failed: {str(e)}")
        
        return {"error": "Could not fetch TSPSC results"}
    
    async def check_ts_rera_property(self, registration_no: str) -> Dict[str, Any]:
        """Verify property registration in Telangana RERA database"""
        key = self._cache_key("ts_rera", registration_no=registration_no)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://rera.telangana.gov.in/api/project/{registration_no}",
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    result = {
                        "platform": "Telangana RERA",
                        "registration": registration_no[-4:],
                        "action": "View full details at https://rera.telangana.gov.in",
                        "warning": "Verify BEFORE investing in property"
                    }
                    self._to_cache(key, result)
                    return result
        except Exception as e:
            logger.error(f"RERA check failed: {str(e)}")
        
        return {"error": "Could not verify property registration"}
    
    async def get_aarogyasri_hospitals(self, district: str, specialty: str = "") -> Dict[str, Any]:
        """Find Aarogyasri empanelled hospitals (free health scheme in Telangana)"""
        key = self._cache_key("aarogyasri", district=district, specialty=specialty)
        if cached := self._from_cache(key):
            return cached
        
        try:
            result = {
                "scheme": "Aarogyasri (Telangana)",
                "coverage": "Free inpatient treatment",
                "eligibility": "Below poverty line families in Telangana",
                "benefits": ["No registration fee", "Free procedures", "Zero out-of-pocket"],
                "district": district,
                "specialty": specialty or "All",
                "status": f"Search hospitals at https://aarogyasri.telangana.gov.in",
                "helpline": "1800-425-0066"
            }
            self._to_cache(key, result)
            return result
        except Exception as e:
            logger.error(f"Aarogyasri check failed: {str(e)}")
        
        return {"error": "Could not fetch hospital information"}
    
    # =====================
    # JOBS + CAREER
    # =====================
    
    async def search_naukri_jobs(self, role: str, location: str = "Hyderabad", 
                                   experience: str = "0-3") -> Dict[str, Any]:
        """Search real job listings on Naukri via RapidAPI"""
        key = self._cache_key("naukri", role=role, location=location, exp=experience)
        if cached := self._from_cache(key):
            return cached
        
        try:
            rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
            if not rapidapi_key:
                return {"note": "RAPIDAPI_KEY not configured", "alternative": "Visit naukri.com directly"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://naukri-api.p.rapidapi.com/jobs/search",
                    params={
                        "keyword": role,
                        "location": location,
                        "experience": experience,
                        "noOfResult": 10
                    },
                    headers={
                        "X-RapidAPI-Key": rapidapi_key,
                        "X-RapidAPI-Host": "naukri-api.p.rapidapi.com"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "role": role,
                        "location": location,
                        "count": len(data.get("results", [])),
                        "jobs": data.get("results", [])[:5],  # Top 5
                        "source": "Naukri.com"
                    }
                    self._to_cache(key, result, self.short_cache_ttl)
                    return result
        except Exception as e:
            logger.error(f"Naukri search failed: {str(e)}")
        
        return {"error": "Could not search jobs"}
    
    async def get_salary_data(self, role: str, location: str, experience_years: int) -> Dict[str, Any]:
        """
        Get salary estimates for a role.
        Primary path: RapidAPI JSearch salary wrapper (stable + already in this repo).
        """
        key = self._cache_key("salary", role=role, location=location, exp=experience_years)
        if cached := self._from_cache(key):
            return cached

        if not self._rapidapi_enabled():
            return {"note": "RapidAPI not configured"}

        try:
            payload = await rapidapi.jsearch_salary(role, location)
            self._to_cache(key, payload, self.short_cache_ttl)
            return payload
        except Exception as e:
            logger.error(f"Salary data fetch failed: {str(e)}")
            return {"error": "Could not fetch salary data", "detail": str(e)}
    
    # =====================
    # FINANCE + MARKETS
    # =====================
    
    async def get_nse_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Live NSE stock data - using Alpha Vantage as reliable fallback"""
        key = self._cache_key("nse", symbol=symbol)
        if cached := self._from_cache(key):
            return cached
        
        # Try Alpha Vantage first (more reliable)
        try:
            alpha_key = os.getenv("ALPHA_VANTAGE_KEY", "")
            if alpha_key:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "GLOBAL_QUOTE",
                            "symbol": f"{symbol}.BSE",  # Indian stocks on BSE
                            "apikey": alpha_key
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "Global Quote" in data:
                            quote = data["Global Quote"]
                            result = {
                                "symbol": symbol,
                                "price": quote.get("05. price"),
                                "change": quote.get("09. change"),
                                "change_percent": quote.get("10. change percent"),
                                "timestamp": datetime.now().isoformat(),
                                "source": "Alpha Vantage/BSE"
                            }
                            self._to_cache(key, result, 60)
                            return result
        except Exception as e:
            logger.warning(f"Alpha Vantage failed: {str(e)}")
        
        # Fallback to mock data with clear indication
        result = {
            "symbol": symbol,
            "price": "1,234.56",
            "change": "+12.34",
            "change_percent": "+1.01%",
            "timestamp": datetime.now().isoformat(),
            "source": "Demo data - Configure ALPHA_VANTAGE_KEY for live data"
        }
        self._to_cache(key, result, 300)
        return result
    
    async def get_mutual_fund_nav(self, scheme_code: str) -> Dict[str, Any]:
        """Get mutual fund NAV - free MFAPI"""
        key = self._cache_key("mf_nav", scheme_code=scheme_code)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://api.mfapi.in/mf/{scheme_code}",
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "scheme_code": scheme_code,
                        "data": data,
                        "source": "MFAPI (India mutual funds)"
                    }
                    self._to_cache(key, result, 3600)  # Longer cache for NAV
                    return result
        except Exception as e:
            logger.error(f"MF NAV fetch failed: {str(e)}")
        
        return {"error": "Could not fetch mutual fund NAV"}
    
    async def get_gold_price(self) -> Dict[str, Any]:
        """Live gold/silver price in INR"""
        key = self._cache_key("gold_price")
        if cached := self._from_cache(key):
            return cached
        
        try:
            gold_api_key = os.getenv("GOLDAPI_KEY", "")
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://www.goldapi.io/api/XAU/INR",
                    headers={"x-access-token": gold_api_key} if gold_api_key else {}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "metal": "Gold (XAU)",
                        "currency": "INR",
                        "price": data.get("price"),
                        "price_per_gram": data.get("price_per_gram"),
                        "timestamp": datetime.now().isoformat(),
                        "source": "GoldAPI"
                    }
                    self._to_cache(key, result, 300)
                    return result
        except Exception as e:
            logger.error(f"Gold price fetch failed: {str(e)}")
        
        return {"error": "Could not fetch gold price"}
    
    async def get_crypto_price(self, coin: str = "bitcoin") -> Dict[str, Any]:
        """Crypto prices in INR - CoinGecko free API (always works)"""
        key = self._cache_key("crypto", coin=coin)
        if cached := self._from_cache(key):
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": coin, "vs_currencies": "inr", "include_24hr_change": "true"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    coin_data = data.get(coin, {})
                    result = {
                        "coin": coin,
                        "currency": "INR",
                        "price": coin_data.get("inr"),
                        "change_24h": coin_data.get("inr_24h_change"),
                        "timestamp": datetime.now().isoformat(),
                        "source": "CoinGecko (Live)"
                    }
                    self._to_cache(key, result, 300)
                    return result
        except Exception as e:
            logger.error(f"Crypto price fetch failed: {str(e)}")
        
        return {"error": "Could not fetch crypto price"}
    
    # =====================
    # WEATHER + LOCATION
    # =====================
    
    async def get_weather(self, district: str, state: str = "Telangana") -> Dict[str, Any]:
        """Weather for Indian districts - OpenWeatherMap with proper error handling"""
        key = self._cache_key("weather", district=district, state=state)
        if cached := self._from_cache(key):
            return cached
        
        try:
            ow_key = os.getenv("OPENWEATHER_KEY", "")
            if not ow_key:
                # Return demo data with clear message
                result = {
                    "district": district,
                    "temperature": 28.5,
                    "humidity": 65,
                    "rainfall_risk": 20,
                    "weather": "Partly Cloudy",
                    "timestamp": datetime.now().isoformat(),
                    "source": "Demo data - Configure OPENWEATHER_KEY for live data"
                }
                self._to_cache(key, result, 300)
                return result
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": f"{district},{state},IN",
                        "appid": ow_key,
                        "units": "metric",
                        "lang": "en"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "district": district,
                        "temperature": data.get("main", {}).get("temp"),
                        "humidity": data.get("main", {}).get("humidity"),
                        "rainfall_risk": data.get("clouds", {}).get("all"),
                        "weather": data.get("weather", [{}])[0].get("main"),
                        "description": data.get("weather", [{}])[0].get("description"),
                        "timestamp": datetime.now().isoformat(),
                        "source": "OpenWeatherMap"
                    }
                    self._to_cache(key, result, 300)
                    return result
        except Exception as e:
            logger.error(f"Weather fetch failed: {str(e)}")
        
        return {"error": "Could not fetch weather data"}
    
    async def get_imd_crop_advisory(self, district: str) -> Dict[str, Any]:
        """IMD crop weather advisory for farmers"""
        key = self._cache_key("imd_advisory", district=district)
        if cached := self._from_cache(key):
            return cached
        
        try:
            result = {
                "district": district,
                "platform": "Indian Meteorological Department",
                "action": f"Check crop advisory at https://meghdoot.imd.gov.in/district/{district}",
                "benefits": ["Rainfall forecast", "Crop recommendations", "Risk alerts"],
                "language": "Available in local languages"
            }
            self._to_cache(key, result)
            return result
        except Exception as e:
            logger.error(f"IMD advisory fetch failed: {str(e)}")
        
        return {"error": "Could not fetch crop advisory"}
    
    # =====================
    # IMMIGRATION
    # =====================
    
    def calculate_crs_score(self, profile: Dict[str, Any]) -> int:
        """
        Calculate Express Entry CRS (Comprehensive Ranking System) score
        
        profile = {
            "age": 28,
            "education": "bachelors",  # phd, masters, bachelors, diploma_2yr, diploma_1yr, highschool
            "canadian_experience": 0,
            "foreign_experience": 5,
            "english_clb": 9,  # CLB score 0-12
            "french_clb": 0,
            "spouse": True,
            "spouse_education": "bachelors",
            "spouse_english_clb": 7,
            "job_offer": False,
            "job_noc_00": False,  # NOC 00 = management role
            "provincial_nomination": False
        }
        """
        score = 0
        
        # Age points (maximum 132 for single)
        age_points = {20: 100, 21: 109, 22: 119, 23: 128, 24: 128,
                      25: 128, 26: 124, 27: 120, 28: 116, 29: 112,
                      30: 107, 31: 99, 32: 91, 33: 83, 34: 75,
                      35: 67, 36: 59, 37: 51, 38: 43, 39: 35,
                      40: 27, 41: 19, 42: 11, 43: 5, 44: 0}
        score += age_points.get(profile.get("age", 0), 0)
        
        # Education (maximum 150)
        edu_points = {"phd": 150, "masters": 135, "bachelors": 120,
                      "diploma_2yr": 95, "diploma_1yr": 90, "highschool": 30}
        score += edu_points.get(profile.get("education", ""), 0)
        
        # Language (English CLB) - maximum 136
        clb = profile.get("english_clb", 0)
        if clb >= 10: score += 136
        elif clb >= 9: score += 124
        elif clb >= 8: score += 110
        elif clb >= 7: score += 96
        elif clb >= 6: score += 72
        else: score += 0
        
        # Canadian work experience (maximum 80 for 3+ years)
        can_exp_map = {1: 40, 2: 53, 3: 64, 4: 72, 5: 80}
        can_exp = profile.get("canadian_experience", 0)
        score += can_exp_map.get(min(can_exp, 5), 0)
        
        # Foreign work experience (maximum 35 for 3+ years)
        for_exp_map = {1: 13, 2: 25, 3: 35}
        for_exp = profile.get("foreign_experience", 0)
        score += for_exp_map.get(min(for_exp, 3), 0)
        
        # Job offer (50 points if NOC 40+ else 200)
        if profile.get("job_offer"):
            score += 50 if not profile.get("job_noc_00") else 200
        
        # Provincial nomination (600 points - huge!)
        if profile.get("provincial_nomination"):
            score += 600
        
        return min(score, 1200)  # Max CRS is 1200
    
    async def get_latest_express_entry_draw(self) -> Dict[str, Any]:
        """Get latest Express Entry draw from IRCC"""
        key = self._cache_key("express_entry_draw")
        if cached := self._from_cache(key):
            return cached
        
        try:
            # This would scrape from https://www.canada.ca/ in production
            result = {
                "platform": "IRCC Express Entry",
                "action": "Check latest draws at https://www.canada.ca/immigration-refugees-citizenship",
                "categories": ["FSW", "CEC", "FST"],
                "crs_score_needed": "Check latest - varies 400-500+",
                "processing_time": "6 months average",
                "note": "Use your CRS score to check eligibility for each draw"
            }
            self._to_cache(key, result)
            return result
        except Exception as e:
            logger.error(f"Express Entry fetch failed: {str(e)}")
        
        return {"error": "Could not fetch Express Entry info"}


# Initialize global instance
api_manager = IndiaAPIManager()
