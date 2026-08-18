Accessible Collaboration Agent API Specification
1. API 개요
Base URL
text

http://13.209.41.10:8000
EC2를 재시작하면 Public IPv4가 변경될 수 있으므로, 실제 연동 시 최신 주소를 확인한다.
Swagger 문서
text

http://13.209.41.10:8000/docs
기술 스택
FastAPI
Amazon Bedrock Converse API
Pydantic
AWS EC2
Python
2. 전체 처리 흐름
text

STT·화자 분리 결과
        ↓
사용자 1차 검토·수정
        ↓
POST /analyze
        ↓
Semantic Meeting Document 생성
        ↓
사용자 2차 검토·수정
        ↓
POST /document-feedback
        ↓
POST /ask
        ↓
사용자 질문에 대한 근거 기반 답변
        ↓
evidence의 start_time으로 원본 오디오 이동
3. 공통 데이터 규칙
ID 규칙
회의 ID
text

meeting_001
STT segment ID
text

seg_001
seg_002
TO-DO ID
text

todo_001
todo_002
검토 상태
text

pending
아직 사용자 검토 전
text

corrected
사용자가 수정함
text

confirmed
사용자가 최종 확정함
Source-Linked 규칙
Agent는 timestamp를 직접 만들지 않는다.
Agent는 근거가 되는 segment_id만 반환한다.
json

{
  "evidence_segment_ids": ["seg_002"]
}
서버가 실제 STT 데이터에서 해당 segment를 조회하여 다음 정보를 붙인다.
json

{
  "segment_id": "seg_002",
  "quote": "서경님은 AI가 회의 내용을 분석하는 부분을 맡아주세요.",
  "speaker": "speaker_2",
  "start_time": 5.1,
  "end_time": 12.0
}
iOS에서는 start_time을 사용하여 AVPlayer.seek를 실행한다.
4. GET /health
목적
서버가 정상적으로 실행 중인지 확인한다.
Request
GET /health
Response
Status: 200 OK
json

{
  "status": "ok"
}
이 API는 AI 분석을 실행하지 않고, 서버 연결 상태만 확인한다.
5. POST /analyze
목적
사용자가 1차 검토를 완료한 STT·화자 데이터를 바탕으로 Semantic Meeting Document를 생성한다.
처리 내용
text

검토 완료 STT segments
→ Bedrock 분석
→ 대주제·중주제·소주제 생성
→ 회의 요약 생성
→ 사용자 TO-DO 추출
→ 근거 segment와 timestamp 연결
Request
POST /analyze
Content-Type: application/json
json

{
  "meeting_id": "meeting_001",
  "reviewed_segments": [
    {
      "segment_id": "seg_001",
      "text": "이번 과제의 주제는 시각장애 대학생의 협업 지원 시스템으로 정하겠습니다.",
      "speaker": "speaker_1",
      "start_time": 0.0,
      "end_time": 5.0,
      "original_text": "이번 과제의 주제는 시각장애 대학생의 협업 지원 시스템으로 정하겠습니다.",
      "original_speaker": "speaker_1",
      "review_status": "confirmed",
      "user_edited": false
    },
    {
      "segment_id": "seg_002",
      "text": "서경님은 AI가 회의 내용을 분석하고 사용자 역할을 정리하는 부분을 맡아주세요.",
      "speaker": "서경",
      "start_time": 5.1,
      "end_time": 12.0,
      "original_text": "서경님은 AI가 회의 내용을 분석하고 사용자 역할을 정리하는 부분을 맡아주세요.",
      "original_speaker": "speaker_2",
      "review_status": "corrected",
      "user_edited": true
    }
  ]
}
Request 필드
필드	타입	필수	설명
meeting_id	String	O	회의 식별자
reviewed_segments	Array	O	사용자 검토가 완료된 STT 목록
segment_id	String	O	STT 문장 식별자
text	String	O	현재 확정된 문장
speaker	String/null	X	현재 확정된 화자
start_time	Float/null	X	오디오 시작 시간, 초 단위
end_time	Float/null	X	오디오 종료 시간, 초 단위
original_text	String/null	X	수정 전 STT 문장
original_speaker	String/null	X	수정 전 화자
review_status	String	O	pending, corrected, confirmed
user_edited	Boolean	O	사용자 수정 여부
Response
Status: 200 OK
json

