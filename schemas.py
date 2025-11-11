"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime

# Existing example schemas (kept for reference)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# IMMERZO-specific schemas

class OTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15, description="Indian phone number with country code or 10 digits")
    code: str = Field(..., min_length=4, max_length=8, description="OTP code")
    purpose: Literal["franchise", "mall"] = Field(..., description="Verification context")
    verified: bool = Field(False)
    expires_at: datetime

class FranchiseInquiry(BaseModel):
    full_name: str = Field(...)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    investment_capacity_lakhs: float = Field(..., ge=0)
    preferred_cities: str = Field(..., description="Comma separated cities")
    city_tier: Literal["Tier 1", "Tier 2"]
    message: Optional[str] = None
    otp_verified: bool = Field(False)

class MallInquiry(BaseModel):
    contact_name: str
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    mall_name: str
    location_city: str
    available_space_sqft: int = Field(..., ge=0)
    has_floorplan: bool = Field(False)
    floorplan_filename: Optional[str] = None
    message: Optional[str] = None
    otp_verified: bool = Field(False)
