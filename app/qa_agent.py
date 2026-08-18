import json
import os
import re

import boto3
from dotenv import load_dotenv

from .schemas import (
    AskResponse,
    MeetingDocument,
    ReviewedTranscriptSegment,
)
from .prompts import QA_SYSTEM_PROMPT


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


def extract_json(text: str) -> dict:
    text = text.strip()

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

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
            "maxTokens": 2000,
            "temperature": 0,
        },
    )

    return response["output"]["message"]["content"][0]["text"]


def answer_question(
    document: MeetingDocument,
    segments: list[ReviewedTranscriptSegment],
    question: str,
    user_name: str | None = None,
) -> AskResponse:
    document_json = document.model_dump_json(indent=2)

    source_text = "\n".join(
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

    user_prompt = f"""
사용자 이름:
{user_name or "알 수 없음"}

검토 완료된 Semantic Meeting Document:
{document_json}

검토 완료된 원문 근거:
{source_text}

사용자 질문:
{question}

문서와 원문 근거에 있는 정보만 사용해서 답변해.
정보가 없거나 충돌하면 needs_confirmation을 true로 설정해.

반드시 JSON 객체만 반환해.
JSON 앞뒤에 설명을 붙이지 마.
Markdown 코드블록도 사용하지 마.
"""

    raw_text = call_bedrock(
        system_prompt=QA_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    data = extract_json(raw_text)

    return AskResponse.model_validate(data)
