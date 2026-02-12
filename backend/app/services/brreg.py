"""
Brønnøysundregistrene API Integration
Search Norwegian company registry for autocomplete
"""
import httpx
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Brønnøysund API endpoints
BRREG_SEARCH_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"


async def search_companies(query: str, limit: int = 10) -> List[Dict]:
    """
    Search companies in Brønnøysundregistrene by name
    
    Args:
        query: Company name search query (e.g., "GHB")
        limit: Maximum number of results (default: 10)
    
    Returns:
        List of company dictionaries with:
        - name: Company name
        - org_number: Organization number (9 digits)
        - address: Formatted address
        - postal_code: Postal code
        - city: City/municipality
        - municipality: Municipality name
        - nace_code: NACE industry code
        - nace_description: Industry description
    """
    if not query or len(query) < 2:
        return []
    
    try:
        params = {
            "navn": query,
            "size": limit,
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(BRREG_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            companies = []
            entities = data.get("_embedded", {}).get("enheter", [])
            
            for entity in entities:
                # Extract business address
                forretningsadresse = entity.get("forretningsadresse", {})
                postadresse = entity.get("postadresse", {})
                
                # Prefer business address, fallback to postal address
                address_data = forretningsadresse or postadresse
                
                # Build formatted address
                address_lines = []
                if address_data.get("adresse"):
                    address_lines.extend(address_data["adresse"])
                
                formatted_address = ", ".join(address_lines) if address_lines else None
                
                # Extract NACE code (industry classification)
                naeringskode1 = entity.get("naeringskode1", {})
                nace_code = naeringskode1.get("kode", None)
                nace_description = naeringskode1.get("beskrivelse", None)
                
                companies.append({
                    "name": entity.get("navn", ""),
                    "org_number": entity.get("organisasjonsnummer", ""),
                    "address": formatted_address,
                    "postal_code": address_data.get("postnummer", None),
                    "city": address_data.get("poststed", None),
                    "municipality": entity.get("kommune", {}).get("kommunenavn", None),
                    "municipality_number": entity.get("kommune", {}).get("kommunenummer", None),
                    "nace_code": nace_code,
                    "nace_description": nace_description,
                    "organizational_form": entity.get("organisasjonsform", {}).get("kode", None),
                    "organizational_form_desc": entity.get("organisasjonsform", {}).get("beskrivelse", None),
                })
            
            logger.info(f"Brreg search for '{query}': found {len(companies)} results")
            return companies
    
    except httpx.HTTPError as e:
        logger.error(f"Brreg API error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in brreg search: {str(e)}")
        return []


async def get_company_details(org_number: str) -> Optional[Dict]:
    """
    Get detailed company information by organization number
    
    Args:
        org_number: 9-digit organization number
    
    Returns:
        Company details dictionary or None if not found
    """
    try:
        url = f"{BRREG_SEARCH_URL}/{org_number}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            entity = response.json()
            
            # Extract address
            forretningsadresse = entity.get("forretningsadresse", {})
            postadresse = entity.get("postadresse", {})
            address_data = forretningsadresse or postadresse
            
            address_lines = []
            if address_data.get("adresse"):
                address_lines.extend(address_data["adresse"])
            
            formatted_address = ", ".join(address_lines) if address_lines else None
            
            # Extract NACE code
            naeringskode1 = entity.get("naeringskode1", {})
            
            return {
                "name": entity.get("navn", ""),
                "org_number": entity.get("organisasjonsnummer", ""),
                "address": formatted_address,
                "postal_code": address_data.get("postnummer", None),
                "city": address_data.get("poststed", None),
                "municipality": entity.get("kommune", {}).get("kommunenavn", None),
                "nace_code": naeringskode1.get("kode", None),
                "nace_description": naeringskode1.get("beskrivelse", None),
                "organizational_form": entity.get("organisasjonsform", {}).get("beskrivelse", None),
                "registration_date": entity.get("registreringsdatoEnhetsregisteret", None),
                "employees": entity.get("antallAnsatte", None),
            }
    
    except httpx.HTTPError as e:
        logger.error(f"Brreg API error fetching {org_number}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching company {org_number}: {str(e)}")
        return None
