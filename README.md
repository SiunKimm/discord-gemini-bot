# discord-gemini-bot

Discord 슬래시 커맨드 기반 봇입니다. 주사위, 현재 시간, Gemini 질의, 사용자 대화 분석 기능을 제공합니다.

## 실행 방법

1. 의존성 설치

```bash
pip install -U discord.py google-generativeai python-dotenv
```

2. 환경변수 설정

`.env` 파일에 아래 값을 설정합니다.

```env
DISCORD_BOT_TOKEN=...
GEMINI_API_KEY=...
# 선택값
GEMINI_MODEL_NAME=gemma-3-27b-it
```

3. 봇 실행

```bash
python bot.py
```

## 구조

- `bot.py`: 봇 초기화 및 Cog 동적 로딩
- `cogs/`: 슬래시 커맨드 구현
- `config/settings.py`: 환경변수 및 공통 설정
- `utils/gemini_wrapper.py`: Gemini 비동기 호출 래퍼
- `utils/text_utils.py`: Discord 메시지 길이 분할 유틸

## 리팩터링 포인트

- Cog 로딩을 스펙 기반 반복문으로 통일
- 필수 환경변수 검증 추가
- Gemini 응답 전송 로직의 텍스트 분할 공통화
- 사용자 분석 Cog를 메서드 단위로 분리해 가독성 및 유지보수성 개선

## 테스트

```bash
python -m unittest discover -s tests -v
```

## 로깅

- 표준 출력 대신 Python `logging` 기반으로 실행 로그를 출력합니다.
- Cog 로딩 실패, Gemini 타임아웃/오류, 채널 메시지 수집 실패를 로그로 남깁니다.
