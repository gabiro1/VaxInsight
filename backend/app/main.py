from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    admin,
    auth,
    dashboard,
    health,
    narratives,
    questions,
    reviews,
    vaccine_content,
)
from app.core.config import settings
from app.schemas.common import RootResponse
from app.services.narratives import NarrativePersistenceError
from app.services.questions import QuestionPersistenceError
from app.services.rate_limit import RateLimitExceeded, RateLimitUnavailable
from app.services.reviews import ReviewPersistenceError
from app.services.vaccine_content import VaccineContentPersistenceError

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Application and database availability checks.",
    },
    {
        "name": "Authentication",
        "description": "Registration, login, token issuance, and token verification.",
    },
    {
        "name": "Accounts",
        "description": "Authenticated account, password, and email-management actions.",
    },
    {
        "name": "Invitation Management",
        "description": "Invitation creation, acceptance, listing, and revocation.",
    },
    {
        "name": "User Management",
        "description": "Administrator-only user directory and account-management actions.",
    },
    {
        "name": "Administrator Dashboard",
        "description": "Administrator-only operational summary statistics.",
    },
    {
        "name": "Dashboard",
        "description": "Authenticated-user activity and owned-record summaries.",
    },
    {
        "name": "Audit Logs",
        "description": "Administrator-only audit event search and pagination.",
    },
    {
        "name": "Permission Management",
        "description": (
            "Administrator-only permission catalogue and role assignment inspection."
        ),
    },
    {
        "name": "Narratives",
        "description": (
            "Owner-scoped narrative records and immutable history; no model output."
        ),
    },
    {
        "name": "Narrative Reviews",
        "description": (
            "Human reviewer assignments, structured review records, evidence, and "
            "explicit escalation status."
        ),
    },
    {
        "name": "Vaccine Content",
        "description": (
            "Published official vaccine content and administrator-managed registry "
            "records."
        ),
    },
    {
        "name": "Questions",
        "description": (
            "Owner-scoped community vaccine questions and separate analysis runs."
        ),
    },
    {
        "name": "Question Reviews",
        "description": (
            "Reviewer-only queue and public professional responses for community "
            "questions."
        ),
    },
]


def documentation_url(app_env: str) -> str | None:
    """Keep the generated OpenAPI document out of production deployments."""

    return None if app_env == "production" else "/openapi.json"


app = FastAPI(
    title="VaxInsight API",
    description=(
        "Backend API for the VaxInsight mobile application. Protected endpoints "
        "use JWT bearer access tokens obtained from the authentication endpoints."
    ),
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    openapi_url=documentation_url(settings.APP_ENV),
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
)

allowed_origins = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith(
        (
            "/api/v1/auth",
            "/api/v1/admin",
            "/api/v1/dashboard",
            "/api/v1/narratives",
            "/api/v1/reviews",
            "/api/v1/vaccine-content",
            "/api/v1/admin/vaccine-content",
            "/api/v1/questions",
            "/api/v1/review/questions",
        )
    ):
        response.headers.setdefault("Cache-Control", "no-store")
    if settings.APP_ENV == "production":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request,
    error: RateLimitExceeded,
):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"},
        headers={"Retry-After": str(error.retry_after)},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request,
    error: RequestValidationError,
):
    """Return validation details without echoing submitted request values."""

    sanitized_errors = [
        {key: value for key, value in detail.items() if key != "input"}
        for detail in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(sanitized_errors)},
    )


@app.exception_handler(RateLimitUnavailable)
async def rate_limit_unavailable_handler(
    request: Request,
    error: RateLimitUnavailable,
):
    return JSONResponse(
        status_code=503,
        content={"detail": "Request protection is temporarily unavailable"},
    )


@app.exception_handler(NarrativePersistenceError)
async def narrative_persistence_error_handler(
    request: Request,
    error: NarrativePersistenceError,
):
    return JSONResponse(
        status_code=503,
        content={"detail": "Narrative storage is temporarily unavailable"},
    )


@app.exception_handler(ReviewPersistenceError)
async def review_persistence_error_handler(
    request: Request,
    error: ReviewPersistenceError,
):
    return JSONResponse(
        status_code=503,
        content={"detail": "Review storage is temporarily unavailable"},
    )


@app.exception_handler(VaccineContentPersistenceError)
async def vaccine_content_persistence_error_handler(
    request: Request,
    error: VaccineContentPersistenceError,
):
    return JSONResponse(
        status_code=503,
        content={"detail": "Vaccine content storage is temporarily unavailable"},
    )


@app.exception_handler(QuestionPersistenceError)
async def question_persistence_error_handler(
    request: Request,
    error: QuestionPersistenceError,
):
    return JSONResponse(
        status_code=503,
        content={"detail": "Question storage is temporarily unavailable"},
    )


app.include_router(
    health.router,
    prefix="/api/v1",
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
)

app.include_router(
    dashboard.router,
    prefix="/api/v1",
)

app.include_router(
    narratives.router,
    prefix="/api/v1",
)

app.include_router(
    reviews.router,
    prefix="/api/v1",
)

app.include_router(
    vaccine_content.router,
    prefix="/api/v1",
)

app.include_router(
    questions.router,
    prefix="/api/v1",
)


@app.get(
    "/",
    response_model=RootResponse,
    response_description="API welcome information.",
    summary="Show API welcome information",
    description=(
        "Return the API welcome message and the interactive documentation path "
        "when documentation is enabled for the current environment."
    ),
    tags=["Health"],
)
async def root():
    return {
        "message": "Welcome to VaxInsight API",
        "documentation": "/docs" if settings.APP_ENV != "production" else None,
    }
