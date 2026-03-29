from pydantic import BaseModel
from typing import List, Optional

class DownloadLink(BaseModel):
    name: str
    original_url: str          # hidden
    clean_url: Optional[str] = None   # public: /d/slug-1
    size: Optional[str] = None
    direct_apk: bool = False

class OldVersion(BaseModel):
    version: str
    date: Optional[str] = None
    download_url: str

class AppDetail(BaseModel):
    title: str
    slug: str
    url: str
    logo: Optional[str] = None
    version: str
    size: Optional[str] = None
    developer: Optional[str] = None
    category: Optional[str] = None
    requires_android: Optional[str] = None
    updated: Optional[str] = None
    description: str
    screenshots: List[str] = []
    download_links: List[DownloadLink] = []
    old_versions: List[OldVersion] = []

class AppItem(BaseModel):
    title: str
    url: str
    image: Optional[str] = None
