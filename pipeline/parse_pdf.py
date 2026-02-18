"""PDF 텍스트 추출 모듈 (pdfplumber 사용)"""
import pdfplumber


def parse_pdf(pdf_path: str) -> str:
    """PDF 파일에서 전체 텍스트를 추출합니다."""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                texts.append(text)
            if (i + 1) % 50 == 0:
                print(f"  PDF 파싱 중... {i+1}/{total} 페이지")
    return "\n".join(texts)
