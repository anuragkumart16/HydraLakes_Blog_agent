from fastapi import Request
from fastapi import APIRouter

auth_router = APIRouter()

@auth_router.get("/password-login")
async def password_login(request:Request):
    return ({
        "message" : "working!"
    })