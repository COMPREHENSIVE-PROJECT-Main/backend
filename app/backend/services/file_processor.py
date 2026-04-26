# 첨부파일 처리 서비스 (텍스트 추출 → LLM 핵심 요약)

import base64
import json

from fastapi import UploadFile
from openai import AzureOpenAI

from app.com.logger import get_logger

logger = get_logger("file_processor")

# 지원 파일 유형별 처리 방식
_TEXT_EXTS  = {".pdf", ".docx", ".doc", ".txt", ".md"}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"}
_AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}

_MAX_EXTRACT_CHARS = 8000   # 텍스트 추출 후 LLM에 넘길 최대 길이 (토큰 절약)


def _ext(filename: str) -> str:
    from pathlib import Path
    return Path(filename).suffix.lower()


def _extract_pdf(content: bytes) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc).strip()


def _extract_docx(content: bytes) -> str:
    import io
    from docx import Document
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_text(content: bytes, filename: str) -> str | None:
    ext = _ext(filename)
    try:
        if ext == ".pdf":
            return _extract_pdf(content)
        if ext in (".docx", ".doc"):
            return _extract_docx(content)
        if ext in (".txt", ".md"):
            return content.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning("텍스트 추출 실패: file=%s, error=%s", filename, e)
    return None


def _summarize_text(raw_text: str, filename: str) -> str:
    from app.ai.services.llm_service import call_llm

    truncated = raw_text[:_MAX_EXTRACT_CHARS]
    system_prompt = (
        "당신은 법률 문서 요약 전문가입니다.\n"
        "문서에서 법적으로 중요한 핵심 정보만 추출하세요.\n"
        "불필요한 서술 없이 항목 형식으로 간결하게 작성하세요."
    )
    user_prompt = (
        f"다음 문서({filename})에서 핵심 정보만 추출하세요.\n"
        "추출 대상: 당사자명, 날짜, 금액, 주요 사실관계, 증거 항목.\n"
        "200자 이내로 간결하게 작성하세요.\n\n"
        f"문서 내용:\n{truncated}"
    )
    return call_llm(system_prompt, user_prompt)


def _analyze_image(content: bytes, filename: str) -> str:
    from app.ai.core.runtime import settings

    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.normalized_azure_openai_endpoint,
    )
    b64 = base64.b64encode(content).decode()
    ext = _ext(filename).lstrip(".")
    mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"

    response = client.chat.completions.create(
        model=settings.chat_model_name,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "이 이미지는 법률 사건의 증거 자료입니다.\n"
                        "법적으로 중요한 내용만 100자 이내로 간결하게 요약하세요.\n"
                        "장면을 생생하게 묘사하지 말고 사실관계 중심으로 작성하세요."
                    ),
                },
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


async def process_attachments(files: list[UploadFile]) -> tuple[str, list[str]]:
    """
    첨부파일 목록을 처리하여 요약 텍스트와 추가 질문 목록 반환.

    Returns:
        (file_summary, extra_questions)
        - file_summary: 분석 가능한 파일들의 핵심 내용 요약 (case JSON에 저장)
        - extra_questions: 분석 불가 파일(영상 등)에 대한 추가 질문
    """
    if not files:
        return "", []

    summaries: list[str] = []
    extra_questions: list[str] = []

    for file in files:
        if not file.filename:
            continue

        ext = _ext(file.filename)
        content = await file.read()

        if ext in _VIDEO_EXTS:
            extra_questions.append(
                f"첨부하신 영상 '{file.filename}'에 어떤 내용이 담겨 있는지 구체적으로 서술해주세요. "
                "(예: 촬영 시각, 장소, 등장인물, 주요 상황)"
            )
            logger.info("영상 파일, 질문 추가: %s", file.filename)
            continue

        if ext in _AUDIO_EXTS:
            extra_questions.append(
                f"첨부하신 음성 파일 '{file.filename}'의 내용을 요약해주세요. "
                "(예: 발화자, 대화 내용, 녹음 경위)"
            )
            logger.info("음성 파일, 질문 추가: %s", file.filename)
            continue

        if ext in _IMAGE_EXTS:
            try:
                summary = _analyze_image(content, file.filename)
                summaries.append(f"[이미지: {file.filename}]\n{summary}")
                logger.info("이미지 분석 완료: %s", file.filename)
            except Exception as e:
                logger.warning("이미지 분석 실패: file=%s, error=%s", file.filename, e)
                extra_questions.append(f"첨부하신 이미지 '{file.filename}'의 내용을 설명해주세요.")
            continue

        if ext in _TEXT_EXTS:
            raw = _extract_text(content, file.filename)
            if raw:
                summary = _summarize_text(raw, file.filename)
                summaries.append(f"[{file.filename}]\n{summary}")
                logger.info("문서 요약 완료: %s", file.filename)
            else:
                extra_questions.append(f"첨부하신 '{file.filename}' 파일의 내용을 설명해주세요.")
            continue

        # 지원하지 않는 형식
        extra_questions.append(f"첨부하신 '{file.filename}' 파일의 내용을 설명해주세요.")

    file_summary = "\n\n".join(summaries)
    return file_summary, extra_questions
