from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
import enum

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class AnalysisStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Verdict(enum.Enum):
    SAFE = "safe"
    NEEDS_REVIEW = "needs_review"
    HIGH_RISK = "high_risk"
    BLOCK = "block"
    MALICIOUS = "malicious"

class Decision(enum.Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    PENDING = "pending"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    decisions = relationship("Decision", back_populates="user")

class Extension(Base):
    __tablename__ = "extensions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(String(255), nullable=False, index=True)  # Extension ID from store
    store_type = Column(String(50), nullable=False)  # chrome, firefox, edge
    name = Column(String(500), nullable=False)
    developer_name = Column(String(255))
    developer_email = Column(String(255))
    developer_website = Column(String(500))
    verified_publisher = Column(Boolean, default=False)
    duns_number = Column(String(50))
    privacy_policy_url = Column(String(500))
    support_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    versions = relationship("ExtensionVersion", back_populates="extension")
    analyses = relationship("Analysis", back_populates="extension")

class ExtensionVersion(Base):
    __tablename__ = "extension_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extension_id = Column(UUID(as_uuid=True), ForeignKey("extensions.id"), nullable=False)
    version = Column(String(50), nullable=False)
    manifest_json = Column(JSON, nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    extension = relationship("Extension", back_populates="versions")
    analyses = relationship("Analysis", back_populates="version")

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extension_id = Column(UUID(as_uuid=True), ForeignKey("extensions.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("extension_versions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    
    # Scores (0-10 scale for each module)
    metadata_score = Column(Float, default=0.0)
    permissions_score = Column(Float, default=0.0)
    code_behavior_score = Column(Float, default=0.0)
    network_score = Column(Float, default=0.0)
    threat_intel_score = Column(Float, default=0.0)
    cve_score = Column(Float, default=0.0)
    ai_score = Column(Float, default=0.0)
    
    # Final calculated score (0-50)
    final_score = Column(Float, default=0.0)
    verdict = Column(Enum(Verdict))
    
    # Analysis data
    metadata_data = Column(JSON)
    permissions_data = Column(JSON)
    code_behavior_data = Column(JSON)
    network_data = Column(JSON)
    threat_intel_data = Column(JSON)
    cve_data = Column(JSON)
    ai_analysis = Column(JSON)
    
    # Bonuses and maluses
    bonuses = Column(JSON, default=dict)
    maluses = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    extension = relationship("Extension", back_populates="analyses")
    version = relationship("ExtensionVersion", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
    comments = relationship("Comment", back_populates="analysis")
    decisions = relationship("Decision", back_populates="analysis")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="comments")
    user = relationship("User", back_populates="comments")

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(Enum(Decision), nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis = relationship("Analysis", back_populates="decisions")
    user = relationship("User", back_populates="decisions")

class PermissionRiskMatrix(Base):
    __tablename__ = "permission_risk_matrix"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permission = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    category = Column(String(100))
    explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BehaviorPattern(Base):
    __tablename__ = "behavior_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    pattern = Column(String(500), nullable=False)  # Regex pattern
    category = Column(String(100), nullable=False)  # obfuscation, tracking, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text)
    examples = Column(JSON)  # Array of example matches
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False)  # virustotal, openai, etc.
    key_name = Column(String(255), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())