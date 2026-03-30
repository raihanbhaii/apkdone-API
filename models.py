from pydantic import BaseModel
from typing import List, Optional

class DownloadLink(BaseModel):
    name: str
    original_url: str
    clean_url: Optional[str] = None

class AppDetail(BaseModel):
    title: str
    slug: str
    url: str
    logo: Optional[str] = None
    version: str
    size: Optional[str] = None
    updated: Optional[str] = None
    requires_android: Optional[str] = None
    description: str = ""
    download_links: List[DownloadLink] = []

class AppItem(BaseModel):
    title: str
    url: str
    image: Optional[str] = None