{
  "meeting_id": "meeting_001",
  "topics": [
    {
      "title": "프로젝트 주제",
      "summary": "시각장애 대학생의 협업 지원 시스템을 논의함",
      "children": [
        {
          "title": "AI 분석 기능",
          "summary": "회의 내용을 분석해 사용자의 역할을 정리함",
          "children": [],
          "evidence_segment_ids": [
            "seg_002"
          ]
        }
      ],
      "evidence_segment_ids": [
        "seg_001",
        "seg_002"
      ]
    }
  ],
  "summary": "시각장애 대학생의 협업을 지원하기 위한 AI 시스템의 기능과 역할을 논의함.",
  "todo_list": [
    {
      "todo_id": "todo_001",
      "title": "AI 회의 내용 분석 기능 구현",
      "assignee": "서경",
      "deadline": null,
      "status": "미확정",
      "needs_confirmation": true,
      "confirmation_reason": "구체적인 마감일이 확정되지 않음",
      "evidence_segment_ids": [
        "seg_002"
      ],
      "evidence": [
        {
          "segment_id": "seg_002",
          "quote": "서경님은 AI가 회의 내용을 분석하고 사용자 역할을 정리하는 부분을 맡아주세요.",
          "speaker": "서경",
          "start_time": 5.1,
          "end_time": 12.0
        }
      ],
      "review_status": "pending"
    }
  ],
  "reviewed_source_version": "stt_review_v1",
  "review_status": "pending"
}
iOS 표시 규칙
topics
대주제 버튼
중주제·소주제 하위 버튼
VoiceOver가 계층 순서대로 읽도록 구성
summary
회의 전체 요약 화면에 표시
todo_list
각 TO-DO 카드에 다음을 표시한다.
업무 제목
담당자
마감일
상태
확인 필요 여부
근거 듣기 버튼
needs_confirmation
true이면 다음과 같이 표시한다.
text

확인이 필요한 업무입니다.
6. POST /stt-feedback
목적
사용자가 STT 문장이나 화자를 수정했음을 서버에 전달한다.
Request
POST /stt-feedback
Content-Type: application/json
json

{
  "meeting_id": "meeting_001",
  "segment_id": "seg_002",
  "reviewed_text": "서경님은 AI가 회의 내용을 분석하고 사용자 역할을 정리하는 부분을 맡아주세요.",
  "reviewed_speaker": "서경",
  "review_status": "confirmed"
}
Request 필드
필드	타입	필수	설명
meeting_id	String	O	회의 식별자
segment_id	String	O	수정할 STT 문장 ID
reviewed_text	String/null	X	사용자가 수정한 문장
reviewed_speaker	String/null	X	사용자가 수정한 화자
review_status	String	O	pending, corrected, confirmed
Response
json

{
  "status": "received",
  "meeting_id": "meeting_001",
  "target_id": "seg_002",
  "message": "STT·화자 수정 내용이 접수되었습니다."
}
iOS 처리 흐름
text

STT 문장 수정
→ 저장 또는 확정 버튼 클릭
→ /stt-feedback 호출
→ 수정 완료 표시
→ /analyze 재호출
주의
사용자가 문장이나 화자를 수정해도 다음 값은 유지해야 한다.
text

segment_id
start_time
end_time
그래야 수정된 문장도 원본 오디오 위치와 연결될 수 있다.
7. POST /document-feedback
목적
Semantic Meeting Document 생성 이후 사용자가 요약·TO-DO를 수정하거나 확정한다.
Request
POST /document-feedback
Content-Type: application/json
TO-DO 마감일 수정 예시
json

