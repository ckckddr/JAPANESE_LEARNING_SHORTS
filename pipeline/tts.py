"""
Google Cloud TTS API (REST API Key 방식)로 일본어 음성 합성
"""
import os
import sys
import json
import base64
import requests
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import GOOGLE_TTS_API_KEY, TTS_VOICE_MALE, TTS_VOICE_FEMALE, TTS_VOICE_NARRATOR

TTS_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"

# 화자 역할별 음성 매핑
VOICE_MAP = {
    "male": TTS_VOICE_MALE,
    "female": TTS_VOICE_FEMALE,
    "narrator": TTS_VOICE_NARRATOR,
}

# 화자 이름별 성별 매핑 (일반적인 일본 이름 기준)
NAME_GENDER = {
    "田中": "male",
    "山田": "male",
    "佐藤": "female",
    "鈴木": "male",
    "高橋": "female",
    "伊藤": "male",
    "渡辺": "female",
    "ナレーター": "narrator",
    "narrator": "narrator",
}


def _get_voice_for_speaker(speaker: str) -> str:
    """화자 이름으로 음성 결정"""
    gender = NAME_GENDER.get(speaker, "male")
    return VOICE_MAP.get(gender, TTS_VOICE_MALE)


def synthesize_line(text: str, speaker: str, output_path: str,
                    speaking_rate: float = 1.0) -> str:
    """
    단일 텍스트 라인을 MP3로 합성
    Args:
        text: 일본어 텍스트
        speaker: 화자 이름 (음성 선택에 사용)
        output_path: 출력 MP3 경로
        speaking_rate: 읽기 속도 (0.25~4.0, 기본 1.0)
    Returns:
        output_path
    """
    voice_name = _get_voice_for_speaker(speaker)

    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "ja-JP",
            "name": voice_name,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": speaking_rate,
            "pitch": 0.0,
        }
    }

    resp = requests.post(
        TTS_ENDPOINT,
        params={"key": GOOGLE_TTS_API_KEY},
        json=payload,
        timeout=30
    )
    resp.raise_for_status()

    audio_content = resp.json().get("audioContent", "")
    audio_bytes = base64.b64decode(audio_content)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    return output_path


def check_tts() -> bool:
    """TTS API 연결 확인"""
    try:
        import tempfile
        tmp = tempfile.mktemp(suffix=".mp3")
        synthesize_line("テスト", "ナレーター", tmp)
        if os.path.exists(tmp):
            os.remove(tmp)
        return True
    except Exception as e:
        print(f"TTS 연결 오류: {e}")
        return False


if __name__ == "__main__":
    print("TTS 연결 테스트...")
    ok = check_tts()
    print("TTS OK" if ok else "TTS FAIL")
