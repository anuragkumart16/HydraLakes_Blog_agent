from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

# router imports
from routes.auth_routes import auth_router

templates = Jinja2Templates(directory="src/templates")


app = FastAPI()

@app.get("/",response_class = HTMLResponse)
async def root(request:Request):
    return templates.TemplateResponse(request=request , name="index.html")

@app.get("/login",response_class = HTMLResponse)
async def login(request:Request):
    return templates.TemplateResponse(request=request , name="login.html")

# TODO : create email login system later
@app.get("/login-email", response_class=HTMLResponse)
async def login_email(request: Request):
    return templates.TemplateResponse(request=request, name="login_email.html", context={"user_name": "Team Member", "login_url": "http://localhost:8000/login", "otp_code": "849-204", "expiration_minutes": "15"})


app.include_router(auth_router, prefix="/api/v1/auth",tags=["Auth"])