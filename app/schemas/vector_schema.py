from pydantic import BaseModel


class VectorDocument(BaseModel):
    document_id: str
    content: str
    embedding: list[float]
    metadata: dict


class VectorInsertRequest(BaseModel):
    documents: list[VectorDocument]


class VectorInsertResponse(BaseModel):
    inserted_count: int
    collection: str


class VectorDeleteRequest(BaseModel):
    document_ids: list[str]
