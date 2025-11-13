from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from database import get_db
from models import Analysis, Comment, Decision, User, UserRole
from auth import get_current_active_user, get_admin_user

router = APIRouter()

# Pydantic models
class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: str
    content: str
    user_name: str
    created_at: str

class DecisionCreate(BaseModel):
    decision: str  # accept, reject, pending
    reason: Optional[str] = None

class DecisionResponse(BaseModel):
    id: str
    decision: str
    reason: Optional[str]
    user_name: str
    created_at: str

# Routes for comments
@router.post("/analysis/{analysis_id}/comments", response_model=CommentResponse)
async def add_comment(
    analysis_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to an analysis"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Check if analysis exists
    analysis = await db.get(Analysis, analysis_uuid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Create comment
    comment = Comment(
        id=uuid.uuid4(),
        analysis_id=analysis_uuid,
        user_id=current_user.id,
        content=comment_data.content
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return CommentResponse(
        id=str(comment.id),
        content=comment.content,
        user_name=current_user.full_name,
        created_at=comment.created_at.isoformat()
    )

@router.get("/analysis/{analysis_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all comments for an analysis"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Check permissions
    analysis = await db.get(Analysis, analysis_uuid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if current_user.role != UserRole.ADMIN and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these comments")
    
    # Get comments with user information
    result = await db.execute(
        select(Comment, User.full_name)
        .join(User)
        .where(Comment.analysis_id == analysis_uuid)
        .order_by(Comment.created_at.desc())
    )
    
    comments = result.all()
    
    return [
        CommentResponse(
            id=str(comment.id),
            content=comment.content,
            user_name=full_name,
            created_at=comment.created_at.isoformat()
        )
        for comment, full_name in comments
    ]

# Routes for decisions
@router.post("/analysis/{analysis_id}/decisions", response_model=DecisionResponse)
async def make_decision(
    analysis_id: str,
    decision_data: DecisionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Make a decision on an analysis"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Check if analysis exists and is completed
    analysis = await db.get(Analysis, analysis_uuid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if analysis.status.value != 'completed':
        raise HTTPException(status_code=400, detail="Analysis not yet completed")
    
    # Create decision
    decision = Decision(
        id=uuid.uuid4(),
        analysis_id=analysis_uuid,
        user_id=current_user.id,
        decision=Decision(decision_data.decision),
        reason=decision_data.reason
    )
    
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    
    return DecisionResponse(
        id=str(decision.id),
        decision=decision.decision.value,
        reason=decision.reason,
        user_name=current_user.full_name,
        created_at=decision.created_at.isoformat()
    )

@router.get("/analysis/{analysis_id}/decisions", response_model=List[DecisionResponse])
async def get_decisions(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all decisions for an analysis"""
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Check permissions
    analysis = await db.get(Analysis, analysis_uuid)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if current_user.role != UserRole.ADMIN and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these decisions")
    
    # Get decisions with user information
    result = await db.execute(
        select(Decision, User.full_name)
        .join(User)
        .where(Decision.analysis_id == analysis_uuid)
        .order_by(Decision.created_at.desc())
    )
    
    decisions = result.all()
    
    return [
        DecisionResponse(
            id=str(decision.id),
            decision=decision.decision.value,
            reason=decision.reason,
            user_name=full_name,
            created_at=decision.created_at.isoformat()
        )
        for decision, full_name in decisions
    ]