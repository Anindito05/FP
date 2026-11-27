"""ORM tables for the wellness backend."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, LargeBinary, String, Text, Float, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from .database import Base

class TimestampMixin:
    id = __import__('sqlalchemy').Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = __import__('sqlalchemy').Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class User(TimestampMixin, Base):
    __tablename__ = "users"
    email = __import__('sqlalchemy').Column(String(320), nullable=True)
    password_hash = __import__('sqlalchemy').Column(String(512), nullable=True)
    display_name = __import__('sqlalchemy').Column(String(120), nullable=True)
    role = __import__('sqlalchemy').Column(String(20), nullable=False, server_default="user")
    is_guest = __import__('sqlalchemy').Column(Boolean, nullable=False, server_default=text("false"))
    is_active = __import__('sqlalchemy').Column(Boolean, nullable=False, server_default=text("true"))
    region_code = __import__('sqlalchemy').Column(String(8), nullable=True)
    locale = __import__('sqlalchemy').Column(String(16), nullable=False, server_default="en")
    last_login_at = __import__('sqlalchemy').Column(DateTime(timezone=True))
    deleted_at = __import__('sqlalchemy').Column(DateTime(timezone=True))
    __table_args__ = (Index("uq_users_email_lower", func.lower(email), unique=True, postgresql_where=email.is_not(None)),)

class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"
    user_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    family_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = __import__('sqlalchemy').Column(String(64), nullable=False, unique=True)
    expires_at = __import__('sqlalchemy').Column(DateTime(timezone=True), nullable=False)
    revoked_at = __import__('sqlalchemy').Column(DateTime(timezone=True))
    replaced_by = __import__('sqlalchemy').Column(UUID(as_uuid=True))

class ChatSession(TimestampMixin, Base):
    __tablename__ = "chat_sessions"
    user_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = __import__('sqlalchemy').Column(String(200))
    status = __import__('sqlalchemy').Column(String(20), nullable=False, server_default="active")
    mode = __import__('sqlalchemy').Column(String(20), nullable=False, server_default="text")
    started_at = __import__('sqlalchemy').Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = __import__('sqlalchemy').Column(DateTime(timezone=True))
    risk_peak_level = __import__('sqlalchemy').Column(String(20), nullable=False, server_default="none")
    message_count = __import__('sqlalchemy').Column(Integer, nullable=False, server_default="0")
    __table_args__ = (Index("ix_sessions_user_started", "user_id", "started_at"),)

class Message(TimestampMixin, Base):
    __tablename__ = "messages"
    session_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = __import__('sqlalchemy').Column(String(20), nullable=False)
    content_enc = __import__('sqlalchemy').Column(LargeBinary, nullable=False)
    turn_index = __import__('sqlalchemy').Column(Integer, nullable=False)
    route = __import__('sqlalchemy').Column(String(20))
    client_msg_id = __import__('sqlalchemy').Column(String(128))
    latency_ms = __import__('sqlalchemy').Column(Integer)
    __table_args__ = (UniqueConstraint("session_id", "client_msg_id", name="uq_message_client_id"), Index("ix_messages_session_turn", "session_id", "turn_index"))

class MessageAnalysis(TimestampMixin, Base):
    __tablename__ = "message_analysis"
    message_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    emotion_label = __import__('sqlalchemy').Column(String(40))
    emotion_scores = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="{}")
    intent_label = __import__('sqlalchemy').Column(String(40))
    risk_score = __import__('sqlalchemy').Column(Float, nullable=False, server_default="0")
    risk_level = __import__('sqlalchemy').Column(String(20), nullable=False, server_default="none", index=True)
    risk_source = __import__('sqlalchemy').Column(String(30))
    keyword_hits = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="[]")
    model_versions = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="{}")
    prompt_versions = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="{}")

class RiskEvent(TimestampMixin, Base):
    __tablename__ = "risk_events"
    session_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    message_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    risk_level = __import__('sqlalchemy').Column(String(20), nullable=False)
    action_taken = __import__('sqlalchemy').Column(String(80), nullable=False)
    user_accepted_help = __import__('sqlalchemy').Column(Boolean)
    reviewed_by = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("users.id"))
    review_label = __import__('sqlalchemy').Column(String(30))
    __table_args__ = (Index("ix_risk_events_unreviewed", "created_at", postgresql_where=text("reviewed_by IS NULL")),)

class Consent(TimestampMixin, Base):
    __tablename__ = "consents"
    user_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = __import__('sqlalchemy').Column(String(40), nullable=False)
    granted = __import__('sqlalchemy').Column(Boolean, nullable=False)
    version = __import__('sqlalchemy').Column(String(40), nullable=False)
    granted_at = __import__('sqlalchemy').Column(DateTime(timezone=True))
    revoked_at = __import__('sqlalchemy').Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("user_id", "type", "version"),)

class HelpSearchCache(TimestampMixin, Base):
    __tablename__ = "help_search_cache"
    query_key = __import__('sqlalchemy').Column(String(64), nullable=False, unique=True)
    results = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="[]")
    fetched_at = __import__('sqlalchemy').Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Feedback(TimestampMixin, Base):
    __tablename__ = "feedback"
    message_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = __import__('sqlalchemy').Column(Integer, nullable=False)
    helpful = __import__('sqlalchemy').Column(Boolean)
    comment = __import__('sqlalchemy').Column(Text)

class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"
    actor_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = __import__('sqlalchemy').Column(String(100), nullable=False)
    entity = __import__('sqlalchemy').Column(String(100), nullable=False)
    entity_id = __import__('sqlalchemy').Column(UUID(as_uuid=True))
    metadata_json = __import__('sqlalchemy').Column("metadata", JSONB, nullable=False, server_default="{}")

class EvalRun(TimestampMixin, Base):
    __tablename__ = "eval_runs"
    name = __import__('sqlalchemy').Column(String(200), nullable=False)
    dataset = __import__('sqlalchemy').Column(String(500), nullable=False)
    git_sha = __import__('sqlalchemy').Column(String(80))
    model_versions = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="{}")
    recall = __import__('sqlalchemy').Column(Float)
    precision = __import__('sqlalchemy').Column(Float)
    f2 = __import__('sqlalchemy').Column(Float)
    fnr = __import__('sqlalchemy').Column(Float)
    groundedness = __import__('sqlalchemy').Column(Float)
    latency_p95_ms = __import__('sqlalchemy').Column(Float)

class MoodState(TimestampMixin, Base):
    __tablename__ = "mood_states"
    session_id = __import__('sqlalchemy').Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_index = __import__('sqlalchemy').Column(Integer, nullable=False)
    level = __import__('sqlalchemy').Column(Integer, nullable=False)
    instant_level = __import__('sqlalchemy').Column(Integer, nullable=False)
    mood_vector = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="{}")
    emotion_top = __import__('sqlalchemy').Column(String(40), nullable=False)
    trend = __import__('sqlalchemy').Column(String(20), nullable=False)
    shift_flag = __import__('sqlalchemy').Column(String(20))
    index_version = __import__('sqlalchemy').Column(String(100))
    __table_args__ = (UniqueConstraint("session_id", "turn_index", name="uq_mood_session_turn"),)

class IndexManifest(TimestampMixin, Base):
    __tablename__ = "index_manifest"
    version = __import__('sqlalchemy').Column(String(100), nullable=False, unique=True)
    manifest = __import__('sqlalchemy').Column(JSONB, nullable=False, server_default="{}")

class DatasetRegistry(TimestampMixin, Base):
    __tablename__ = "dataset_registry"
    dataset_id = __import__('sqlalchemy').Column(String(100), nullable=False, unique=True)
    validity_tier = __import__('sqlalchemy').Column(String(1), nullable=False)
    enabled = __import__('sqlalchemy').Column(Boolean, nullable=False, server_default=text("false"))
    verified_by_human = __import__('sqlalchemy').Column(Boolean, nullable=False, server_default=text("false"))
    metadata_json = __import__('sqlalchemy').Column("metadata", JSONB, nullable=False, server_default="{}")

for _name, _type, _default in (("emotion_dist",JSONB,"{}"),("level_dist",JSONB,"{}"),("instant_level",Integer,"0"),("level",Integer,"0"),("confidence",Float,"0"),("novelty",Float,"1"),("classifier_mode",String(30),"degraded"),("index_version",String(100),None),("prompt_version",String(100),None)):
    setattr(MessageAnalysis,_name,__import__('sqlalchemy').Column(_type,nullable=_default is not None,server_default=str(_default) if _default is not None else None))
