# AnAJu-Agent-Backend
FastAPI and Amazon Bedrock backend for the accessible collaboration agent
## Backend File Structure

```text
app/
├── __init__.py
├── analyzer.py
├── evidence.py
├── feedback.py
├── main.py
├── prompts.py
├── qa_agent.py
└── schemas.py
```
__init__.py
app 디렉터리를 Python 패키지로 인식하도록 하는 초기화 파일입니다.
현재 별도의 실행 로직은 포함하지 않으며, app.main, app.analyzer와 같이 모듈 간 import가 가능하도록 합니다.

main.py
FastAPI 애플리케이션의 진입점입니다.

schemas.py
API 요청·응답과 Agent 결과에 사용되는 Pydantic 데이터 모델을 정의합니다.

prompts.py
Amazon Bedrock에 전달할 시스템 프롬프트를 관리합니다.

analyzer.py
검토 완료된 STT·화자 데이터를 Semantic Meeting Document로 변환하는 1차 Agent 로직을 담당합니다.

qa_agent.py
사용자의 질문에 답변하는 2차 Agent 로직을 담당합니다.

evidence.py
AI가 선택한 근거 segment_id를 실제 STT 데이터의 문장·화자·timestamp와 연결합니다.
Agent가 timestamp를 직접 생성하지 않고, 다음처럼 근거 segment ID만 반환하도록 설계합니다.

feedback.py
사용자가 STT·화자 정보 또는 Semantic Meeting Document를 수정·확정하는 Human-in-the-loop 피드백 로직을 담당합니다.


<Module Dependency>
main.py
 ├── analyzer.py
 │    ├── prompts.py
 │    ├── schemas.py
 │    └── evidence.py
 │
 ├── qa_agent.py
 │    ├── prompts.py
 │    └── schemas.py
 │
 ├── feedback.py
 │    └── schemas.py
 │
 └── schemas.py

 
<Overall Backend Flow>
  
STT·화자 분리 결과
        ↓
사용자 1차 검토·수정
        ↓
main.py → analyzer.py
        ↓
Amazon Bedrock
        ↓
Semantic Meeting Document
        ↓
evidence.py
        ↓
근거 문장·화자·오디오 timestamp 연결
        ↓
사용자 2차 검토·수정
        ↓
feedback.py
        ↓
main.py → qa_agent.py
        ↓
사용자 질문에 대한 근거 기반 답변
