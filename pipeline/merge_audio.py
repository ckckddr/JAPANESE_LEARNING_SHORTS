"""
대화 스크립트의 각 라인을 TTS로 합성하고 하나의 MP3로 병합
pydub 대신 ffmpeg subprocess 직접 호출 (Python 3.14 호환)

[변경] export_episode()가 (output_path, timings) 튜플을 반환
timings: 각 세그먼트의 실제 오디오 길이 정보
  [
    {"type": "thumbnail", "duration": 3.0},   # 썸네일 구간
    {"type": "narration", "duration": 4.2},   # 인트로 나레이션
    {"type": "dialogue",  "duration": 2.8, "index": 0},  # 대사별
    ...
    {"type": "review",    "duration": 5.1},   # 핵심문장 복습
  ]
"""
import os
import sys
import subprocess
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .make_video import get_audio_duration, THUMBNAIL_DURATION
from .tts import check_tts, synthesize_line
from config import AUDIO_DIR

# 화자 전환 간격 (초)
PAUSE_BETWEEN_LINES    = 0.6
PAUSE_AFTER_NARRATION  = 1.0
PAUSE_BETWEEN_SECTIONS = 1.5


def _audio_note_to_rate(note: str) -> float:
    mapping = {"slow": 0.85, "normal": 1.0, "emphasis": 0.9, "fast": 1.15}
    return mapping.get(note, 1.0)


def _make_silence(duration_sec: float, output_path: str):
    """ffmpeg로 무음 MP3 생성"""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=22050:cl=mono",
        "-t", str(duration_sec),
        "-acodec", "libmp3lame",
        output_path
    ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.run(cmd, capture_output=True, check=True, startupinfo=startupinfo)


def _concat_mp3s(file_list: list, output_path: str):
    """ffmpeg concat demuxer로 MP3 파일들을 하나로 합치기"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        list_path = f.name
        for fp in file_list:
            escaped = fp.replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    result = subprocess.run(cmd, capture_output=True, text=False, startupinfo=startupinfo)
    os.unlink(list_path)

    stderr_text = result.stderr.decode('utf-8', errors='replace')
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg concat 오류: {stderr_text[-300:]}")


def export_episode(script: dict, output_path: str) -> tuple[str, list[dict]]:
    """
    스크립트 전체를 MP3로 합성
    구성: 나레이션 → 대화 → 핵심 문장 복습

    Returns:
        (output_path, timings)
        timings: 각 세그먼트의 실제 측정 길이 정보 리스트
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # timings: make_video에서 화면 전환 타이밍에 사용
    # thumbnail 구간은 고정값, 나머지는 실제 오디오 길이 측정
    timings = [{"type": "thumbnail", "duration": THUMBNAIL_DURATION}]

    with tempfile.TemporaryDirectory() as tmpdir:
        segments = []
        idx = 0

        # ── 세그먼트 누적용 버퍼 ─────────────────────────
        # 나레이션/복습은 하나의 타이밍 블록으로 묶음
        # 대사는 각각 개별 타이밍으로 측정

        def add_silence(duration):
            nonlocal idx
            p = os.path.join(tmpdir, f"sil_{idx:04d}.mp3")
            _make_silence(duration, p)
            segments.append({"path": p, "tag": "silence"})
            idx += 1

        def add_tts(text, speaker, rate=1.0, tag="misc"):
            nonlocal idx
            p = os.path.join(tmpdir, f"seg_{idx:04d}.mp3")
            synthesize_line(text, speaker, p, speaking_rate=rate)
            segments.append({"path": p, "tag": tag})
            idx += 1

        # ── 1. 인트로 무음 ──────────────────────────────────
        add_silence(0.5)

        # ── 2. 인트로 나레이션 ──────────────────────────────
        narration_start_idx = len(segments)
        intro_jp = script.get("intro_narration", "")
        if intro_jp:
            add_tts(intro_jp, "ナレーター", rate=0.95, tag="narration")
            add_silence(PAUSE_AFTER_NARRATION)

        # 나레이션 구간 길이 측정
        narration_segs = segments[narration_start_idx:]
        if narration_segs:
            narration_dur = sum(
                get_audio_duration(s["path"]) for s in narration_segs
            )
            timings.append({"type": "narration", "duration": narration_dur})

        # ── 3. 대화 라인 (각각 개별 타이밍 측정) ────────────
        dialogue = script.get("dialogue", [])
        for i, line in enumerate(dialogue):
            speaker = line.get("speaker", "田中")
            text_jp = line.get("text_jp", "")
            rate = _audio_note_to_rate(line.get("audio_note", "normal"))
            if not text_jp:
                continue

            seg_start_idx = len(segments)
            add_tts(text_jp, speaker, rate=rate, tag=f"dialogue_{i}")
            add_silence(PAUSE_BETWEEN_LINES)

            # 이 대사 + 뒤 무음까지의 실제 길이
            line_segs = segments[seg_start_idx:]
            line_dur = sum(get_audio_duration(s["path"]) for s in line_segs)
            timings.append({
                "type": "dialogue",
                "index": i,
                "duration": line_dur,
                "speaker": speaker,
            })

        # ── 4. 아웃트로 무음 ───────────────────────────────
        add_silence(0.5)

        # ── 6. 전체 병합 ───────────────────────────────────
        all_paths = [s["path"] for s in segments]
        _concat_mp3s(all_paths, output_path)

    # 3분(180초) 길이 제한 체크
    try:
        duration = get_audio_duration(output_path)
        if duration > 180:
            print(f"  [경고] 오디오 길이가 {duration:.1f}초로 3분을 초과했습니다.")
    except Exception:
        pass

    size_kb = os.path.getsize(output_path) // 1024
    print(f"  오디오 생성 완료: {output_path} ({size_kb} KB)")
    return output_path, timings