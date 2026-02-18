# JAPANESE_LEARNING_SHORTS

비즈니스 일본어 학습용 YouTube Shorts 자동 생성 및 업로드 시스템입니다. JLPT N1/N2 수준의 비즈니스 일본어 상황극을 생성하고, TTS와 ffmpeg를 통해 자막이 포함된 세로형 영상을 제작하여 YouTube에 자동으로 업로드합니다.

## 주요 기능
- **상황극 생성**: Gemini API를 사용하여 여행업 실무 중심의 비즈니스 일본어 스크립트 생성
- **지식 베이스 활용**: 제공된 N1/N2 문사 및 한자 리스트를 기반으로 한 학습 콘텐츠 구성
- **음성 합성**: Google Cloud TTS를 사용한 자연스러운 일본어/한국어 성우 음성 생성
- **영상 제작**: ffmpeg를 활용한 1080x1920(Vertical) Shorts 영상 및 다이내믹 자막 생성
- **자동 업로드**: YouTube Data API v3를 통한 데일리 자동 업로드

## 설치 및 설정
1. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```
2. **환경 변수 설정**: `.env.example` 파일을 참고하여 `.env` 파일을 생성하고 아래 키를 입력하세요.
   - `GEMINI_API_KEY`
   - `GOOGLE_TTS_API_KEY`
3. **YouTube API 설정**: Google Cloud Console에서 YouTube Data API v3를 활성화하고 `youtube_client_secret.json` 파일을 루트 디렉토리에 저장하세요.

## 실행 방법
- **수동 실행**:
  ```bash
  python main.py
  ```
- **테스트(업로드 제외)**:
  ```bash
  python main.py --dry-run
  ```

## 기술 스택
- Python 3.14
- Google Gemini API (Content Generation)
- Google Cloud TTS (Audio)
- ffmpeg (Video Editing)
- YouTube Data API v3 (Upload)
