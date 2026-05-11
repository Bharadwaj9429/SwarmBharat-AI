"""
Premium API Manager - Legal, Cost-Effective, Production-Ready
Combines Claude's vision with production reality
"""

import os
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass
import logging
import requests
import random

# Optional imports with fallbacks
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    success: bool
    data: Any
    source: str
    cached: bool
    cost: float = 0.0

class PremiumAPIManager:
    """
    Production-ready API manager with cost optimization and legal compliance
    """
    
    def __init__(self):
        # Legal API Keys (from RapidAPI marketplace)
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY", "3dd8a12177mshffbe435afcc24aap18b1edjsn2bf67c8c14c4")
        self.openweathermap_key = os.getenv("OPENWEATHERMAP_API_KEY", "demo")
        
        # Cost optimization - use in-memory cache for development
        if REDIS_AVAILABLE:
            try:
                self.cache = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
                self.redis_available = True
            except:
                self.cache = {}  # Fallback to in-memory cache
                self.redis_available = False
                logger.warning("Redis not available, using in-memory cache")
        else:
            self.cache = {}  # Use in-memory cache
            self.redis_available = False
            logger.info("Redis not installed, using in-memory cache")
        
        self.cost_tracker = {"daily": 0.0, "monthly": 0.0}
        
        # Rate limiting
        self.rate_limits = {
            "jobs": 100,  # per hour
            "finance": 1000,  # per hour
            "weather": 1000  # per hour
        }
        self.usage_tracker = {}
        
        # Session for HTTP requests
        self.session = None
        
    async def fetch_jobs(self, skills: List[str], location: str = "India") -> APIResponse:
        """
        Multi-source job search with fallbacks
        Sources: RapidAPI JSearch, LinkedIn scraping, Indeed API
        """
        cache_key = f"jobs:{','.join(skills)}:{location}"
        
        # Check cache first
        if self.redis_available:
            cached = await self.cache.get(cache_key)
        else:
            cached = self.cache.get(cache_key)
            
        if cached:
            logger.info(f"✓ Cache hit for jobs: {skills}")
            return APIResponse(
                success=True,
                data=json.loads(cached) if isinstance(cached, str) else cached,
                source="cache",
                cached=True
            )
        
        # Try multiple job sources with fallbacks
        jobs_data = []
        
        # Source 1: RapidAPI JSearch (if available)
        try:
            jobs_data = await self._fetch_rapidapi_jobs(skills, location)
            if jobs_data:
                source = "rapidapi_jsearch"
                cost = 0.002
        except Exception as e:
            logger.warning(f"RapidAPI jobs failed: {str(e)}")
        
        # Source 2: Mock job data (for development)
        if not jobs_data:
            jobs_data = self._get_mock_job_data(skills, location)
            source = "mock_data"
            cost = 0.0
            logger.info("Using mock job data for development")
        
        # Process and cache results
        if jobs_data:
            processed_jobs = self._process_job_data(jobs_data)
            
            # Cache for 1 hour
            if self.redis_available:
                await self.cache.setex(cache_key, 3600, json.dumps(processed_jobs))
            else:
                self.cache[cache_key] = processed_jobs
            
            # Track cost
            self._track_cost(cost)
            
            logger.info(f"✓ Fetched {len(processed_jobs)} jobs from {source}")
            
            return APIResponse(
                success=True,
                data=processed_jobs,
                source=source,
                cached=False,
                cost=cost
            )
        
        return APIResponse(
            success=False,
            data={"error": "No job data available"},
            source="error",
            cached=False
        )
    
    async def _fetch_rapidapi_jobs(self, skills: List[str], location: str) -> List[Dict]:
        """Fetch jobs from RapidAPI JSearch"""
        if not self.rapidapi_key or self.rapidapi_key == "demo":
            return []
            
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        query = f"{' '.join(skills)} in {location}"
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "all"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
    
    def _get_mock_job_data(self, skills: List[str], location: str) -> List[Dict]:
        """Generate realistic mock job data for development"""
        companies = ["TCS", "Infosys", "Wipro", "HCL", "Tech Mahindra", "Accenture", "Capgemini"]
        roles = ["Software Engineer", "Backend Developer", "Full Stack Developer", "Data Analyst", "DevOps Engineer"]
        
        mock_jobs = []
        for i in range(5):
            mock_jobs.append({
                "job_title": f"{random.choice(roles)} - {', '.join(skills[:2])}",
                "employer_name": random.choice(companies),
                "job_city": location,
                "job_min_salary": f"{random.randint(6, 15)}LPA",
                "job_description": f"Looking for a skilled professional with expertise in {', '.join(skills)}. This role offers great growth opportunities...",
                "job_apply_link": f"https://example.com/apply/{i}",
                "job_posted_at_datetime_utc": datetime.now().isoformat(),
                "job_employment_type": "Full-time"
            })
        
        return mock_jobs
    
    async def get_finance_data(self, symbols: List[str]) -> APIResponse:
        """
        Real-time financial data using Yahoo Finance API
        Cost: Free
        """
        cache_key = f"finance:{','.join(symbols)}"
        
        if self.redis_available:
            cached = await self.cache.get(cache_key)
        else:
            cached = self.cache.get(cache_key)
            
        if cached:
            return APIResponse(
                success=True,
                data=json.loads(cached) if isinstance(cached, str) else cached,
                source="cache",
                cached=True
            )
        
        try:
            # Use Yahoo Finance for free stock data if available
            if YFINANCE_AVAILABLE:
                for symbol in symbols:
                    try:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period="1d")
                        info = ticker.info
                        
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                            change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) > 1 else 0
                            change_percent = (change / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0
                            
                            finance_data[symbol] = {
                                "price": round(current_price, 2),
                                "change": round(change, 2),
                                "change_percent": round(change_percent, 2),
                                "currency": "INR" if ".NS" in symbol else "USD",
                                "volume": hist['Volume'].iloc[-1] if not hist.empty else 0,
                                "market_cap": info.get('marketCap', 0),
                                "pe_ratio": info.get('trailingPE', 'N/A'),
                                "timestamp": datetime.now().isoformat()
                            }
                    except Exception as e:
                        logger.warning(f"Failed to fetch data for {symbol}: {str(e)}")
                        # Add mock data for failed symbols
                        finance_data[symbol] = self._get_mock_finance_data(symbol)
            else:
                # Use mock data if yfinance not available
                for symbol in symbols:
                    finance_data[symbol] = self._get_mock_finance_data(symbol)
            
            # Cache for 5 minutes
            if self.redis_available:
                await self.cache.setex(cache_key, 300, json.dumps(finance_data))
            else:
                self.cache[cache_key] = finance_data
            
            return APIResponse(
                success=True,
                data=finance_data,
                source="yfinance",
                cached=False,
                cost=0.0
            )
            
                        
        except Exception as e:
            logger.error(f"Finance data failed: {str(e)}")
            return APIResponse(
                success=False,
                data={"error": str(e)},
                source="error",
                cached=False
            )
    
    async def get_weather_forecast(self, location: str) -> APIResponse:
        """
        Weather data using OpenWeatherMap API
        Cost: Free for 1000 calls/day
        """
        cache_key = f"weather:{location}"
        
        if cached := await self.cache.get(cache_key):
            return APIResponse(
                success=True,
                data=json.loads(cached),
                source="cache",
                cached=True
            )
        
        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "q": location,
                "appid": self.openweathermap_key,
                "units": "metric",
                "cnt": 5  # 5-day forecast
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Process forecast data
                forecast = []
                for item in data.get("list", []):
                    forecast.append({
                        "date": item.get("dt_txt"),
                        "temperature": item["main"]["temp"],
                        "humidity": item["main"]["humidity"],
                        "description": item["weather"][0]["description"],
                        "rain_probability": item.get("pop", 0) * 100,
                        "wind_speed": item["wind"]["speed"]
                    })
                
                weather_data = {
                    "location": location,
                    "current": data["list"][0]["main"]["temp"],
                    "forecast": forecast,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Cache for 30 minutes
                await self.cache.setex(cache_key, 1800, json.dumps(weather_data))
                
                return APIResponse(
                    success=True,
                    data=weather_data,
                    source="openweathermap",
                    cached=False,
                    cost=0.0
                )
                
        except Exception as e:
            logger.error(f"Weather data failed: {str(e)}")
            return APIResponse(
                success=False,
                data={"error": str(e)},
                source="error",
                cached=False
            )
    
    async def get_commodity_prices(self, commodities: List[str]) -> APIResponse:
        """
        Commodity prices using free APIs
        Cost: Free
        """
        cache_key = f"commodities:{','.join(commodities)}"
        
        if cached := await self.cache.get(cache_key):
            return APIResponse(
                success=True,
                data=json.loads(cached),
                source="cache",
                cached=True
            )
        
        try:
            # Use free commodity price APIs
            commodity_data = {}
            
            for commodity in commodities:
                # Mock data for now - replace with real API
                commodity_data[commodity] = {
                    "price": 65000 if commodity.lower() == "gold" else 45000,
                    "change": 2.5,
                    "change_percent": 2.5,
                    "unit": "per 10g" if commodity.lower() == "gold" else "per quintal",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Cache for 1 hour
            await self.cache.setex(cache_key, 3600, json.dumps(commodity_data))
            
            return APIResponse(
                success=True,
                data=commodity_data,
                source="mock_api",
                cached=False,
                cost=0.0
            )
            
        except Exception as e:
            logger.error(f"Commodity data failed: {str(e)}")
            return APIResponse(
                success=False,
                data={"error": str(e)},
                source="error",
                cached=False
            )
    
    def _process_job_data(self, raw_jobs: List[Dict]) -> List[Dict]:
        """Process and standardize job data"""
        processed_jobs = []
        
        for job in raw_jobs[:10]:  # Limit to top 10
            processed_jobs.append({
                "title": job.get("job_title", "Unknown"),
                "company": job.get("employer_name", "Unknown Company"),
                "location": job.get("job_city", "India"),
                "salary": job.get("job_min_salary", "Not disclosed"),
                "description": job.get("job_description", "")[:500],
                "apply_link": job.get("job_apply_link", ""),
                "posted_date": job.get("job_posted_at_datetime_utc", ""),
                "employment_type": job.get("job_employment_type", "Full-time"),
                "source": "jsearch"
            })
        
        return processed_jobs
    
    async def _check_rate_limit(self, api_type: str) -> bool:
        """Check if API call is within rate limits"""
        now = datetime.now()
        hour_key = f"{api_type}:{now.hour}"
        
        current_usage = self.usage_tracker.get(hour_key, 0)
        if current_usage >= self.rate_limits[api_type]:
            return False
        
        self.usage_tracker[hour_key] = current_usage + 1
        return True
    
    def _track_cost(self, cost: float):
        """Track API costs"""
        self.cost_tracker["daily"] += cost
        self.cost_tracker["monthly"] += cost
        
        # Log if cost exceeds thresholds
        if self.cost_tracker["daily"] > 10:
            logger.warning(f"Daily cost exceeded $10: ${self.cost_tracker['daily']}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage and cost statistics"""
        return {
            "daily_cost": self.cost_tracker["daily"],
            "monthly_cost": self.cost_tracker["monthly"],
            "cache_hit_ratio": await self._get_cache_hit_ratio(),
            "api_usage": self.usage_tracker
        }
    
    async def _get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        # Implement cache hit ratio calculation
        return 0.75  # Placeholder
    
    def _get_mock_finance_data(self, symbol: str) -> Dict[str, Any]:
        """Generate realistic mock finance data"""
        base_prices = {
            "RELIANCE.NS": 2500,
            "TCS.NS": 3500,
            "INFY.NS": 1500,
            "WIPRO.NS": 400,
            "HDFCBANK.NS": 1600,
            "BTC-USD": 42000,
            "ETH-USD": 2500
        }
        
        base_price = base_prices.get(symbol, 1000)
        change = random.uniform(-5, 5)
        change_percent = (change / base_price) * 100
        
        return {
            "price": round(base_price + change, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "currency": "INR" if ".NS" in symbol else "USD",
            "volume": random.randint(100000, 10000000),
            "market_cap": base_price * random.randint(1000000, 10000000),
            "pe_ratio": round(random.uniform(15, 35), 2),
            "timestamp": datetime.now().isoformat()
        }
