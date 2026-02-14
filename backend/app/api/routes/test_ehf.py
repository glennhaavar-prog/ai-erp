"""
EHF Testing API - Test EHF invoice processing (Stub implementation)
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/api/test", tags=["Testing"])


class EHFTestRequest(BaseModel):
    xml_content: str


@router.post("/ehf/send-raw")
async def test_ehf_processing(
    request: EHFTestRequest
) -> Dict[str, Any]:
    """
    Test EHF invoice processing (stub)
    """
    return {
        "success": False,
        "test_mode": True,
        "timestamp": "2026-02-14T12:00:00Z",
        "steps": [
            {
                "step": "parsing",
                "status": "❌ Not implemented",
                "message": "EHF processing not yet implemented"
            }
        ],
        "error": "EHF testing endpoint is a stub - feature not yet implemented"
    }


@router.get("/samples/{filename}")
async def get_sample_file(filename: str) -> Dict[str, Any]:
    """
    Get sample EHF file (stub)
    """
    raise HTTPException(
        status_code=404,
        detail=f"Sample file '{filename}' not found. Feature not yet implemented."
    )
