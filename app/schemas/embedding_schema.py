from pydantic import BaseModel


class EmbedRequest(BaseModel):
    text: str
    model: str | None = None


class EmbedResponse(BaseModel):
    embedding: list[float]
    dim: int


class VectorSearchRequest(BaseModel):
    query_text: str
    top_n: int = 5


class VectorSearchResult(BaseModel):
    document_id: str
    content: str
    score: float
    metadata: dict
