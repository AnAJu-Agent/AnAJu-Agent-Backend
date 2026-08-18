from typing import List, Optional, Literal
from pydantic import BaseModel, Field


ReviewStatus = Literal["pending", "corrected", "confirmed"]


class TranscriptSegment(BaseModel):
    segment_id: str
    text: str
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ReviewedTranscriptSegment(TranscriptSegment):
    original_text: Optional[str] = None
    original_speaker: Optional[str] = None
    review_status: ReviewStatus = "pending"
    user_edited: bool = False


class Evidence(BaseModel):
    segment_id: str
    quote: str
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class TopicNode(BaseModel):
    title: str
    summary: str
    children: List["TopicNode"] = Field(default_factory=list)
    evidence_segment_ids: List[str] = Field(default_factory=list)


class TodoItem(BaseModel):
    todo_id: str
    title: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "미확정"
    needs_confirmation: bool = False
    confirmation_reason: Optional[str] = None
    evidence_segment_ids: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    review_status: ReviewStatus = "pending"


class MeetingDocument(BaseModel):
    meeting_id: str
    topics: List[TopicNode] = Field(default_factory=list)
    summary: str
    todo_list: List[TodoItem] = Field(default_factory=list)
    reviewed_source_version: str = "stt_review_v1"
    review_status: ReviewStatus = "pending"


class AnalyzeRequest(BaseModel):
    meeting_id: str
    reviewed_segments: List[ReviewedTranscriptSegment]


class AskRequest(BaseModel):
    meeting_id: str
    question: str
    user_name: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    related_todo_ids: List[str] = Field(default_factory=list)
    evidence_segment_ids: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    suggested_next_actions: List[str] = Field(default_factory=list)
    needs_confirmation: bool = False


class STTFeedbackRequest(BaseModel):
    meeting_id: str
    segment_id: str
    reviewed_text: Optional[str] = None
    reviewed_speaker: Optional[str] = None
    review_status: ReviewStatus = "confirmed"


class DocumentFeedbackRequest(BaseModel):
    meeting_id: str
    target_type: Literal["topic", "summary", "todo"]
    target_id: Optional[str] = None
    field: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    review_status: ReviewStatus = "confirmed"


class FeedbackResponse(BaseModel):
    status: str
    meeting_id: str
    target_id: Optional[str] = None
    message: str


TopicNode.model_rebuild()
