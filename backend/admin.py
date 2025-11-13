from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from database import get_db
from models import User, UserRole, SystemSetting, ApiKey, Analysis, AnalysisStatus, Verdict
from auth import get_admin_user

router = APIRouter()

# Pydantic models
class SystemSettingCreate(BaseModel):
    key: str
    value: dict
    description: Optional[str] = None

class SystemSettingResponse(BaseModel):
    id: str
    key: str
    value: dict
    description: Optional[str]
    created_at: str

class ApiKeyCreate(BaseModel):
    service_name: str
    key_name: str
    encrypted_key: str

class ApiKeyResponse(BaseModel):
    id: str
    service_name: str
    key_name: str
    is_active: bool
    usage_count: int
    last_used: Optional[str]
    created_at: str

# Routes for system settings
@router.post("/settings", response_model=SystemSettingResponse)
async def create_setting(
    setting_data: SystemSettingCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a system setting"""
    
    # Check if key already exists
    existing = await db.execute(
        select(SystemSetting).where(SystemSetting.key == setting_data.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Setting key already exists")
    
    setting = SystemSetting(
        id=uuid.uuid4(),
        key=setting_data.key,
        value=setting_data.value,
        description=setting_data.description
    )
    
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    
    return SystemSettingResponse(
        id=str(setting.id),
        key=setting.key,
        value=setting.value,
        description=setting.description,
        created_at=setting.created_at.isoformat()
    )

@router.get("/settings", response_model=List[SystemSettingResponse])
async def list_settings(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all system settings"""
    
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    
    return [
        SystemSettingResponse(
            id=str(setting.id),
            key=setting.key,
            value=setting.value,
            description=setting.description,
            created_at=setting.created_at.isoformat()
        )
        for setting in settings
    ]

@router.get("/settings/{key}", response_model=SystemSettingResponse)
async def get_setting(
    key: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific setting"""
    
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return SystemSettingResponse(
        id=str(setting.id),
        key=setting.key,
        value=setting.value,
        description=setting.description,
        created_at=setting.created_at.isoformat()
    )

@router.put("/settings/{key}", response_model=SystemSettingResponse)
async def update_setting(
    key: str,
    setting_data: SystemSettingCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a system setting"""
    
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    setting.value = setting_data.value
    setting.description = setting_data.description
    
    await db.commit()
    await db.refresh(setting)
    
    return SystemSettingResponse(
        id=str(setting.id),
        key=setting.key,
        value=setting.value,
        description=setting.description,
        created_at=setting.created_at.isoformat()
    )

@router.delete("/settings/{key}")
async def delete_setting(
    key: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a system setting"""
    
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    await db.delete(setting)
    await db.commit()
    
    return {"message": "Setting deleted successfully"}

# Routes for API keys
@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an API key"""
    
    api_key = ApiKey(
        id=uuid.uuid4(),
        service_name=api_key_data.service_name,
        key_name=api_key_data.key_name,
        encrypted_key=api_key_data.encrypted_key
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return ApiKeyResponse(
        id=str(api_key.id),
        service_name=api_key.service_name,
        key_name=api_key.key_name,
        is_active=api_key.is_active,
        usage_count=api_key.usage_count,
        last_used=api_key.last_used.isoformat() if api_key.last_used else None,
        created_at=api_key.created_at.isoformat()
    )

@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all API keys"""
    
    result = await db.execute(select(ApiKey))
    api_keys = result.scalars().all()
    
    return [
        ApiKeyResponse(
            id=str(key.id),
            service_name=key.service_name,
            key_name=key.key_name,
            is_active=key.is_active,
            usage_count=key.usage_count,
            last_used=key.last_used.isoformat() if key.last_used else None,
            created_at=key.created_at.isoformat()
        )
        for key in api_keys
    ]

@router.put("/api-keys/{key_id}/toggle")
async def toggle_api_key(
    key_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle API key active status"""
    
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid API key ID")
    
    api_key = await db.get(ApiKey, key_uuid)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = not api_key.is_active
    await db.commit()
    await db.refresh(api_key)
    
    return ApiKeyResponse(
        id=str(api_key.id),
        service_name=api_key.service_name,
        key_name=api_key.key_name,
        is_active=api_key.is_active,
        usage_count=api_key.usage_count,
        last_used=api_key.last_used.isoformat() if api_key.last_used else None,
        created_at=api_key.created_at.isoformat()
    )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an API key"""
    
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid API key ID")
    
    api_key = await db.get(ApiKey, key_uuid)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    await db.delete(api_key)
    await db.commit()
    
    return {"message": "API key deleted successfully"}

# Dashboard metrics
@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard metrics"""
    
    # User metrics
    total_users = await db.execute(select(User))
    total_users_count = len(total_users.scalars().all())
    
    active_users = await db.execute(select(User).where(User.is_active == True))
    active_users_count = len(active_users.scalars().all())
    
    admin_users = await db.execute(select(User).where(User.role == UserRole.ADMIN))
    admin_users_count = len(admin_users.scalars().all())
    
    # Analysis metrics
    total_analyses = await db.execute(select(Analysis))
    total_analyses_count = len(total_analyses.scalars().all())
    
    completed_analyses = await db.execute(select(Analysis).where(Analysis.status == AnalysisStatus.COMPLETED))
    completed_analyses_count = len(completed_analyses.scalars().all())
    
    # Verdict distribution
    verdict_counts = {}
    verdict_map = {
        Verdict.SAFE.value: Verdict.SAFE,
        Verdict.NEEDS_REVIEW.value: Verdict.NEEDS_REVIEW,
        Verdict.HIGH_RISK.value: Verdict.HIGH_RISK,
        Verdict.BLOCK.value: Verdict.BLOCK,
        Verdict.MALICIOUS.value: Verdict.MALICIOUS
    }
    for verdict_value, verdict_enum in verdict_map.items():
        count = await db.execute(select(Analysis).where(Analysis.verdict == verdict_enum))
        verdict_counts[verdict_value] = len(count.scalars().all())
    
    return {
        "users": {
            "total": total_users_count,
            "active": active_users_count,
            "admins": admin_users_count
        },
        "analyses": {
            "total": total_analyses_count,
            "completed": completed_analyses_count,
            "verdicts": verdict_counts
        }
    }