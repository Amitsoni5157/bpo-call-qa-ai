from  pydantic import BaseModel, Field
from typing import List, Literal

class QAComplianceAudit(BaseModel):
    call_id: str = Field(description="Unique call identification string")
    customer_sentiment: Literal["Positive", "Neutral", "Negative"] = Field(
        description="Overall customer tone by the end of the call"
    )
    primary_issue: str =Field(
        description="Core problem or query reported by the customer"
    )
    agent_professionalism_score: int = Field(
        ge=1, le=10,
        description="Agent rating on a scale of 1 to 10"
    )
    mandatory_greeting_done: bool = Field(
        description="Did the agent follow standard company greeting protocols?"
    )
    solution_provided: str =Field(
        description="Specific resolution or next steps offered by the agent"
    )
    compliance_score_percentage: float = Field(
        ge = 0.0, le=100.0,
        description="Total percentage compliance based on QA audit checklist"
    )
    requires_human_review: bool = Field(
        default=False, 
        description="Triggered when AI confidence/compliance falls below threshold"
    )
    audit_notes: List[str] = Field(
        default_factory=list, 
        description="Key observations, policy violations, or coaching remarks"
    )
    
class AuditRequestResponse(BaseModel):
    status: str
    message: str
    data: QAComplianceAudit