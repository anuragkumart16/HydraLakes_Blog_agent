import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

# router imports
from routes.auth_routes import auth_router, decode_access_token
from routes.recipient_routes import recipient_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

# TODO : create email login system later
@app.get("/login-email", response_class=HTMLResponse)
async def login_email(request: Request):
    return templates.TemplateResponse(request=request, name="login_email.html", context={"user_name": "Team Member", "login_url": "http://localhost:8000/login", "otp_code": "849-204", "expiration_minutes": "15"})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Extract token from cookie or Authorization header
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return RedirectResponse(url="/login", status_code=307)

    try:
        payload = decode_access_token(token)
        user_name = payload.get("username") or payload.get("email", "User")
        return templates.TemplateResponse(request=request, name="dashboard.html", context={"user_name": user_name})
    except Exception:
        return RedirectResponse(url="/login", status_code=307)

@app.get("/recipients", response_class=HTMLResponse)
async def recipients_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return RedirectResponse(url="/login", status_code=307)

    try:
        payload = decode_access_token(token)
        user_name = payload.get("username") or payload.get("email", "User")
        return templates.TemplateResponse(request=request, name="recipients.html", context={"user_name": user_name})
    except Exception:
        return RedirectResponse(url="/login", status_code=307)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(recipient_router, prefix="/api/v1/recipients", tags=["Recipients"])