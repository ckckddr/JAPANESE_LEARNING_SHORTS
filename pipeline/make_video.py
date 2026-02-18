"""
MP3 + 썸네일 이미지 → MP4 변환 (ffmpeg 사용)
[업데이트] 썸네일 구간 + 대본 자막 구간 구성
  - 영상 시작: 썸네일 정적 화면 (THUMBNAIL_DURATION초)
  - 이후: 각 대사를 화자명 / 일본어 / 한국어 번역으로 표시
  - 세로형 숏츠 (1080x1920) 지원
"""
import subprocess
import os
import sys
import shutil
import requests
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from PIL import Image, ImageDraw, ImageFont
from config import THUMBNAIL_SIZE, VIDEO_DIR, DATA_DIR

W, H = THUMBNAIL_SIZE # 1080, 1920
BG_COLOR = (12, 16, 38)         # 딥 네이비
ACCENT_COLOR = (255, 75, 75)    # 레드 포인트
ACCENT_BLUE = (60, 130, 255)    # 블루 포인트
TEXT_COLOR = (255, 255, 255)
SUBTEXT_COLOR = (180, 185, 210)
GOLD_COLOR = (255, 200, 60)
SPEAKER_A_COLOR = (100, 200, 255)   # 화자 A 이름 색
SPEAKER_B_COLOR = (255, 150, 100)   # 화자 B 이름 색
DIM_OVERLAY    = (0, 0, 0, 160)     # 자막 배경 반투명

# 썸네일 표시 시간 (초)
THUMBNAIL_DURATION = 0.5

FONT_DIR = DATA_DIR / "fonts"

# Font Download URLs (Reliable CDNs)
FONT_URL_JP = "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"
FONT_URL_KR = "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/OTF/Korean/NotoSansCJKkr-Bold.otf"


def _ensure_fonts():
    """Noto Sans JP/KR 폰트 자동 다운로드"""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    
    font_jp = FONT_DIR / "NotoSansCJKjp-Bold.otf"
    font_kr = FONT_DIR / "NotoSansCJKkr-Bold.otf"

    if not font_jp.exists():
        print("  폰트 다운로드 중 (JP)...")
        try:
            r = requests.get(FONT_URL_JP, timeout=30)
            r.raise_for_status()
            with open(font_jp, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"  [경고] JP 폰트 다운로드 실패: {e}")

    if not font_kr.exists():
        print("  폰트 다운로드 중 (KR)...")
        try:
            r = requests.get(FONT_URL_KR, timeout=30)
            r.raise_for_status()
            with open(font_kr, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"  [경고] KR 폰트 다운로드 실패: {e}")

    return str(font_jp), str(font_kr)


def _get_font(size: int, lang: str = "JP"):
    """
    폰트 로드 (JP 또는 KR)
    다운로드 실패 시 시스템 기본 폰트로 폴백
    """
    path_jp, path_kr = _ensure_fonts()
    font_path = path_jp if lang == "JP" else path_kr

    if not os.path.exists(font_path):
        # 폰트 다운 실패 시 시스템 폰트 시도 (윈도우 기준)
        if lang == "JP":
            font_path = "C:/Windows/Fonts/msgothic.ttc"
        else:
            font_path = "C:/Windows/Fonts/malgun.ttf"
            
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    """글자 단위로 max_width를 넘지 않도록 줄바꿈"""
    # \n이 포함된 경우 먼저 분리해서 각각 처리
    if "\n" in text:
        result = []
        for segment in text.split("\n"):
            result.extend(_wrap_text(draw, segment, font, max_width))
        return result

    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if draw.textlength(test, font=font) > max_width:
            if cur:
                lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines if lines else [text]



