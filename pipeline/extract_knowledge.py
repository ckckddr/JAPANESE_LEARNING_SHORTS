"""
PDF에서 문법/어휘/한자 지식을 추출하고 캐시합니다.
최초 1회만 Gemini API 호출, 이후 JSON 캐시 사용.
"""
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from google import genai
from google.genai import types
from config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    PDF_N1, PDF_N2, PDF_KANJI,
    CACHE_N1, CACHE_N2, CACHE_KANJI,
)
from pipeline.parse_pdf import parse_pdf

_client = genai.Client(api_key=GEMINI_API_KEY)

# ── 청크 크기 (Gemini 컨텍스트 및 출력 제한 고려) ─────────
CHUNK_SIZE = 4000  # 8000에서 4000으로 축소 (출력 잘림 방지)


def _chunk_text(text: str, size: int = CHUNK_SIZE):
    """텍스트를 청크로 분할"""
    for i in range(0, len(text), size):
        yield text[i:i + size]


def _extract_grammar_from_chunk(chunk: str, level: str) -> list:
    """청크에서 문법 항목 추출"""
    prompt = f"""다음은 JLPT {level} 문법 교재의 일부입니다.
이 텍스트에서 문법 항목을 추출하여 JSON 배열로 반환하세요.

각 항목 형식:
{{
  "form": "문법 형태 (예: 〜에도 불구하고)",
  "meaning_ko": "한국어 의미",
  "example_jp": "일본어 예문",
  "example_ko": "예문 한국어 번역",
  "level": "{level}"
}}

텍스트:
{chunk}

JSON 배열만 반환하세요. 추출할 항목이 없으면 [] 반환."""

    try:
        resp = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        # 텍스트 추출 시 점검
        text_content = resp.text.strip()
        if text_content.startswith("```"):
            text_content = text_content.split("```")[1]
            if text_content.startswith("json"):
                text_content = text_content[4:]
        return json.loads(text_content)
    except Exception as e:
        print(f"  [경고] 문법 추출 오류: {e}")
        return []


def _extract_kanji_from_chunk(chunk: str) -> list:
    """청크에서 한자 항목 추출"""
    prompt = f"""다음은 일본 상용한자 교재의 일부입니다.
이 텍스트에서 한자 항목을 추출하여 JSON 배열로 반환하세요.

각 항목 형식:
{{
  "kanji": "한자 (예: 旅)",
  "reading": "음독/훈독 (예: りょ/た비)",
  "meaning_ko": "한국어 의미",
  "example_word": "예시 단어 (예: 旅行)",
  "example_reading": "예시 단어 읽기 (예: りょこう)"
}}

텍스트:
{chunk}

JSON 배열만 반환하세요. 추출할 항목이 없으면 [] 반환."""

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
        return json.loads(text_content)
    except Exception as e:
        print(f"  [경고] 한자 추출 오류: {e}")
        return []


def extract_grammar(pdf_path: str, level: str) -> list:
    """PDF에서 문법 항목 전체 추출"""
    print(f"  PDF 파싱: {pdf_path}")
    text = parse_pdf(str(pdf_path))
    print(f"  텍스트 추출 완료 ({len(text):,}자)")

    all_grammar = []
    chunks = list(_chunk_text(text))
    print(f"  {len(chunks)}개 청크로 분할하여 Gemini API 호출...")

    for i, chunk in enumerate(chunks):
        print(f"  청크 {i+1}/{len(chunks)} 처리 중...")
        items = _extract_grammar_from_chunk(chunk, level)
        all_grammar.extend(items)
        time.sleep(1)  # API 레이트 리밋 방지

    # 중복 제거 (form 기준)
    seen = set()
    unique = []
    for g in all_grammar:
        key = g.get("form", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(g)

    print(f"  {level} 문법 추출 완료: {len(unique)}개")
    return unique


def extract_kanji(pdf_path: str) -> list:
    """PDF에서 한자 전체 추출"""
    print(f"  PDF 파싱: {pdf_path}")
    text = parse_pdf(str(pdf_path))
    print(f"  텍스트 추출 완료 ({len(text):,}자)")

    all_kanji = []
    chunks = list(_chunk_text(text))
    print(f"  {len(chunks)}개 청크로 분할하여 Gemini API 호출...")

    for i, chunk in enumerate(chunks):
        print(f"  청크 {i+1}/{len(chunks)} 처리 중...")
        items = _extract_kanji_from_chunk(chunk)
        all_kanji.extend(items)
        time.sleep(1)

    # 중복 제거 (kanji 기준)
    seen = set()
    unique = []
    for k in all_kanji:
        key = k.get("kanji", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(k)

    print(f"  한자 추출 완료: {len(unique)}개")
    return unique


def load_or_extract_all() -> dict:
    """
    3개 PDF 캐시 통합 로드.
    캐시가 있으면 즉시 반환, 없으면 추출 후 캐시 저장.
    반환: {"n1": {"grammar": [...]}, "n2": {"grammar": [...]}, "kanji": [...]}
    """
    result = {}

    # ── N1 문법 ────────────────────────────────────────────
    if CACHE_N1.exists():
        print(f"[캐시] N1 문법 로드: {CACHE_N1}")
        with open(CACHE_N1, "r", encoding="utf-8") as f:
            result["n1"] = json.load(f)
    else:
        print("[추출] N1 문법 PDF 처리 중...")
        grammar_n1 = extract_grammar(PDF_N1, "N1")
        data = {"grammar": grammar_n1}
        with open(CACHE_N1, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        result["n1"] = data
        print(f"[저장] {CACHE_N1}")

    # ── N2 문법 ────────────────────────────────────────────
    if CACHE_N2.exists():
        print(f"[캐시] N2 문법 로드: {CACHE_N2}")
        with open(CACHE_N2, "r", encoding="utf-8") as f:
            result["n2"] = json.load(f)
    else:
        print("[추출] N2 문법 PDF 처리 중...")
        grammar_n2 = extract_grammar(PDF_N2, "N2")
        data = {"grammar": grammar_n2}
        with open(CACHE_N2, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        result["n2"] = data
        print(f"[저장] {CACHE_N2}")

    # ── 상용한자 ───────────────────────────────────────────
    if CACHE_KANJI.exists():
        print(f"[캐시] 한자 로드: {CACHE_KANJI}")
        with open(CACHE_KANJI, "r", encoding="utf-8") as f:
            result["kanji"] = json.load(f)
    else:
        print("[추출] 한자 PDF 처리 중...")
        kanji = extract_kanji(PDF_KANJI)
        with open(CACHE_KANJI, "w", encoding="utf-8") as f:
            json.dump(kanji, f, ensure_ascii=False, indent=2)
        result["kanji"] = kanji
        print(f"[저장] {CACHE_KANJI}")

    n1_cnt = len(result["n1"]["grammar"])
    n2_cnt = len(result["n2"]["grammar"])
    kanji_cnt = len(result["kanji"]) if isinstance(result["kanji"], list) else 0
    print(f"\n[지식베이스] N1: {n1_cnt}개, N2: {n2_cnt}개, 한자: {kanji_cnt}개")
    return result


if __name__ == "__main__":
    knowledge = load_or_extract_all()
    print("추출 완료!")
