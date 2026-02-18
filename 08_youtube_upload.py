"""YouTube Data API v3로 MP4 자동 업로드"""
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.pickle"
CLIENT_SECRET_FILE = "youtube_client_secret.json"  # GCP에서 다운로드


def get_youtube_client():
    """OAuth 인증 (최초 1회 브라우저 인증, 이후 토큰 재사용)"""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def build_metadata(script: dict) -> dict:
    """스크립트에서 YouTube 메타데이터 자동 생성"""
    situation = script.get("situation", {})
    ep_type = situation.get("type", "")
    ep_situation = situation.get("situation", "")
    title_jp = script.get("episode_title", "")
    difficulty = situation.get("difficulty", "N2")

    grammar_list = " / ".join(
        g["form"] for g in script.get("used_grammar", [])
    )
    vocab_list = " / ".join(
        v["word"] for v in script.get("used_vocab", [])
    )

    title = f"【{ep_type}】{title_jp} | 여행업 비즈니스 일본어 {difficulty}"

    description = f"""
여행업 실무 비즈니스 일본어 학습 팟캐스트

📌 상황: {ep_situation}
📌 타입: {ep_type} ({'도매사↔여행사' if ep_type == 'B2B' else '여행사↔고객'})
📌 난이도: {difficulty}

🔤 핵심 문법: {grammar_list}
📝 핵심 어휘: {vocab_list}

━━━━━━━━━━━━━━━━━━━━
[구성]
00:00 상황 소개
01:00 핵심 문법 해설
03:00 실전 대화
종료 전 핵심 문장 정리

#비즈니스일본어 #JLPT{difficulty} #여행업일본어 #일본어공부 #{ep_type}
""".strip()

    tags = [
        "비즈니스일본어", f"JLPT{difficulty}", "여행업일본어",
        "일본어공부", ep_type, "日本語", "ビジネス日本語"
    ]

    return {"title": title, "description": description, "tags": tags}


def upload_video(video_path: str, script: dict) -> str:
    """YouTube 업로드 → 영상 URL 반환"""
    youtube = get_youtube_client()
    metadata = build_metadata(script)

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": "27",   # Education
            "defaultLanguage": "ko",
        },
        "status": {
            "privacyStatus": "public",   # public / unlisted / private
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

    print(f"  YouTube 업로드 중: {metadata['title']}")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  업로드 진행: {int(status.progress() * 100)}%")

    video_id = response["id"]
    url = f"https://youtu.be/{video_id}"
    print(f"  업로드 완료: {url}")
    return url


if __name__ == "__main__":
    print("YouTube 클라이언트 인증 테스트...")
    client = get_youtube_client()
    print("인증 OK")
