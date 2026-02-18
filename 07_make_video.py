"""MP3 + 썸네일 이미지 → MP4 변환 (ffmpeg 사용)"""
import subprocess
import os
import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

THUMBNAIL_SIZE = (1280, 720)
BG_COLOR = (18, 18, 40)       # 다크 네이비
ACCENT_COLOR = (255, 60, 60)   # 레드 포인트
TEXT_COLOR = (255, 255, 255)


def make_thumbnail(script: dict, output_path: str):
    """에피소드 썸네일 이미지 생성"""
    img = Image.new("RGB", THUMBNAIL_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)

    situation = script.get("situation", {})
    ep_type = situation.get("type", "")
    title = script.get("episode_title", "ビジネス日本語")

    # 타입 뱃지 (B2B / B2C)
    badge_color = (255, 60, 60) if ep_type == "B2C" else (60, 120, 255)
    draw.rectangle([60, 60, 200, 110], fill=badge_color)
    draw.text((90, 70), ep_type, fill=TEXT_COLOR)

    # 에피소드 제목
    draw.text((60, 140), title, fill=TEXT_COLOR)

    # 상황 설명
    situation_text = situation.get("situation", "")
    draw.text((60, 260), situation_text, fill=(180, 180, 200))

    # 하단 브랜딩
    draw.rectangle([0, 640, 1280, 720], fill=ACCENT_COLOR)
    draw.text((60, 652), "ビジネス日本語 Podcast  |  N1/N2", fill=TEXT_COLOR)

    img.save(output_path)
    return output_path


def make_video(mp3_path: str, thumbnail_path: str, output_path: str):
    """ffmpeg로 MP3 + 이미지 → MP4"""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", thumbnail_path,
        "-i", mp3_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 오류: {result.stderr}")
    return output_path


def build_video(script: dict, mp3_path: str, video_dir: str) -> str:
    """썸네일 생성 + MP4 변환"""
    os.makedirs(video_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(mp3_path))[0]

    thumbnail_path = os.path.join(video_dir, f"{base}_thumb.jpg")
    video_path = os.path.join(video_dir, f"{base}.mp4")

    print(f"  썸네일 생성: {thumbnail_path}")
    make_thumbnail(script, thumbnail_path)

    print(f"  MP4 변환: {video_path}")
    make_video(mp3_path, thumbnail_path, video_path)

    return video_path