{
  "meeting_id": "meeting_001",
  "target_type": "todo",
  "target_id": "todo_001",
  "field": "deadline",
  "original_value": null,
  "corrected_value": "8월 17일",
  "review_status": "confirmed"
}
TO-DO 담당자 수정 예시
json

{
  "meeting_id": "meeting_001",
  "target_type": "todo",
  "target_id": "todo_001",
  "field": "assignee",
  "original_value": "서경",
  "corrected_value": "지원",
  "review_status": "confirmed"
}
요약 수정 예시
json

{
  "meeting_id": "meeting_001",
  "target_type": "summary",
  "target_id": null,
  "field": "summary",
  "original_value": "기존 요약",
  "corrected_value": "사용자가 수정한 회의 요약",
  "review_status": "confirmed"
}
Request 필드
필드	타입	필수	설명
meeting_id	String	O	회의 식별자
target_type	String	O	topic, summary, todo
target_id	String/null	조건부	수정 대상 ID
field	String	O	수정할 필드명
original_value	String/null	X	기존 값
corrected_value	String/null	X	사용자 수정값
review_status	String	O	pending, corrected, confirmed
Response
json

{
  "status": "received",
  "meeting_id": "meeting_001",
  "target_id": "todo_001",
  "message": "Semantic Meeting Document 수정 내용이 반영되었습니다."
}
지원이 구현할 편집 항목
MVP에서는 우선 다음 세 가지를 편집 가능하게 하면 돼.
TO-DO 제목
담당자
마감일
8. POST /ask
목적
사용자의 질문에 대해 검토·수정된 Semantic Meeting Document와 원문 근거를 기반으로 답변한다.
전제
반드시 먼저 /analyze가 성공해야 한다.
Request
POST /ask
Content-Type: application/json
json

{
  "meeting_id": "meeting_001",
  "question": "내 역할과 다음 회의 전까지 해야 할 일을 알려줘.",
  "user_name": "서경"
}
Request 필드
필드	타입	필수	설명
meeting_id	String	O	회의 식별자
question	String	O	사용자 질문
user_name	String/null	X	질문한 사용자 이름
질문 예시
text

내 역할은 뭐야?
내가 해야 할 일은 뭐야?
마감일이 언제야?
아직 정해지지 않은 내용은 뭐야?
조원에게 무엇을 확인해야 해?
다음 회의 전까지 뭘 해야 해?
Response
json

{
  "answer": "서경님은 AI가 회의 내용을 분석하고 사용자 역할을 정리하는 부분을 맡았습니다. 다음 회의 전까지 기본 Agent 결과 구조를 확인해야 합니다.",
  "related_todo_ids": [
    "todo_001"
  ],
  "evidence_segment_ids": [
    "seg_002"
  ],
  "suggested_questions": [
    "구체적인 마감일은 언제인가요?"
  ],
  "suggested_next_actions": [
    "기본 Agent 결과 구조를 확정하세요."
  ],
  "needs_confirmation": true
}
iOS 표시 규칙
answer: 답변 본문
related_todo_ids: 관련 업무 카드 연결
suggested_questions: 추가로 확인할 질문
suggested_next_actions: 다음 행동
needs_confirmation: true: 답변을 확정하기 전 원문 확인 안내
9. 오류 응답
분석 결과가 없는 회의
Status: 404 Not Found
json

{
  "detail": "해당 회의의 분석 결과가 없습니다."
}
Bedrock 분석 오류
Status: 500 Internal Server Error
json

{
  "detail": "문서 생성 중 오류가 발생했습니다."
}
주요 오류 원인
Bedrock 권한 오류
잘못된 모델 ID
잘못된 AWS 리전
요청 JSON 형식 오류
Pydantic Schema 검증 실패
