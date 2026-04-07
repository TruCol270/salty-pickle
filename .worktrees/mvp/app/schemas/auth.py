from pydantic import BaseModel


class OAuthStateResponse(BaseModel):
    auth_url: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
