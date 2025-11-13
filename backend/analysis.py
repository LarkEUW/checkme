from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import uuid
import json
import os
import tempfile
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

from database import get_db, AsyncSessionLocal
from models import (
    Analysis, AnalysisStatus, Verdict, Extension, ExtensionVersion, User, UserRole
)
from auth import get_current_active_user, get_admin_user
from analysis_engine import AnalysisEngine

router = APIRouter()

# Pydantic models
class AnalysisRequest(BaseModel):
    mode: str  # 'url', 'file', 'combined'
    url: Optional[HttpUrl] = None
    file_path: Optional[str] = None
    store_type: Optional[str] = None  # 'chrome', 'firefox', 'edge'

class AnalysisResponse(BaseModel):
    id: str
    status: str
    final_score: Optional[float]
    verdict: Optional[str]
    created_at: str

class AnalysisDetailResponse(BaseModel):
    id: str
    status: str
    final_score: Optional[float]
    verdict: Optional[str]
    scores: dict
    results: dict
    bonuses: dict
    maluses: dict
    created_at: str
    completed_at: Optional[str]

# Analysis engine instance
analysis_engine = AnalysisEngine()

# Helper functions
async def extract_manifest_from_file(file_path: str) -> dict:
    """Extract manifest.json from extension file"""
    try:
        if file_path.endswith('.zip') or file_path.endswith('.crx'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to temp directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Look for manifest.json
                    manifest_path = os.path.join(temp_dir, 'manifest.json')
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    else:
                        # Look in subdirectories
                        for root, dirs, files in os.walk(temp_dir):
                            if 'manifest.json' in files:
                                with open(os.path.join(root, 'manifest.json'), 'r', encoding='utf-8') as f:
                                    return json.load(f)
        
        raise HTTPException(status_code=400, detail="Manifest not found in extension file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract manifest: {str(e)}")

async def get_store_data(store_type: str, extension_id: str) -> Optional[dict]:
    """Get extension data from web store"""
    # Use the real downloader to get store data
    try:
        from extension_downloader import ExtensionDownloader
        async with ExtensionDownloader() as downloader:
            # For Chrome extensions, we can get store data
            if store_type == 'chrome':
                return await downloader._get_chrome_store_data(extension_id)
            elif store_type == 'firefox':
                return await downloader._get_firefox_store_data(extension_id)
            elif store_type == 'edge':
                return await downloader._get_edge_store_data(extension_id)
    except Exception:
        # Return fallback data on error
        return {
            'rating': 4.0,
            'users': 1000,
            'last_updated': '2024-01-01T00:00:00Z',
            'verified_publisher': False,
            'developer_email': 'unknown@example.com',
            'developer_website': 'https://example.com'
        }

# Routes
@router.post("/analyze", response_model=AnalysisResponse)
async def create_analysis(
    background_tasks: BackgroundTasks,
    mode: str = Form(...),
    url: Optional[str] = Form(None),
    store_type: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new analysis job"""
    
    # Validate input
    if mode == 'url' and not url:
        raise HTTPException(status_code=400, detail="URL required for URL mode")
    if mode == 'file' and not file:
        raise HTTPException(status_code=400, detail="File required for file mode")
    if mode in ['url', 'combined'] and not store_type:
        raise HTTPException(status_code=400, detail="Store type required")
    
    analysis_id = uuid.uuid4()
    
    # Handle file upload
    file_path = None
    if file:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{analysis_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    # Create analysis record
    analysis = Analysis(
        id=analysis_id,
        extension_id=uuid.uuid4(),  # Will be updated later
        version_id=uuid.uuid4(),    # Will be updated later
        user_id=current_user.id,
        status=AnalysisStatus.PENDING
    )
    
    db.add(analysis)
    await db.commit()
    
    # Start analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id,
        mode,
        url,
        file_path,
        store_type,
        current_user.id
    )
    
    return AnalysisResponse(
        id=str(analysis_id),
        status=AnalysisStatus.PENDING.value,
        final_score=None,
        verdict=None,
        created_at=analysis.created_at.isoformat()
    )

async def run_analysis(
    analysis_id: uuid.UUID,
    mode: str,
    url: Optional[str],
    file_path: Optional[str],
    store_type: Optional[str],
    user_id: uuid.UUID
):
    """Run the actual analysis"""
    async with AsyncSessionLocal() as db:
        try:
            # Get analysis record
            analysis = await db.get(Analysis, analysis_id)
            if not analysis:
                return
            
            # Update status to in progress
            analysis.status = AnalysisStatus.IN_PROGRESS
            await db.commit()
            
            manifest = None
            store_data = None
            temp_dir = None
            
            if mode in ['url', 'combined']:
                # Extract extension ID from URL
                # Example: https://chrome.google.com/webstore/detail/adblock-plus-free-ad-bloc/cfhdojbkjhnklbpkdaibdccddilifddb
                extension_id = url.split('/')[-1] if url else None
                
                # Get store data
                if extension_id and store_type:
                    store_data = await get_store_data(store_type, extension_id)
                
                # Download and extract extension using real downloader
                from extension_downloader import ExtensionDownloader
                
                async with ExtensionDownloader() as downloader:
                    download_result = await downloader.download_from_store(url, store_type)
                    manifest_path = os.path.join(download_result['file_path'], 'manifest.json')
                    
                    # Load the real manifest
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    file_path = download_result['file_path']
                    store_data = download_result.get('store_data')
            
            elif mode == 'file' and file_path:
                # Extract manifest from uploaded file
                manifest = await extract_manifest_from_file(file_path)
            
            if not manifest:
                analysis.status = AnalysisStatus.FAILED
                await db.commit()
                return
            
            # Run analysis
            results = await analysis_engine.analyze_extension(manifest, file_path, store_data)
            
            # Update analysis record with results
            analysis.status = AnalysisStatus.COMPLETED
            analysis.final_score = results['final_score']
            analysis.verdict = Verdict(results['verdict'])
            
            # Store individual scores
            analysis.metadata_score = results['scores'].get('metadata', 0)
            analysis.permissions_score = results['scores'].get('permissions', 0)
            analysis.code_behavior_score = results['scores'].get('code_behavior', 0)
            analysis.network_score = results['scores'].get('network', 0)
            analysis.threat_intel_score = results['scores'].get('threat_intel', 0)
            analysis.cve_score = results['scores'].get('cve', 0)
            analysis.ai_score = results['scores'].get('ai', 0)
            
            # Store detailed results
            analysis.metadata_data = results['results'].get('metadata', {}).get('data', {})
            analysis.permissions_data = results['results'].get('permissions', {}).get('data', {})
            analysis.code_behavior_data = results['results'].get('code_behavior', {}).get('data', {})
            analysis.network_data = results['results'].get('network', {}).get('data', {})
            analysis.threat_intel_data = results['results'].get('threat_intel', {}).get('data', {})
            analysis.cve_data = results['results'].get('cve', {}).get('data', {})
            analysis.ai_analysis = results['results'].get('ai', {}).get('data', {})
            
            analysis.bonuses = results['bonuses']
            analysis.maluses = results['maluses']
            
            analysis.completed_at = datetime.utcnow()
            
            await db.commit()
            
        except Exception as e:
            # Update status to failed
            analysis = await db.get(Analysis, analysis_id)
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                await db.commit()
        
        finally:
            # Cleanup temp files
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

@router.get("/analysis/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed analysis results"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    analysis = await db.get(Analysis, analysis_uuid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this analysis")
    
    return AnalysisDetailResponse(
        id=str(analysis.id),
        status=analysis.status.value,
        final_score=analysis.final_score,
        verdict=analysis.verdict.value if analysis.verdict else None,
        scores={
            'metadata': analysis.metadata_score,
            'permissions': analysis.permissions_score,
            'code_behavior': analysis.code_behavior_score,
            'network': analysis.network_score,
            'threat_intel': analysis.threat_intel_score,
            'cve': analysis.cve_score,
            'ai': analysis.ai_score
        },
        results={
            'metadata': {'data': analysis.metadata_data, 'findings': []},
            'permissions': {'data': analysis.permissions_data, 'findings': []},
            'code_behavior': {'data': analysis.code_behavior_data, 'findings': []},
            'network': {'data': analysis.network_data, 'findings': []},
            'threat_intel': {'data': analysis.threat_intel_data, 'findings': []},
            'cve': {'data': analysis.cve_data, 'findings': []},
            'ai': {'data': analysis.ai_analysis, 'findings': []}
        },
        bonuses=analysis.bonuses,
        maluses=analysis.maluses,
        created_at=analysis.created_at.isoformat(),
        completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None
    )

@router.get("/analyses", response_model=List[AnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    verdict: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List analyses with filtering"""
    
    query = select(Analysis)
    
    # Filter by user if not admin
    if current_user.role != UserRole.ADMIN:
        query = query.where(Analysis.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.where(Analysis.status == AnalysisStatus(status))
    if verdict:
        query = query.where(Analysis.verdict == Verdict(verdict))
    
    query = query.offset(skip).limit(limit).order_by(Analysis.created_at.desc())
    
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return [
        AnalysisResponse(
            id=str(analysis.id),
            status=analysis.status.value,
            final_score=analysis.final_score,
            verdict=analysis.verdict.value if analysis.verdict else None,
            created_at=analysis.created_at.isoformat()
        )
        for analysis in analyses
    ]

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an analysis"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    analysis = await db.get(Analysis, analysis_uuid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this analysis")
    
    await db.delete(analysis)
    await db.commit()
    
    return {"message": "Analysis deleted successfully"}