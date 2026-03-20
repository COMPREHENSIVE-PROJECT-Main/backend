import re


def split_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    # 단락/문장 경계 기준으로 분할
    boundaries = re.split(r'(\n\n+|(?<=\. )(?=[A-Z가-힣]))', text)
    segments: list[str] = []
    buf = ""
    for part in boundaries:
        buf += part
        if len(buf) >= chunk_size:
            segments.append(buf)
            buf = ""
    if buf.strip():
        segments.append(buf)

    if not segments:
        return [text] if text.strip() else []

    # chunk_size 초과 세그먼트 강제 분할
    chunks: list[str] = []
    for seg in segments:
        while len(seg) > chunk_size:
            chunks.append(seg[:chunk_size])
            seg = seg[chunk_size:]
        if seg.strip():
            chunks.append(seg)

    if not chunks:
        return []

    # overlap 적용
    result: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = result[-1][-overlap:] if len(result[-1]) >= overlap else result[-1]
        result.append(prev_tail + chunks[i])

    return result
