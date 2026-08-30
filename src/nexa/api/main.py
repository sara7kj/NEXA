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
from nexa.approvals.service import create_request, decide, get_request, list_pending
from nexa.tools import execute_tool, registry

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

class ApprovalDecision(BaseModel):
    approve: bool
    reason: str | None = None


class StatusChangeRequest(BaseModel):
    code: str
    new_status: str
    reason: str


@app.post("/projects/request-status-change")
def request_status_change(
    body: StatusChangeRequest,
    user: UserContext = Depends(require(Permission.PROJECTS_UPDATE_STATUS)),
) -> dict:
    details = execute_tool("get_project_details", {"code": body.code}, user)
    if not details.data.get("found"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")

    current = details.data["status"]

    arguments = {
        "code": body.code.upper(),
        "new_status": body.new_status,
        "reason": body.reason,
        "expected_current_status": current,
    }

    tool = registry.get("update_project_status")
    try:
        tool.input_schema(**arguments)
    except Exception as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))

    request_id = create_request(
        "update_project_status",
        arguments,
        "project",
        body.code.upper(),
        {"status": current},
        {"status": body.new_status},
        body.reason,
        user,
    )

    return {
        "submitted": True,
        "executed": False,
        "approval_request_id": request_id,
        "message": (
            f"Request submitted for approval. {body.code.upper()} is still "
            f"'{current}'. No change has been made."
        ),
    }


@app.get("/approvals/pending")
def pending(
    user: UserContext = Depends(require(Permission.APPROVALS_DECIDE)),
) -> list[dict]:
    return list_pending(user)


@app.get("/approvals/{request_id}")
def approval_detail(
    request_id: str, user: UserContext = Depends(current_user)
) -> dict:
    found = get_request(request_id, user)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "request not found")
    return found


@app.post("/approvals/{request_id}/decide")
def approval_decide(
    request_id: str,
    body: ApprovalDecision,
    user: UserContext = Depends(require(Permission.APPROVALS_DECIDE)),
) -> dict:
    result = decide(request_id, body.approve, user, body.reason)

    if not result.get("ok") and result.get("error_code"):
        raise HTTPException(status.HTTP_409_CONFLICT, result["error_code"])

    return result

