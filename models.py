from typing import List, Optional
from pydantic import BaseModel


class MediaItem(BaseModel):
    id: Optional[str] = None
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    alt: Optional[str] = None
    is_video: bool = False


class SearchResponse(BaseModel):
    query: str
    count: int
    cached: bool
    items: List[MediaItem]
