import ipaddress
from urllib.parse import urlparse
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_core import core_schema
from datetime import datetime
from typing import Optional, List, Any, Dict
from bson import ObjectId


def _is_ssrf_unsafe(url: str) -> bool:
    """Block private IPs, localhost, link-local, and non-http schemes (10.1)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return True
        hostname = parsed.hostname
        if not hostname:
            return True
        blocked_hosts = {'localhost', '127.0.0.1', '::1', '0.0.0.0', 'metadata.google.internal'}
        if hostname.lower() in blocked_hosts:
            return True
        if hostname.endswith('.local') or hostname.endswith('.internal'):
            return True
        try:
            ip = ipaddress.ip_address(hostname)
            return (ip.is_private or ip.is_loopback or
                    ip.is_link_local or ip.is_reserved or ip.is_multicast)
        except ValueError:
            pass  # Not an IP address — hostname is fine
        return False
    except Exception:
        return True


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class URLModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    group_name: Optional[str] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "url": "https://www.amazon.com/product/example",
                "group_name": "Electronics"
            }
        }


class URLCreateRequest(BaseModel):
    urls: List[str]
    group_name: Optional[str] = None

    @field_validator('urls', mode='before')
    @classmethod
    def validate_urls(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('At least one URL required')
        if len(v) > 500:
            raise ValueError('Maximum 500 URLs per request')
        for url in v:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f'URL must start with http:// or https://: {url}')
            if _is_ssrf_unsafe(url):
                raise ValueError(f'URL targets a private or reserved address: {url}')
        return [u.strip() for u in v]

    class Config:
        json_schema_extra = {
            "example": {
                "urls": [
                    "https://www.amazon.com/product1",
                    "https://www.shopify.com/product2"
                ],
                "group_name": "Test Group"
            }
        }


class ScanResult(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    url: str
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    add_to_cart: bool = False
    buy_now: bool = False
    status: str  # "available", "unavailable", "error"
    blocked_reason: Optional[str] = None
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    scrape_method: Optional[str] = None
    html_primary_source: Optional[str] = None
    variants: Optional[Dict[str, str]] = None
    variants_checked: Optional[bool] = None
    unavailability_override: Optional[bool] = None
    job_id: Optional[str] = None
    url_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "url": "https://www.amazon.com/product/example",
                "add_to_cart": True,
                "buy_now": True,
                "status": "available",
                "response_time": 2.5
            }
        }


class ScanRequest(BaseModel):
    url_ids: Optional[List[str]] = None  # If None, scan all URLs

    class Config:
        json_schema_extra = {
            "example": {
                "url_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
            }
        }


class ScanJobStatus(BaseModel):
    job_id: str
    status: str  # queued|running|done|failed|cancelled
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_urls: int = 0
    completed: int = 0
    success: int = 0
    error: int = 0
    available_count: int = 0
    unavailable_count: int = 0
    availability_summary: Optional[str] = None  # all_available|some_unavailable|none_available|unknown
    rate_urls_per_sec: Optional[float] = None
    eta_seconds: Optional[int] = None
    last_update_at: Optional[datetime] = None


class LogEntry(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    event_type: str
    details: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "INFO"  # INFO, WARNING, ERROR

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ScanResponse(BaseModel):
    message: str
    scanned_count: int
    results: List[ScanResult]


class URLResponse(BaseModel):
    id: str
    url: str
    created_at: datetime
    group_name: Optional[str] = None


class StatsResponse(BaseModel):
    total_urls: int
    total_scans: int
    available_count: int
    unavailable_count: int
    error_count: int
