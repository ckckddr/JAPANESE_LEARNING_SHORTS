"""
비즈니스 일본어 YouTube 자동 업로드 메인 파이프라인

사용법:
  python main.py                  # 오늘 에피소드 생성 + 업로드 (B2B 1편 + B2C 1편)
  python main.py --dry-run        # 업로드 없이 테스트
  python main.py --skip-cache     # 캐시 무시하고 PDF 재추출
  python main.py --privacy private  # 비공개로 업로드
"""
import argparse
import json
import os
import sys
import logging
from datetime import datetime

from config import (
    SCRIPTS_DIR, AUDIO_DIR, VIDEO_DIR, LOG_DIR,
    PDF_N1, PDF_N2, PDF_KANJI,
)
from pipeline.extract_knowledge import load_or_extract_all
from pipeline.generate_situation import generate_situations, save_history
from pipeline.generate_script import generate_script
from pipeline.merge_audio import export_episode
from pipeline.tts import check_tts
from pipeline.make_video import build_video
from pipeline.youtube_upload import upload_video

# ── 로깅 설정 ──────────────────────────────────────────────
def setup_logging():
    log_file = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger(__name__)


def run(dry_run: bool = False, skip_cache: bool = False,
        privacy: str = "public"):
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info(f"비즈니스 일본어 YouTube 자동 업로드 시작")
    logger.info(f"실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"dry_run={dry_run}, privacy={privacy}")
    logger.info("=" * 60)

    # ── 0. TTS 연결 확인 ───────────────────────────────────
    logger.info("TTS 연결 확인 중...")
    if not check_tts():
        logger.error("Google Cloud TTS 연결 실패. GOOGLE_TTS_API_KEY를 확인하세요.")
        sys.exit(1)
    logger.info("TTS OK")

    # ── 1. 캐시 무시 옵션 ──────────────────────────────────
    if skip_cache:
        from config import CACHE_N1, CACHE_N2, CACHE_KANJI
        for cache in [CACHE_N1, CACHE_N2, CACHE_KANJI]:
            if cache.exists():
                cache.unlink()
                logger.info(f"캐시 삭제: {cache}")

    # ── 2. 지식베이스 로드 (캐시 우선) ────────────────────
    logger.info("\n[1단계] 지식베이스 로드...")
    knowledge = load_or_extract_all()

    # ── 3. 오늘 상황 생성 ──────────────────────────────────
    logger.info("\n[2단계] 오늘의 상황 생성...")
    situations = generate_situations()
    save_history(situations)
    for s in situations:
        logger.info(f"  [{s['type']}] {s['situation']} / {s['channel']} / {s['difficulty']}")

    # ── 4. 에피소드 생성 루프 ──────────────────────────────
    uploaded_urls = []
    today = datetime.now().strftime("%Y%m%d")

    for situation in situations:
        ep_type = situation["type"]
        ep_id = f"{today}_{ep_type}"
        logger.info(f"\n{'='*50}")
        logger.info(f"[3단계] {ep_id} 에피소드 생성 중...")

        # 스크립트 생성
        logger.info("  스크립트 생성 (Gemini API)...")
        script = generate_script(situation, knowledge)

        script_path = SCRIPTS_DIR / f"{ep_id}.json"
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        logger.info(f"  스크립트 저장: {script_path}")

        # 오디오 합성 (timings 정보 수집)
        logger.info("  오디오 합성 (TTS)...")
        mp3_path_base = str(AUDIO_DIR / f"{ep_id}.mp3")
        mp3_path, timings = export_episode(script, mp3_path_base)

        # 영상 제작
        logger.info("  영상 제작 (ffmpeg)...")
        video_path = build_video(script, mp3_path, str(VIDEO_DIR), timings=timings)

        # YouTube 업로드
        if dry_run:
            logger.info(f"  [DRY-RUN] 업로드 스킵: {video_path}")
            uploaded_urls.append({"ep_id": ep_id, "url": f"[dry-run] {video_path}"})
        else:
            logger.info("  YouTube 업로드...")
            url = upload_video(video_path, script, privacy=privacy)
            uploaded_urls.append({"ep_id": ep_id, "url": url})

    # ── 5. 결과 요약 ───────────────────────────────────────
    logger.info(f"\n{'='*60}")
    logger.info(f"완료! {len(uploaded_urls)}개 에피소드 처리됨")
    for item in uploaded_urls:
        logger.info(f"  [{item['ep_id']}] {item['url']}")

    return uploaded_urls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="비즈니스 일본어 YouTube 자동 업로드")
    parser.add_argument("--dry-run", action="store_true",
                        help="업로드 없이 테스트 실행")
    parser.add_argument("--skip-cache", action="store_true",
                        help="PDF 캐시 무시하고 재추출")
    parser.add_argument("--privacy", choices=["public", "unlisted", "private"],
                        default="public", help="YouTube 공개 설정 (기본: public)")
    args = parser.parse_args()

    run(
        dry_run=args.dry_run,
        skip_cache=args.skip_cache,
        privacy=args.privacy,
    )
