import json
import os
import re

import boto3
from dotenv import load_dotenv

from .schemas import (
    MeetingDocument,
    ReviewedTranscriptSegment,
)
from .prompts import ANALYZER_SYSTEM_PROMPT
from .evidence import attach_evidence


load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "amazon.nova-lite-v1:0",
)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


def build_segment_text(
    segments: list[ReviewedTranscriptSegment],
) -> str:
    return "\n".join(
        [
            (
                f"[segment_id={segment.segment_id}] "
                f"[speaker={segment.speaker}] "
                f"[start={segment.start_time}, "
                f"end={segment.end_time}]\n"
                f"{segment.text}"
            )
            for segment in segments
        ]
    )


def extract_json(text: str) -> dict:
    """
    Bedrock이 JSON 앞뒤에 설명이나 ```json을 붙이는 경우를 대비한다.
    """
    text = text.strip()

    # Markdown 코드블록 제거
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # JSON 객체의 시작과 끝만 추출
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            f"Bedrock 응답에서 JSON 객체를 찾지 못했습니다:\n{text}"
        )

    return json.loads(text[start:end + 1])


def call_bedrock(
    system_prompt: str,
    user_prompt: str,
) -> str:
    response = bedrock.converse(
        modelId=MODEL_ID,
        system=[
            {
                "text": system_prompt,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": user_prompt,
                    }
                ],
            }
        ],
        inferenceConfig={
            "maxTokens": 3000,
            "temperature": 0,
        },
    )

    return response["output"]["message"]["content"][0]["text"]

def normalize_document_data(
    data: dict,
    meeting_id: str,
) -> dict:
    """
    Bedrock이 반환한 JSON을 MeetingDocument Schema에 맞게 보정한다.
    """

    # meeting_id
    data["meeting_id"] = meeting_id

    # topics가 객체로 반환된 경우 리스트로 변환
    topics = data.get("topics", [])

    if isinstance(topics, dict):
        converted_topics = []

        for key, value in topics.items():
            if isinstance(value, dict):
                converted_topics.append({
                    "title": value.get("title", key),
                    "summary": value.get(
                        "summary",
                        value.get("요약", "")
                    ),
                    "children": value.get(
                        "children",
                        value.get("하위주제", [])
                    ),
                    "evidence_segment_ids": value.get(
                        "evidence_segment_ids",
                        []
                    ),
                })
            else:
                converted_topics.append({
                    "title": key,
                    "summary": str(value),
                    "children": [],
                    "evidence_segment_ids": [],
                })

        data["topics"] = converted_topics

    elif not isinstance(topics, list):
        data["topics"] = []

    # todo_list가 리스트가 아니면 빈 리스트 처리
    todo_list = data.get("todo_list", [])

    if not isinstance(todo_list, list):
        todo_list = []

    normalized_todos = []

    for index, todo in enumerate(todo_list, start=1):
        if not isinstance(todo, dict):
            continue

        review_status = todo.get("review_status")

        if review_status not in [
            "pending",
            "corrected",
            "confirmed",
        ]:
            review_status = "pending"

        normalized_todos.append({
            "todo_id": todo.get(
                "todo_id",
                f"todo_{index:03d}"
            ),
            "title": todo.get(
                "title",
                todo.get(
                    "task",
                    todo.get("업무", "확인 필요 업무")
                )
            ),
            "assignee": todo.get(
                "assignee",
                todo.get("담당자")
            ),
            "deadline": todo.get(
                "deadline",
                todo.get("마감일")
            ),
            "status": todo.get(
                "status",
                "미확정"
            ),
            "needs_confirmation": todo.get(
                "needs_confirmation",
                False
            ),
            "confirmation_reason": todo.get(
                "confirmation_reason"
            ),
            "evidence_segment_ids": todo.get(
                "evidence_segment_ids",
                []
            ),
            "review_status": review_status,
        })

    data["todo_list"] = normalized_todos

    # 필수 문자열 필드 보정
    data["summary"] = str(
        data.get("summary", "")
    )

    data["reviewed_source_version"] = str(
        data.get(
            "reviewed_source_version",
            "stt_review_v1"
        )
    )

    if data.get("review_status") not in [
        "pending",
        "corrected",
        "confirmed",
    ]:
        data["review_status"] = "pending"

    return data


def analyze_meeting(
    meeting_id: str,
    segments: list[ReviewedTranscriptSegment],
) -> MeetingDocument:
    transcript = build_segment_text(segments)

    user_prompt = f"""
    meeting_id: {meeting_id}

다음은 사용자가 1차 검토를 완료한 STT·화자 데이터다.

{transcript}

위 내용을 바탕으로 Semantic Meeting Document를 생성해줘.

반드시 아래 조건을 지켜:
- topics는 리스트로 반환
- todo_list 각 항목에는 todo_id와 title을 반드시 포함
- task라는 필드명 대신 title 사용
- reviewed_source_version은 "stt_review_v1"
- review_status는 "pending", "corrected", "confirmed" 중 하나
- evidence_segment_ids에는 실제 입력에 존재하는 segment_id만 사용
- timestamp는 직접 만들지 말고 segment_id만 반환
- JSON 객체만 반환
- JSON 외의 설명과 Markdown 코드블록은 금지
"""

    raw_text = call_bedrock(
        system_prompt=ANALYZER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    data = extract_json(raw_text)

    data = normalize_document_data(
        data=data,
        meeting_id=meeting_id,
    )

    document = MeetingDocument.model_validate(data)
    document.meeting_id = meeting_id

    for todo in document.todo_list:
        todo.evidence = attach_evidence(
            todo.evidence_segment_ids,
            segments,
        )

    return document