def _draw_badge(draw, font, text, x, y, h=55,
                fill=None, outline=None, text_color=TEXT_COLOR, pad_x=20, pad_y=10):
    """
    pad_y: 텍스트 위아래 여백 (px). h보다 우선 적용.
    h는 pad_y 무시하고 명시적으로 높이를 고정하고 싶을 때만 사용.
    """
    box_w = int(draw.textlength(text, font=font)) + pad_x * 2
    # 실제 텍스트 높이를 bbox로 정확히 측정
    bbox = font.getbbox(text)
    text_h = bbox[3] - bbox[1]
    box_h = text_h + pad_y * 2
    if fill:
        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=10, fill=fill)
    if outline:
        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=10, outline=outline, width=2)
    # bbox[1]은 폰트 상단 여백(ascender) 보정
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, fill=text_color, font=font)
    return x + box_w + 15


def make_thumbnail(script: dict, output_path: str) -> str:
    """에피소드 썸네일 이미지 생성 (1080x1920)"""
    img = Image.new("RGB", THUMBNAIL_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)

    situation = script.get("situation", {})
    ep_type = situation.get("type", "B2B")
    difficulty = situation.get("difficulty", "N2")
    title = script.get("episode_title", "ビジネス日本語")
    situation_text = situation.get("situation", "")
    channel = situation.get("channel", "")

    # ── 배경 그라데이션 효과 (좌측 세로 바) ──────────────────
    badge_color = ACCENT_COLOR if ep_type == "B2C" else ACCENT_BLUE
    draw.rectangle([0, 0, 10, H], fill=badge_color)

    # ── 상단 뱃지 영역 ────────────────────────────────────
    font_badge = _get_font(32, "JP")
    x = 40
    x = _draw_badge(draw, font_badge, ep_type, x, 80, fill=badge_color)
    x = _draw_badge(draw, font_badge, "JLPT " + difficulty, x, 80,
                    fill=GOLD_COLOR, text_color=(20, 20, 20))
    x = _draw_badge(draw, font_badge, channel, x, 80, outline=SUBTEXT_COLOR)

    # ── 에피소드 제목 ─────────────────────────────────────
    font_title = _get_font(64, "JP")
    lines = _wrap_text(draw, title, font_title, W - 80)
    y = 200
    for line in lines:
        draw.text((40, y), line, fill=TEXT_COLOR, font=font_title)
        y += 85

    # ── 상황 설명 ─────────────────────────────────────────
    font_situation = _get_font(38, "JP")
    sit_lines = _wrap_text(draw, situation_text, font_situation, W - 80)
    y += 40
    for line in sit_lines:
        draw.text((40, y), line, fill=SUBTEXT_COLOR, font=font_situation)
        y += 55

    # ── 핵심 문법 표시 ────────────────────────────────────
    used_grammar = script.get("used_grammar", [])
    if used_grammar:
        font_g = _get_font(30, "KR")
        gy = max(y + 80, 750)
        _draw_badge(draw, font_g, "핵심 문법", 40, gy, fill=badge_color)
        bbox = font_g.getbbox("핵심 문법")
        gy += (bbox[3] - bbox[1]) + 10 * 2 + 14
        for g in used_grammar[:3]:
            text = "  " + g.get("form", "") + "   (" + g.get("meaning_ko", "") + ")"
            draw.text((50, gy), text, fill=SUBTEXT_COLOR, font=font_g)
            gy += 44


    # ── 하단 브랜딩 바 ────────────────────────────────────
    draw.rectangle([0, H - 120, W, H], fill=badge_color)
    font_brand = _get_font(34, "KR")
    draw.text((40, H - 100), "ビジネス日本語 Podcast  |  여행업 실무 일본어",
              fill=TEXT_COLOR, font=font_brand)
    tag_text = f"#{ep_type} #{difficulty}"
    tw = draw.textlength(tag_text, font=font_brand)
    draw.text((W - 40 - tw, H - 100), tag_text, fill=TEXT_COLOR, font=font_brand)

    img.save(output_path, quality=95)
    return output_path


