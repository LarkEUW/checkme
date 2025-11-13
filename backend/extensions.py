from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from database import get_db
from models import Extension, ExtensionVersion, User
from auth import get_current_active_user

router = APIRouter()

# Pydantic models
class ExtensionResponse(BaseModel):
    id: str
    store_id: str
    store_type: str
    name: str
    developer_name: Optional[str]
    verified_publisher: bool
    created_at: str

class ExtensionVersionResponse(BaseModel):
    id: str
    version: str
    created_at: str

# Routes
@router.get("/", response_model=List[ExtensionResponse])
async def list_extensions(
    skip: int = 0,
    limit: int = 20,
    store_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all extensions"""
    
    query = select(Extension)
    
    if store_type:
        query = query.where(Extension.store_type == store_type)
    
    query = query.offset(skip).limit(limit).order_by(Extension.created_at.desc())
    
    result = await db.execute(query)
    extensions = result.scalars().all()
    
    return [
        ExtensionResponse(
            id=str(ext.id),
            store_id=ext.store_id,
            store_type=ext.store_type,
            name=ext.name,
            developer_name=ext.developer_name,
            verified_publisher=ext.verified_publisher,
            created_at=ext.created_at.isoformat()
        )
        for ext in extensions
    ]

@router.get("/{extension_id}")
async def get_extension(
    extension_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get extension details with versions"""
    
    try:
        ext_uuid = uuid.UUID(extension_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid extension ID")
    
    extension = await db.get(Extension, ext_uuid)
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    # Get versions
    versions = await db.execute(
        select(ExtensionVersion).where(ExtensionVersion.extension_id == ext_uuid)
    )
    version_list = versions.scalars().all()
    
    return {
        "extension": ExtensionResponse(
            id=str(extension.id),
            store_id=extension.store_id,
            store_type=extension.store_type,
            name=extension.name,
            developer_name=extension.developer_name,
            verified_publisher=extension.verified_publisher,
            created_at=extension.created_at.isoformat()
        ),
        "versions": [
            ExtensionVersionResponse(
                id=str(v.id),
                version=v.version,
                created_at=v.created_at.isoformat()
            )
            for v in version_list
        ]
    }