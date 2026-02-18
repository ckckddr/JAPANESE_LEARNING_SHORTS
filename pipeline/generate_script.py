"""
Gemini API로 여행업 비즈니스 일본어 대화 스크립트 생성
"""
import json
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)


def _pick_knowledge(knowledge: dict, situation: dict) -> dict:
    """상황에 맞는 문법/어휘를 지식베이스에서 랜덤 선택"""
    level = situation.get("difficulty", "N2")

    # 레벨에 맞는 문법 선택
    grammar_pool = knowledge.get(level.lower(), {}).get("grammar", [])
    if not grammar_pool:
        # 레벨 없으면 N2 폴백
        grammar_pool = knowledge.get("n2", {}).get("grammar", [])

    selected_grammar = random.sample(grammar_pool, min(3, len(grammar_pool)))

    # 한자에서 여행 관련 단어 선택
    kanji_pool = knowledge.get("kanji", [])
    if isinstance(kanji_pool, list):
        selected_kanji = random.sample(kanji_pool, min(5, len(kanji_pool)))
    else:
        selected_kanji = []

    return {"grammar": selected_grammar, "kanji": selected_kanji}


def generate_script(situation: dict, knowledge: dict) -> dict:
    """
    Gemini API로 대화 스크립트 생성
    """
    picked = _pick_knowledge(knowledge, situation)
    grammar_info = json.dumps(picked["grammar"], ensure_ascii=False, indent=2)
    kanji_info = json.dumps(picked["kanji"][:5], ensure_ascii=False, indent=2)

    ep_type = situation.get("type", "B2B")
    situation_text = situation.get("situation", "")
    channel = situation.get("channel", "電話")
    difficulty = situation.get("difficulty", "N2")

    if ep_type == "B2B":
        speakers = "旅行会社の担当者（田中）と ホ테ルの営業担当（山田）"
        context = "도매사(ホテル)와 여행사 간의 비즈니스 대화"
    else:
        speakers = "旅行会社のスタッフ（佐藤）と お客様（김민준）"
        context = "여행사 직원과 고객 간의 서비스 대화"

    prompt = f"""당신은 여행업 비즈니스 일본어 교육 콘텐츠 전문가입니다.
아래 조건에 맞는 학습용 대화 스크립트를 생성해주세요.

## 상황
- 타입: {ep_type} ({context})
- 상황: {situation_text}
- 채널: {channel}
- 난이도: JLPT {difficulty}
- 화자: {speakers}

## 사용할 문법 (최소 2개 이상 자연스럽게 포함)
{grammar_info}

## 참고 한자/어휘
{kanji_info}

## 요구사항
1. 전체 영상 길이는 3분(180초) 이내로 구성 (대사 5~8 라인 필수)
2. 각 라인은 자연스럽고 매우 간결한 비즈니스 일본어
3. 문법 포인트가 실제 대화에서 자연스럽게 사용될 것
4. 여행업 실무 용어 포함
5. 한국어 번역 포함

## 출력 형식 (JSON만 반환)
{{
  "episode_title": "에피소드 제목 (일본어, 20자 이내)",
  "situation": {{
    "type": "{ep_type}",
    "situation": "{situation_text}",
    "channel": "{channel}",
    "difficulty": "{difficulty}"
  }},
  "intro_narration": "에피소드 소개 나레이션 (일본어, 2~3문장)",
  "intro_narration_ko": "나레이션 한국어 번역",
  "dialogue": [
    {{
      "speaker": "화자 이름",
      "role": "役職 (예: 旅行会社担当者)",
      "text_jp": "일본어 대사",
      "text_ko": "한국어 번역",
      "audio_note": "TTS 읽기 속도 힌트 (normal/slow/emphasis)"
    }}
  ],
  "grammar_explanation": [
    {{
      "form": "문법 형태",
      "meaning_ko": "의미",
      "example_jp": "예문",
      "example_ko": "번역",
      "usage_note": "사용 포인트"
    }}
  ],
  "used_grammar": [
    {{"form": "문법 형태", "meaning_ko": "의미", "example_jp": "예문", "example_ko": "번역"}}
  ],
  "used_vocab": [
    {{"word": "단어", "reading": "읽기", "meaning_ko": "의미"}}
  ],
  "summary": "에피소드 요약 (한국어, 2~3문장)"
}}"""

    try:
        resp = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        text_content = resp.text.strip()
        if text_content.startswith("```"):
            text_content = text_content.split("```")[1]
            if text_content.startswith("json"):
                text_content = text_content[4:]
        script = json.loads(text_content)
        return script
    except Exception as e:
        print(f"  [오류] 스크립트 생성 실패: {e}")
        # 폴백 스크립트
        return {
            "episode_title": f"ビジネス日本語 {ep_type}",
            "situation": situation,
            "intro_narration": f"今日は{situation_text}についての会話를 배워봅시다.",
            "intro_narration_ko": f"오늘은 {situation_text}에 대한 대화를 배워봅시다.",
            "dialogue": [
                {
                    "speaker": "田中",
                    "role": "旅行会社担当者",
                    "text_jp": "お世話になっております。",
                    "text_ko": "항상 신세 지고 있습니다.",
                    "audio_note": "normal"
                }
            ],
            "grammar_explanation": [],
            "used_grammar": picked["grammar"][:2],
            "used_vocab": [],
            "key_sentences": [],
            "summary": f"{situation_text} 상황의 비즈니스 일본어 대화입니다."
        }


if __name__ == "__main__":
    # 테스트
    test_situation = {
        "type": "B2B",
        "situation": "ホテルの団体予約와 料金交渉",
        "channel": "電話",
        "difficulty": "N1"
    }
    # 더미 데이터
    test_knowledge = {
        "n1": {"grammar": [{"form": "〜에도 불구하고", "meaning_ko": "~에도 불구하고", "example_jp": "...", "example_ko": "..."}]},
        "n2": {"grammar": []},
        "kanji": []
    }
    script = generate_script(test_situation, test_knowledge)
    print(json.dumps(script, ensure_ascii=False, indent=2))