def _speaker_color(speaker: str, speakers: list[str]) -> tuple:
    unique = list(dict.fromkeys(speakers))
    idx = unique.index(speaker) if speaker in unique else 0
    colors = [SPEAKER_A_COLOR, SPEAKER_B_COLOR, GOLD_COLOR, SUBTEXT_COLOR]
    return colors[idx % len(colors)]


def make_dialogue_frame(line: dict, speakers: list[str],
                        script: dict, output_path: str) -> str:
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    situation  = script.get("situation", {})
    ep_type    = situation.get("type", "B2B")
    difficulty = situation.get("difficulty", "N2")
    title      = script.get("episode_title", "ビジネス日本語")
    badge_color = ACCENT_COLOR if ep_type == "B2C" else ACCENT_BLUE

    draw.rectangle([0, 0, 10, H], fill=badge_color)

    font_top = _get_font(32, "JP")
    draw.text((40, 40), f"【{ep_type}】{title}", fill=SUBTEXT_COLOR, font=font_top)

    speaker    = line.get("speaker", "")
    role       = line.get("role", "")
    text_jp    = line.get("text_jp", "")
    text_ko    = line.get("text_ko", "")
    sp_color   = _speaker_color(speaker, speakers)

    font_speaker = _get_font(52, "JP")
    font_role    = _get_font(30, "KR")
    font_jp_text = _get_font(44, "JP")
    font_ko_text = _get_font(36, "KR")

    center_start = H // 3
    padding = 50
    max_w = W - padding * 2

    draw.text((padding, center_start), speaker, fill=sp_color, font=font_speaker)
    role_y = center_start + 65
    draw.text((padding, role_y), role, fill=SUBTEXT_COLOR, font=font_role)

    line_y = role_y + 50
    draw.line([(padding, line_y), (W - padding, line_y)], fill=badge_color, width=2)

    jp_y = line_y + 30
    jp_lines = _wrap_text(draw, text_jp, font_jp_text, max_w)
    for jl in jp_lines:
        draw.text((padding, jp_y), jl, fill=TEXT_COLOR, font=font_jp_text)
        jp_y += 58

    ko_y = jp_y + 30
    ko_lines = _wrap_text(draw, text_ko, font_ko_text, max_w)
    box_h = len(ko_lines) * 50 + 30
    img.paste(Image.new("RGB", (W - padding, box_h), (20, 28, 60)),
              (padding // 2, ko_y - 10))
    for kl in ko_lines:
        draw.text((padding, ko_y), kl, fill=(180, 220, 255), font=font_ko_text)
        ko_y += 50

    draw.rectangle([0, H - 120, W, H], fill=badge_color)
    font_brand = _get_font(30, "KR")
    draw.text((40, H - 95), "ビジネス日本語 Podcast  |  여행업 실무 일본어",
              fill=TEXT_COLOR, font=font_brand)
    tag_text = f"#{ep_type} #{difficulty} #Shorts"
    tw = draw.textlength(tag_text, font=font_brand)
    draw.text((W - 40 - tw, H - 95), tag_text, fill=TEXT_COLOR, font=font_brand)

    img.save(output_path, quality=92)
    return output_path


def get_audio_duration(mp3_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mp3_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _run_ffmpeg(cmd: list, label: str = ""):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    result = subprocess.run(cmd, capture_output=True, text=False, startupinfo=startupinfo)
    stderr = result.stderr.decode('utf-8', errors='replace')
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 오류 [{label}]: {stderr[-500:]}")


def make_video(mp3_path: str, thumbnail_path: str,
               output_path: str, script: dict = None,
               timings: list = None) -> str:
    if script is None:
        return _make_video_simple(mp3_path, thumbnail_path, output_path)

    dialogue = script.get("dialogue", [])
    total_duration = get_audio_duration(mp3_path)
    if total_duration <= 0 or not dialogue:
        return _make_video_simple(mp3_path, thumbnail_path, output_path)

    speakers = [d.get("speaker", "") for d in dialogue]

    # ── 타이밍 계산 ──────────────────────────────────────
    if timings:
        thumb_dur    = next((t["duration"] for t in timings if t["type"] == "thumbnail"), THUMBNAIL_DURATION)
        narration_dur = next((t["duration"] for t in timings if t["type"] == "narration"), 0.0)
        dialogue_timings = {t["index"]: t["duration"] for t in timings if t["type"] == "dialogue"}
        review_dur   = next((t["duration"] for t in timings if t["type"] == "review"), 0.0)
    else:
        print("  [경고] timings 없음 - 균등 분할 사용")
        thumb_dur = THUMBNAIL_DURATION
        narration_dur = 0.0
        review_dur = 0.0
        remaining = max(total_duration - thumb_dur, 1.0)
        per = remaining / len(dialogue)
        dialogue_timings = {i: per for i in range(len(dialogue))}

    tmpdir = tempfile.mkdtemp(prefix="bjp_video_")
    try:
        segment_paths = []
        thumb_vid = os.path.join(tmpdir, "seg_thumb.mp4")
        _run_ffmpeg([
            "ffmpeg", "-y",
            "-loop", "1", "-i", thumbnail_path,
            "-t", str(thumb_dur),
            "-vf", f"scale={W}:{H},setsar=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
            thumb_vid
        ], "썸네일 클립")
        segment_paths.append(thumb_vid)

        if narration_dur > 0:
            narr_vid = os.path.join(tmpdir, "seg_narr.mp4")
            _run_ffmpeg([
                "ffmpeg", "-y",
                "-loop", "1", "-i", thumbnail_path,
                "-t", str(narration_dur),
                "-vf", f"scale={W}:{H},setsar=1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                narr_vid
            ], "나레이션 클립")
            segment_paths.append(narr_vid)

        for i, line in enumerate(dialogue):
            dur = dialogue_timings.get(i)
            if not dur or dur <= 0:
                continue

            frame_path = os.path.join(tmpdir, f"frame_{i:03d}.jpg")
            make_dialogue_frame(line, speakers, script, frame_path)
            seg_path = os.path.join(tmpdir, f"seg_{i:03d}.mp4")
            _run_ffmpeg([
                "ffmpeg", "-y",
                "-loop", "1", "-i", frame_path,
                "-t", str(dur),
                "-vf", f"scale={W}:{H},setsar=1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                seg_path
            ], f"대사 클립 {i}")
            segment_paths.append(seg_path)

        print(f"  [DEBUG] segment_paths ({len(segment_paths)}개): {segment_paths}")
        concat_txt = os.path.join(tmpdir, "concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in segment_paths:
                f.write("file '{}'\n".format(p.replace("\\", "/")))

        silent_vid = os.path.join(tmpdir, "silent.mp4")
        _run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-c:v", "copy",
            silent_vid
        ], "concat")

        _run_ffmpeg([
            "ffmpeg", "-y",
            "-i", silent_vid,
            "-i", mp3_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ], "오디오 합성")

        return output_path
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _make_video_simple(mp3_path: str, thumbnail_path: str,
                       output_path: str) -> str:
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", thumbnail_path,
        "-i", mp3_path,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-shortest",
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=disable,setsar=1",
        output_path
    ]
    _run_ffmpeg(cmd, "simple")
    return output_path


def build_video(script: dict, mp3_path: str, video_dir: str = None,
                timings: list = None) -> str:
    if video_dir is None:
        video_dir = str(VIDEO_DIR)
    os.makedirs(video_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(mp3_path))[0]
    thumbnail_path = os.path.join(video_dir, f"{base}_thumb.jpg")
    video_path     = os.path.join(video_dir, f"{base}.mp4")

    print(f"  썸네일 생성: {thumbnail_path}")
    make_thumbnail(script, thumbnail_path)
    print(f"  MP4 변환: {video_path}")
    make_video(mp3_path, thumbnail_path, video_path, script=script, timings=timings)
    return video_path