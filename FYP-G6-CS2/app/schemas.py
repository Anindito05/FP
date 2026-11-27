"""Validated API contracts."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    display_name: str = Field(min_length=1, max_length=120)
    region_code: str | None = None
    accepted_terms: bool
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
class GuestRequest(BaseModel):
    region_code: str | None = None
    accepted_terms: bool
class RefreshRequest(BaseModel): refresh_token: str
class TokenPair(BaseModel): access_token: str; refresh_token: str; token_type: str = "bearer"; expires_in: int
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id: UUID; email: str | None; display_name: str | None; role: str; is_guest: bool; region_code: str | None
class SessionCreate(BaseModel): title: str | None = None; mode: str = "text"
class SessionOut(BaseModel): model_config=ConfigDict(from_attributes=True); id: UUID; title: str | None; status: str; started_at: datetime; message_count: int
class MessageIn(BaseModel): content: str = Field(min_length=1, max_length=2000); client_msg_id: str = Field(min_length=1, max_length=128)
class EscalationOffer(BaseModel): offer_id: UUID; text: str; options: list[str]
class MessageOut(BaseModel): id: UUID; role: str = "assistant"; content: str; route: str; emotion: str | None = None; escalation_offer: EscalationOffer | None = None; created_at: datetime | None = None; level: int | None = None; trend: str | None = None; shift_flag: str | None = None; classifier_mode: str | None = None
class EscalationResponse(BaseModel): offer_id: UUID; choice: str; country: str | None = None; region: str | None = None; city: str | None = None
class HelplineOut(BaseModel): name: str; phone: str | None = None; url: str | None = None; source_url: str | None = None; hours: str | None = None; languages: list[str] = []; please_verify: str | None = None
class NearbyServiceOut(BaseModel): name: str; phone: str | None = None; url: str | None = None; source_url: str | None = None; hours: str | None = None; languages: list[str] = []; please_verify: str | None = None
class ConsentIn(BaseModel): type: str; granted: bool; version: str
class ConsentOut(BaseModel): type: str; granted: bool; version: str; updated_at: datetime | None = None
class FeedbackIn(BaseModel): message_id: UUID; rating: int = Field(ge=1, le=5); helpful: bool | None = None; comment: str | None = Field(default=None, max_length=1000)
class RiskEventOut(BaseModel): model_config=ConfigDict(from_attributes=True); id: UUID; risk_level: str; action_taken: str; review_label: str | None; created_at: datetime
class RiskReviewIn(BaseModel): review_label: str
class MetricsOut(BaseModel): risk_recall: float | None = None; fnr: float | None = None; avg_latency_ms: float | None = None; escalation_rate: float | None = None; groundedness: float | None = None
class ErrorEnvelope(BaseModel): code: str; message: str; request_id: str | None = None

class ORMModel(BaseModel): model_config = ConfigDict(from_attributes=True)
