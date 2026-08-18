from fastapi import FastAPI, HTTPException

from dotenv import load_dotenv

load_dotenv()  

from .schemas import (
    AnalyzeRequest,
    AskRequest,
    FeedbackResponse,
    DocumentFeedbackRequest,
    STTFeedbackRequest,
)
from .analyzer import analyze_meeting
from .qa_agent import answer_question


app = FastAPI(
    title="Accessible Collaboration Agent API",
    version="0.1.0",
)

# MVP에서는 메모리 저장으로 시작
meeting_store = {}
stt_feedback_store = []
document_feedback_store = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        document = analyze_meeting(
            meeting_id=request.meeting_id,
            segments=request.reviewed_segments,
        )

        meeting_store[request.meeting_id] = {
            "document": document,
            "segments": request.reviewed_segments,
        }

        return document.model_dump()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"문서 생성 중 오류가 발생했습니다: {str(error)}",
        )


@app.post("/ask")
def ask(request: AskRequest):
    meeting = meeting_store.get(request.meeting_id)

    if meeting is None:
        raise HTTPException(
            status_code=404,
            detail="해당 회의의 분석 결과가 없습니다.",
        )

    try:
        result = answer_question(
            document=meeting["document"],
            segments=meeting["segments"],
            question=request.question,
            user_name=request.user_name,
        )

        return result.model_dump()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"질문 응답 중 오류가 발생했습니다: {str(error)}",
        )


@app.post("/stt-feedback", response_model=FeedbackResponse)
def stt_feedback(request: STTFeedbackRequest):
    stt_feedback_store.append(request.model_dump())

    return FeedbackResponse(
        status="received",
        meeting_id=request.meeting_id,
        target_id=request.segment_id,
        message="STT·화자 수정 내용이 접수되었습니다.",
    )


@app.post("/document-feedback", response_model=FeedbackResponse)
def document_feedback(request: DocumentFeedbackRequest):
    document_feedback_store.append(request.model_dump())

    meeting = meeting_store.get(request.meeting_id)

    if meeting is not None:
        document = meeting["document"]

        if request.target_type == "todo":
            for todo in document.todo_list:
                if todo.todo_id == request.target_id:
                    if request.field == "title":
                        todo.title = request.corrected_value or todo.title
                    elif request.field == "assignee":
                        todo.assignee = request.corrected_value
                    elif request.field == "deadline":
                        todo.deadline = request.corrected_value

                    todo.review_status = "confirmed"

        elif request.target_type == "summary":
            if request.field == "summary":
                document.summary = request.corrected_value or document.summary
                document.review_status = "confirmed"

    return FeedbackResponse(
        status="received",
        meeting_id=request.meeting_id,
        target_id=request.target_id,
        message="Semantic Meeting Document 수정 내용이 반영되었습니다.",
    )
