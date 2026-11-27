from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ExtractionRequest(BaseModel):
    url: HttpUrl
    target_price: Optional[float] = Field(
        default=None, gt=0, description="Optional target price to trigger an email alert."
    )


class ProductData(BaseModel):
    url: str
    title: str
    price: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=10)
    in_stock: bool = True
    key_specs: list[str] = Field(default_factory=list)
    extracted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    alert_sent: bool = False


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3)
