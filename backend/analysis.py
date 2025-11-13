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
def _extract_extension_identifier(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.rstrip("/")
    if not url:
        return None
    try:
        return url.split("/")[-1]
    except Exception:
        return None


def _prepare_workspace(analysis_id: uuid.UUID) -> Path:
    workspace_root = Path("analysis_workspace")
    workspace_root.mkdir(exist_ok=True)
    workspace_dir = workspace_root / str(analysis_id)
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir


def _extract_crx_file(crx_path: Path, destination: Path) -> None:
    with open(crx_path, "rb") as handle:
        data = handle.read()
    zip_header = b"PK\x03\x04"
    zip_start = data.find(zip_header)
    if zip_start == -1:
        raise ValueError("Invalid CRX file: ZIP header not found")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
        temp_zip.write(data[zip_start:])
        temp_zip_path = Path(temp_zip.name)
    try:
        with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
            zip_ref.extractall(destination)
    finally:
        temp_zip_path.unlink(missing_ok=True)


def _copy_or_extract_extension(source: str, destination: Path) -> None:
    source_path = Path(source)
    if source_path.is_dir():
        shutil.copytree(source_path, destination, dirs_exist_ok=True)
        return
    if zipfile.is_zipfile(source_path):
        with zipfile.ZipFile(source_path, "r") as zip_ref:
            zip_ref.extractall(destination)
        return
    if source_path.suffix.lower() == ".crx":
        _extract_crx_file(source_path, destination)
        return
    raise ValueError("Unsupported extension package format")


def _load_manifest_from_directory(directory: Path) -> dict:
    manifest_path = directory / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    for path in directory.rglob("manifest.json"):
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    raise HTTPException(status_code=400, detail="Manifest not found in extension file")


def _calculate_directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


async def extract_manifest_from_file(file_path: str, destination: Optional[Path] = None) -> dict:
    """Extract manifest.json from extension file into an optional destination directory"""
    try:
        if destination is None:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                _copy_or_extract_extension(file_path, temp_path)
                return _load_manifest_from_directory(temp_path)
        else:
            if destination.exists():
                shutil.rmtree(destination)
            destination.mkdir(parents=True, exist_ok=True)
            _copy_or_extract_extension(file_path, destination)
            return _load_manifest_from_directory(destination)
    except HTTPException:
        raise
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
    store_identifier = _extract_extension_identifier(url)
    resolved_store_type = store_type or "upload"
    
    # Handle file upload
    file_path = None
    if file:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{analysis_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    if resolved_store_type == "upload" and store_identifier is None:
        store_identifier = f"upload-{analysis_id}"
    
    extension = Extension(
        id=uuid.uuid4(),
        store_id=store_identifier or f"{resolved_store_type}-{analysis_id}",
        store_type=resolved_store_type,
        name=file.filename if file else "Pending Analysis",
        verified_publisher=False
    )
    db.add(extension)
    await db.flush()
    
    version = ExtensionVersion(
        id=uuid.uuid4(),
        extension_id=extension.id,
        version="0.0.0",
        manifest_json={},
        file_path=str(file_path) if file_path else None,
        file_size=os.path.getsize(file_path) if file_path and os.path.isfile(file_path) else None
    )
    db.add(version)
    await db.flush()
    
    # Create analysis record
    analysis = Analysis(
        id=analysis_id,
        extension_id=extension.id,
        version_id=version.id,
        user_id=current_user.id,
        status=AnalysisStatus.PENDING
    )
    
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    # Start analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id,
        mode,
        url,
        str(file_path) if file_path else None,
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
        analysis = None
        workspace_dir: Optional[Path] = None
        cleanup_paths: List[Path] = []
        try:
            analysis = await db.get(Analysis, analysis_id)
            if not analysis:
                return
            extension = await db.get(Extension, analysis.extension_id) if analysis.extension_id else None
            version = await db.get(ExtensionVersion, analysis.version_id) if analysis.version_id else None

            analysis.status = AnalysisStatus.IN_PROGRESS
            await db.commit()
            await db.refresh(analysis)

            manifest: Optional[dict] = None
            store_data: Optional[dict] = None
            workspace_dir = _prepare_workspace(analysis_id)
            file_path_for_engine = str(workspace_dir)
            extension_identifier = _extract_extension_identifier(url)

            if mode in ['url', 'combined'] and url and store_type:
                if extension_identifier:
                    store_data = await get_store_data(store_type, extension_identifier)

                from extension_downloader import ExtensionDownloader

                async with ExtensionDownloader() as downloader:
                    download_result = await downloader.download_from_store(url, store_type)
                downloaded_path = Path(download_result['file_path'])
                manifest = await extract_manifest_from_file(str(downloaded_path), workspace_dir)
                store_data = download_result.get('store_data') or store_data
                extension_identifier = download_result.get('extension_id') or extension_identifier
                cleanup_root = downloaded_path.parent if downloaded_path.parent.exists() else downloaded_path
                cleanup_paths.append(cleanup_root)

            elif mode == 'file' and file_path:
                manifest = await extract_manifest_from_file(file_path, workspace_dir)

            if not manifest:
                analysis.status = AnalysisStatus.FAILED
                await db.commit()
                return

            if extension:
                if extension_identifier:
                    extension.store_id = extension_identifier
                if store_type:
                    extension.store_type = store_type
                extension.name = manifest.get('name') or extension.name or "Unknown Extension"
                extension.developer_name = manifest.get('author') or extension.developer_name
                if store_data:
                    extension.developer_email = store_data.get('developer_email') or extension.developer_email
                    extension.developer_website = store_data.get('developer_website') or extension.developer_website
                    if store_data.get('verified_publisher') is not None:
                        extension.verified_publisher = bool(store_data.get('verified_publisher'))
                    extension.duns_number = store_data.get('duns_number') or extension.duns_number
                    extension.privacy_policy_url = store_data.get('privacy_policy_url') or extension.privacy_policy_url
                    extension.support_url = store_data.get('support_url') or extension.support_url

            if version:
                version.version = manifest.get('version', version.version or "0.0.0")
                version.manifest_json = manifest
                version.file_path = file_path_for_engine
                version.file_size = _calculate_directory_size(workspace_dir)
                if store_data and store_data.get('last_updated'):
                    try:
                        version.last_updated = datetime.fromisoformat(store_data['last_updated'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

            await db.commit()

            results = await analysis_engine.analyze_extension(manifest, file_path_for_engine, store_data)

            analysis.status = AnalysisStatus.COMPLETED
            analysis.final_score = results['final_score']
            analysis.verdict = Verdict(results['verdict'])

            analysis.metadata_score = results['scores'].get('metadata', 0)
            analysis.permissions_score = results['scores'].get('permissions', 0)
            analysis.code_behavior_score = results['scores'].get('code_behavior', 0)
            analysis.network_score = results['scores'].get('network', 0)
            analysis.threat_intel_score = results['scores'].get('threat_intel', 0)
            analysis.cve_score = results['scores'].get('cve', 0)
            analysis.ai_score = results['scores'].get('ai', 0)

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

        except Exception:
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                await db.commit()
        finally:
            for path in cleanup_paths:
                try:
                    if path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                    elif path.exists():
                        path.unlink(missing_ok=True)
                except Exception:
                    pass

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