"""
Government API Manager for SwarmBharat AI
Integrates with Indian government APIs for real-time data
"""

import aiohttp
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    success: bool
    data: Dict[str, Any]
    message: str
    source: str
    timestamp: str

class GovernmentAPIManager:
    """Manages integration with Indian government APIs"""
    
    def __init__(self):
        self.base_urls = {
            'digital_india': 'https://api.digitalindia.gov.in/v1',
            'income_tax': 'https://api.incometaxindia.gov.in/v2',
            'gst': 'https://api.gst.gov.in/v1',
            'epfo': 'https://api.epfindia.gov.in/v1',
            'pm_kisan': 'https://api.pmkisan.gov.in/v1',
            'scholarship': 'https://api.scholarships.gov.in/v1',
            'udyam': 'https://api.udyam.gov.in/v1',
            'mca': 'https://api.mca.gov.in/v1'
        }
        
        self.api_keys = {
            'digital_india': None,  # Will be set from environment
            'income_tax': None,
            'gst': None,
            'epfo': None,
            'pm_kisan': None,
            'scholarship': None,
            'udyam': None,
            'mca': None
        }
        
        # Initialize API keys from environment
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from environment variables"""
        import os
        
        self.api_keys.update({
            'digital_india': os.getenv('DIGITAL_INDIA_API_KEY'),
            'income_tax': os.getenv('INCOME_TAX_API_KEY'),
            'gst': os.getenv('GST_API_KEY'),
            'epfo': os.getenv('EPFO_API_KEY'),
            'pm_kisan': os.getenv('PM_KISAN_API_KEY'),
            'scholarship': os.getenv('SCHOLARSHIP_API_KEY'),
            'udyam': os.getenv('UDYAM_API_KEY'),
            'mca': os.getenv('MCA_API_KEY')
        })
    
    async def _make_api_request(self, api_name: str, endpoint: str, params: Dict[str, Any] = None) -> APIResponse:
        """Make API request to government service"""
        try:
            base_url = self.base_urls.get(api_name)
            api_key = self.api_keys.get(api_name)
            
            if not base_url:
                return APIResponse(
                    success=False,
                    data={},
                    message=f"API {api_name} not configured",
                    source=api_name,
                    timestamp=datetime.now().isoformat()
                )
            
            url = f"{base_url}{endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'SwarmBharat-AI/1.0'
            }
            
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            data=data,
                            message="Success",
                            source=api_name,
                            timestamp=datetime.now().isoformat()
                        )
                    else:
                        return APIResponse(
                            success=False,
                            data={},
                            message=f"HTTP {response.status}: {await response.text()}",
                            source=api_name,
                            timestamp=datetime.now().isoformat()
                        )
        
        except Exception as e:
            logger.error(f"API request failed for {api_name}: {str(e)}")
            return APIResponse(
                success=False,
                data={},
                message=f"Request failed: {str(e)}",
                source=api_name,
                timestamp=datetime.now().isoformat()
            )
    
    # Digital India APIs
    async def verify_aadhaar(self, aadhaar_number: str, otp: str = None) -> APIResponse:
        """Verify Aadhaar number using Digital India API"""
        params = {'aadhaar': aadhaar_number}
        if otp:
            params['otp'] = otp
        
        return await self._make_api_request('digital_india', '/aadhaar/verify', params)
    
    async def verify_pan(self, pan_number: str) -> APIResponse:
        """Verify PAN number using Digital India API"""
        params = {'pan': pan_number}
        return await self._make_api_request('digital_india', '/pan/verify', params)
    
    async def get_digilocker_documents(self, aadhaar_number: str) -> APIResponse:
        """Get documents from DigiLocker"""
        params = {'aadhaar': aadhaar_number}
        return await self._make_api_request('digital_india', '/digilocker/documents', params)
    
    # Income Tax APIs
    async def get_tax_filing_status(self, pan_number: str) -> APIResponse:
        """Get income tax filing status"""
        params = {'pan': pan_number}
        return await self._make_api_request('income_tax', '/filing/status', params)
    
    async def get_tax_refund_status(self, pan_number: str, assessment_year: str) -> APIResponse:
        """Get tax refund status"""
        params = {'pan': pan_number, 'ay': assessment_year}
        return await self._make_api_request('income_tax', '/refund/status', params)
    
    async def calculate_tax_liability(self, income: int, regime: str = 'old') -> APIResponse:
        """Calculate tax liability"""
        params = {'income': income, 'regime': regime}
        return await self._make_api_request('income_tax', '/calculate/tax', params)
    
    # GST APIs
    async def verify_gst_registration(self, gstin: str) -> APIResponse:
        """Verify GST registration"""
        params = {'gstin': gstin}
        return await self._make_api_request('gst', '/registration/verify', params)
    
    async def get_gst_returns_status(self, gstin: str) -> APIResponse:
        """Get GST returns filing status"""
        params = {'gstin': gstin}
        return await self._make_api_request('gst', '/returns/status', params)
    
    async def get_gst_payment_status(self, gstin: str) -> APIResponse:
        """Get GST payment status"""
        params = {'gstin': gstin}
        return await self._make_api_request('gst', '/payment/status', params)
    
    # EPFO APIs
    async def get_epfo_balance(self, uan_number: str) -> APIResponse:
        """Get EPFO balance"""
        params = {'uan': uan_number}
        return await self._make_api_request('epfo', '/balance', params)
    
    async def get_epfo_passbook(self, uan_number: str) -> APIResponse:
        """Get EPFO passbook"""
        params = {'uan': uan_number}
        return await self._make_api_request('epfo', '/passbook', params)
    
    async def check_pf_withdrawal_status(self, uan_number: str) -> APIResponse:
        """Check PF withdrawal status"""
        params = {'uan': uan_number}
        return await self._make_api_request('epfo', '/withdrawal/status', params)
    
    # PM-KISAN APIs
    async def get_pm_kisan_status(self, mobile_number: str) -> APIResponse:
        """Get PM-KISAN beneficiary status"""
        params = {'mobile': mobile_number}
        return await self._make_api_request('pm_kisan', '/beneficiary/status', params)
    
    async def get_pm_kisan_payment_history(self, mobile_number: str) -> APIResponse:
        """Get PM-KISAN payment history"""
        params = {'mobile': mobile_number}
        return await self._make_api_request('pm_kisan', '/payments/history', params)
    
    async def check_pm_kisan_eligibility(self, state: str, land_holding: float) -> APIResponse:
        """Check PM-KISAN eligibility"""
        params = {'state': state, 'land': land_holding}
        return await self._make_api_request('pm_kisan', '/eligibility/check', params)
    
    # Scholarship APIs
    async def get_scholarship_list(self, category: str = 'all') -> APIResponse:
        """Get list of available scholarships"""
        params = {'category': category}
        return await self._make_api_request('scholarship', '/list', params)
    
    async def check_scholarship_eligibility(self, student_id: str, scholarship_id: str) -> APIResponse:
        """Check scholarship eligibility"""
        params = {'student_id': student_id, 'scholarship_id': scholarship_id}
        return await self._make_api_request('scholarship', '/eligibility/check', params)
    
    async def get_scholarship_application_status(self, application_id: str) -> APIResponse:
        """Get scholarship application status"""
        params = {'application_id': application_id}
        return await self._make_api_request('scholarship', '/application/status', params)
    
    # Udyam Registration APIs
    async def verify_udyam_registration(self, udyam_number: str) -> APIResponse:
        """Verify Udyam registration"""
        params = {'udyam': udyam_number}
        return await self._make_api_request('udyam', '/registration/verify', params)
    
    async def get_udyam_certificate(self, udyam_number: str) -> APIResponse:
        """Get Udyam certificate"""
        params = {'udyam': udyam_number}
        return await self._make_api_request('udyam', '/certificate', params)
    
    async def check_udyam_eligibility(self, business_type: str, investment: float) -> APIResponse:
        """Check Udyam eligibility"""
        params = {'type': business_type, 'investment': investment}
        return await self._make_api_request('udyam', '/eligibility/check', params)
    
    # MCA APIs
    async def verify_company_registration(self, cin_number: str) -> APIResponse:
        """Verify company registration"""
        params = {'cin': cin_number}
        return await self._make_api_request('mca', '/company/verify', params)
    
    async def get_company_details(self, cin_number: str) -> APIResponse:
        """Get company details"""
        params = {'cin': cin_number}
        return await self._make_api_request('mca', '/company/details', params)
    
    async def get_director_details(self, din_number: str) -> APIResponse:
        """Get director details"""
        params = {'din': din_number}
        return await self._make_api_request('mca', '/director/details', params)
    
    # Utility Methods
    async def get_all_user_benefits(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get all applicable government benefits for user"""
        benefits = {
            'schemes': [],
            'tax_benefits': [],
            'subsidies': [],
            'eligibility_status': {}
        }
        
        # Check PM-KISAN if farmer
        if user_profile.get('occupation') == 'farmer':
            mobile = user_profile.get('mobile')
            if mobile:
                pm_kisan_status = await self.get_pm_kisan_status(mobile)
                if pm_kisan_status.success:
                    benefits['schemes'].append({
                        'name': 'PM-KISAN',
                        'status': 'active' if pm_kisan_status.data.get('beneficiary') else 'not_enrolled',
                        'amount': '₹6,000 per year'
                    })
        
        # Check tax benefits if salaried
        if user_profile.get('occupation') == 'salaried':
            pan = user_profile.get('pan')
            if pan:
                tax_status = await self.get_tax_filing_status(pan)
                if tax_status.success:
                    benefits['tax_benefits'].extend([
                        {'name': 'Section 80C', 'limit': '₹1.5L'},
                        {'name': 'HRA Exemption', 'limit': 'Based on rent'},
                        {'name': 'Standard Deduction', 'limit': '₹50,000'}
                    ])
        
        # Check scholarships if student
        if user_profile.get('occupation') == 'student':
            scholarships = await self.get_scholarship_list()
            if scholarships.success:
                for scholarship in scholarships.data.get('scholarships', [])[:5]:
                    benefits['schemes'].append({
                        'name': scholarship.get('name'),
                        'type': 'scholarship',
                        'amount': scholarship.get('amount', 'Varies')
                    })
        
        # Check business benefits if entrepreneur
        if user_profile.get('occupation') == 'entrepreneur':
            benefits['schemes'].extend([
                {'name': 'Startup India', 'type': 'funding', 'amount': 'Up to ₹5 crore'},
                {'name': 'MSME Loan', 'type': 'loan', 'amount': 'Up to ₹5 crore'},
                {'name': 'GST Composition', 'type': 'tax', 'benefit': 'Lower tax rates'}
            ])
        
        return benefits
    
    async def get_api_status(self) -> Dict[str, bool]:
        """Get status of all government APIs"""
        status = {}
        
        for api_name in self.base_urls.keys():
            try:
                # Try a simple health check
                response = await self._make_api_request(api_name, '/health')
                status[api_name] = response.success
            except Exception:
                status[api_name] = False
        
        return status

# Global government API manager instance
government_api_manager = GovernmentAPIManager()
