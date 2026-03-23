from dataclasses import dataclass

from app.com.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HNSWConfig:
    space: str = "cosine"
    construction_ef: int = 200
    search_ef: int = 100
    M: int = 16

    def to_metadata_dict(self) -> dict:
        return {
            "hnsw:space": self.space,
            "hnsw:construction_ef": self.construction_ef,
            "hnsw:search_ef": self.search_ef,
            "hnsw:M": self.M,
        }


def get_default_config() -> HNSWConfig:
    return HNSWConfig()


def update_collection_index(collection, config: HNSWConfig) -> None:
    try:
        collection.modify(metadata=config.to_metadata_dict())
        logger.info(f"Updated HNSW index config for collection: {collection.name}")
    except Exception as e:
        logger.error(f"Failed to update HNSW index config: {e}")
        raise
