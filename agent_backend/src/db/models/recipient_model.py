from pydantic import BaseModel, EmailStr
from typing import Optional

class RecipientCreate(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = "Stakeholder"
    is_active: bool = True

class RecipientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class RecipientResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: Optional[str] = None
