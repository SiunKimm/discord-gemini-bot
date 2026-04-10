from typing import List


def chunk_text(text: str, chunk_size: int = 1900) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size는 1 이상의 정수여야 합니다.")
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
