from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from bson import ObjectId

from db.client import db
from db.models.recipient_model import RecipientCreate, RecipientUpdate, RecipientResponse
from routes.auth_routes import decode_access_token

recipient_router = APIRouter()

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )

    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

def format_recipient(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "role": doc.get("role", "Stakeholder"),
        "is_active": doc.get("is_active", True),
        "created_at": doc.get("created_at", "")
    }

@recipient_router.post("/", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
async def create_recipient(recipient: RecipientCreate, user: dict = Depends(get_current_user)):
    existing = await db.recipients.find_one({"email": recipient.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recipient with email '{recipient.email}' already exists"
        )

    recipient_dict = recipient.model_dump()
    recipient_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    result = await db.recipients.insert_one(recipient_dict)
    created_doc = await db.recipients.find_one({"_id": result.inserted_id})

    return format_recipient(created_doc)

@recipient_router.get("/", response_model=List[RecipientResponse])
async def get_all_recipients(
    search: Optional[str] = Query(None, description="Search by name or email"),
    active_only: bool = Query(False, description="Filter active recipients only"),
    user: dict = Depends(get_current_user)
):
    query = {}
    if active_only:
        query["is_active"] = True

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"role": {"$regex": search, "$options": "i"}}
        ]

    cursor = db.recipients.find(query).sort("name", 1)
    recipients = []
    async for doc in cursor:
        recipients.append(format_recipient(doc))

    return recipients

@recipient_router.get("/{recipient_id}", response_model=RecipientResponse)
async def get_recipient_by_id(recipient_id: str, user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(recipient_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recipient ID format")

    doc = await db.recipients.find_one({"_id": ObjectId(recipient_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    return format_recipient(doc)

@recipient_router.put("/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(recipient_id: str, update_data: RecipientUpdate, user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(recipient_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recipient ID format")

    fields_to_update = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not fields_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    # Check if updated email conflicts with another recipient
    if "email" in fields_to_update:
        existing = await db.recipients.find_one({
            "email": fields_to_update["email"],
            "_id": {"$ne": ObjectId(recipient_id)}
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another recipient already uses email '{fields_to_update['email']}'"
            )

    result = await db.recipients.update_one(
        {"_id": ObjectId(recipient_id)},
        {"$set": fields_to_update}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    updated_doc = await db.recipients.find_one({"_id": ObjectId(recipient_id)})
    return format_recipient(updated_doc)

@recipient_router.delete("/{recipient_id}", status_code=status.HTTP_200_OK)
async def delete_recipient(recipient_id: str, user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(recipient_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recipient ID format")

    result = await db.recipients.delete_one({"_id": ObjectId(recipient_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    return {"message": "Recipient deleted successfully", "id": recipient_id}
