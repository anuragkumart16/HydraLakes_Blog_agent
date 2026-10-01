from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username : str
    password : str
    email : EmailStr

class UserLogin(BaseModel):
    email : EmailStr
    password : str

class UserResponse(BaseModel):
    id : str
    username : str
    email : EmailStr