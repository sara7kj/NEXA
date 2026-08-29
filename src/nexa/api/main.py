from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexa.auth.dependencies import UserContext, current_user, require
from nexa.auth.permissions import Permission
from nexa.auth.security import create_token, verify_password
from nexa.db.connection import engine
from nexa.db.models import User
from nexa.rag.store import load_retriever

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["retriever"] = load_retriever()
    yield
    state.clear()


app = FastAPI(title="NEXA", version="0.2.0", lifespan=lifespan)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class SearchHit(BaseModel):
    doc_id: str
    content: str
    score: float


class MeResponse(BaseModel):
    user_id: str
    full_name: str
    role: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.email == body.email))

        if user is None or not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "invalid email or password"
            )
        if not user.is_active:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "invalid email or password"
            )

        return TokenResponse(
            access_token=create_token(user.id, user.role), role=user.role
        )


@app.get("/auth/me", response_model=MeResponse)
def me(user: UserContext = Depends(current_user)) -> MeResponse:
    return MeResponse(
        user_id=user.user_id, full_name=user.full_name, role=user.role.value
    )


@app.get("/search", response_model=list[SearchHit])
def search(
    q: str = Query(min_length=3, max_length=500),
    user: UserContext = Depends(require(Permission.KB_READ)),
) -> list[SearchHit]:
    retriever = state.get("retriever")
    if retriever is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "not ready")

    return [
        SearchHit(doc_id=r.doc_id, content=r.content, score=r.score)
        for r in retriever.search(q)
    ]