from pydantic import BaseModel

class LoginRequest(BaseModel):
    identifier: str  # può essere username o email
    password: str

class LoginResponse(BaseModel):
    status: str