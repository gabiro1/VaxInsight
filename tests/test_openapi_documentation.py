from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}

EXPECTED_OPERATIONS = {
    "/": {"get"},
    "/api/v1/health": {"get"},
    "/api/v1/health/database": {"get"},
    "/api/v1/narratives": {"get", "post"},
    "/api/v1/narratives/{narrative_id}": {"get", "patch"},
    "/api/v1/narratives/{narrative_id}/history": {"get"},
    "/api/v1/narratives/{narrative_id}/assignment": {"post"},
    "/api/v1/narratives/{narrative_id}/assignment/reassign": {"post"},
    "/api/v1/narratives/{narrative_id}/assignment/revoke": {"post"},
    "/api/v1/reviews/assignments": {"get"},
    "/api/v1/reviews/assignments/{assignment_id}": {"get"},
    "/api/v1/reviews/assignments/{assignment_id}/status": {"get", "post"},
    "/api/v1/reviews/assignments/{assignment_id}/review": {"post"},
    "/api/v1/reviews/assignments/{assignment_id}/history": {"get"},
    "/api/v1/auth/register": {"post"},
    "/api/v1/auth/login": {"post"},
    "/api/v1/auth/invitations": {"post"},
    "/api/v1/auth/invitations/accept": {"post"},
    "/api/v1/auth/refresh": {"post"},
    "/api/v1/auth/logout": {"post"},
    "/api/v1/auth/logout-all": {"post"},
    "/api/v1/auth/password/change": {"post"},
    "/api/v1/auth/password-reset/request": {"post"},
    "/api/v1/auth/password-reset/confirm": {"post"},
    "/api/v1/auth/email/verify": {"post"},
    "/api/v1/auth/email/verify/resend": {"post"},
    "/api/v1/auth/me": {"get", "patch", "delete"},
    "/api/v1/auth/admin/users/{user_id}/status": {"patch"},
    "/api/v1/auth/admin/users/{user_id}/role": {"patch"},
    "/api/v1/auth/token-check": {"get"},
    "/api/v1/admin/audit-events": {"get"},
    "/api/v1/admin/invitations": {"get"},
    "/api/v1/admin/invitations/{invitation_id}": {"get", "delete"},
    "/api/v1/admin/invitations/{invitation_id}/revoke": {"post"},
    "/api/v1/admin/users": {"get"},
    "/api/v1/admin/users/{user_id}": {"get"},
    "/api/v1/admin/users/{user_id}/permissions": {"get"},
    "/api/v1/admin/dashboard/summary": {"get"},
    "/api/v1/dashboard/summary": {"get"},
    "/api/v1/admin/permissions": {"get"},
    "/api/v1/admin/roles": {"get"},
    "/api/v1/admin/roles/{role}": {"get"},
    "/api/v1/vaccine-content": {"get"},
    "/api/v1/vaccine-content/{content_id}": {"get"},
    "/api/v1/admin/vaccine-content": {"post"},
    "/api/v1/questions": {"get", "post"},
    "/api/v1/questions/{question_id}": {"get"},
    "/api/v1/questions/{question_id}/analysis": {"post"},
    "/api/v1/review/questions": {"get"},
    "/api/v1/review/questions/{question_id}": {"get"},
    "/api/v1/review/questions/{question_id}/response": {"post"},
}

EXPECTED_TAGS = {
    "/": "Health",
    "/api/v1/health": "Health",
    "/api/v1/health/database": "Health",
    "/api/v1/narratives": "Narratives",
    "/api/v1/narratives/{narrative_id}": "Narratives",
    "/api/v1/narratives/{narrative_id}/history": "Narratives",
    "/api/v1/narratives/{narrative_id}/assignment": "Narrative Reviews",
    "/api/v1/narratives/{narrative_id}/assignment/reassign": "Narrative Reviews",
    "/api/v1/narratives/{narrative_id}/assignment/revoke": "Narrative Reviews",
    "/api/v1/reviews/assignments": "Narrative Reviews",
    "/api/v1/reviews/assignments/{assignment_id}": "Narrative Reviews",
    "/api/v1/reviews/assignments/{assignment_id}/status": "Narrative Reviews",
    "/api/v1/reviews/assignments/{assignment_id}/review": "Narrative Reviews",
    "/api/v1/reviews/assignments/{assignment_id}/history": "Narrative Reviews",
    "/api/v1/auth/register": "Authentication",
    "/api/v1/auth/login": "Authentication",
    "/api/v1/auth/invitations": "Invitation Management",
    "/api/v1/auth/invitations/accept": "Invitation Management",
    "/api/v1/auth/refresh": "Authentication",
    "/api/v1/auth/logout": "Accounts",
    "/api/v1/auth/logout-all": "Accounts",
    "/api/v1/auth/password/change": "Accounts",
    "/api/v1/auth/password-reset/request": "Accounts",
    "/api/v1/auth/password-reset/confirm": "Accounts",
    "/api/v1/auth/email/verify": "Accounts",
    "/api/v1/auth/email/verify/resend": "Accounts",
    "/api/v1/auth/me": "Accounts",
    "/api/v1/auth/admin/users/{user_id}/status": "User Management",
    "/api/v1/auth/admin/users/{user_id}/role": "User Management",
    "/api/v1/auth/token-check": "Authentication",
    "/api/v1/admin/audit-events": "Audit Logs",
    "/api/v1/admin/invitations": "Invitation Management",
    "/api/v1/admin/invitations/{invitation_id}": "Invitation Management",
    "/api/v1/admin/invitations/{invitation_id}/revoke": "Invitation Management",
    "/api/v1/admin/users": "User Management",
    "/api/v1/admin/users/{user_id}": "User Management",
    "/api/v1/admin/users/{user_id}/permissions": "Permission Management",
    "/api/v1/admin/dashboard/summary": "Administrator Dashboard",
    "/api/v1/dashboard/summary": "Dashboard",
    "/api/v1/admin/permissions": "Permission Management",
    "/api/v1/admin/roles": "Permission Management",
    "/api/v1/admin/roles/{role}": "Permission Management",
    "/api/v1/vaccine-content": "Vaccine Content",
    "/api/v1/vaccine-content/{content_id}": "Vaccine Content",
    "/api/v1/admin/vaccine-content": "Vaccine Content",
    "/api/v1/questions": "Questions",
    "/api/v1/questions/{question_id}": "Questions",
    "/api/v1/questions/{question_id}/analysis": "Questions",
    "/api/v1/review/questions": "Question Reviews",
    "/api/v1/review/questions/{question_id}": "Question Reviews",
    "/api/v1/review/questions/{question_id}/response": "Question Reviews",
}

EXPECTED_RESPONSES = {
    ("/", "get"): {"200"},
    ("/api/v1/health", "get"): {"200"},
    ("/api/v1/health/database", "get"): {"200", "503"},
    ("/api/v1/narratives", "get"): {"200", "401", "422"},
    ("/api/v1/narratives", "post"): {"201", "401", "422"},
    ("/api/v1/narratives/{narrative_id}", "get"): {
        "200",
        "401",
        "404",
        "422",
    },
    ("/api/v1/narratives/{narrative_id}", "patch"): {
        "200",
        "401",
        "404",
        "409",
        "422",
    },
    ("/api/v1/narratives/{narrative_id}/history", "get"): {
        "200",
        "401",
        "404",
        "422",
    },
    ("/api/v1/narratives/{narrative_id}/assignment", "post"): {
        "201",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/narratives/{narrative_id}/assignment/reassign", "post"): {
        "200",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/narratives/{narrative_id}/assignment/revoke", "post"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/reviews/assignments", "get"): {"200", "401", "403", "422"},
    ("/api/v1/reviews/assignments/{assignment_id}", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/reviews/assignments/{assignment_id}/status", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/reviews/assignments/{assignment_id}/status", "post"): {
        "200",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/reviews/assignments/{assignment_id}/review", "post"): {
        "201",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/reviews/assignments/{assignment_id}/history", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/auth/register", "post"): {"201", "403", "409", "422", "429", "503"},
    ("/api/v1/auth/login", "post"): {"200", "401", "422", "429", "503"},
    ("/api/v1/auth/invitations", "post"): {
        "201",
        "401",
        "403",
        "409",
        "422",
        "429",
        "503",
    },
    ("/api/v1/auth/invitations/accept", "post"): {
        "200",
        "400",
        "409",
        "422",
        "429",
        "503",
    },
    ("/api/v1/auth/refresh", "post"): {"200", "401", "422", "429", "503"},
    ("/api/v1/auth/logout", "post"): {"200", "401", "422"},
    ("/api/v1/auth/logout-all", "post"): {"200", "401"},
    ("/api/v1/auth/password/change", "post"): {"200", "400", "401", "422"},
    ("/api/v1/auth/password-reset/request", "post"): {"202", "422", "429", "503"},
    ("/api/v1/auth/password-reset/confirm", "post"): {
        "200",
        "400",
        "422",
        "429",
        "503",
    },
    ("/api/v1/auth/email/verify", "post"): {
        "200",
        "400",
        "403",
        "422",
        "429",
        "503",
    },
    ("/api/v1/auth/email/verify/resend", "post"): {"202", "422", "429", "503"},
    ("/api/v1/auth/me", "get"): {"200", "401"},
    ("/api/v1/auth/me", "patch"): {"200", "401", "409", "422", "503"},
    ("/api/v1/auth/me", "delete"): {"200", "401", "409"},
    ("/api/v1/auth/admin/users/{user_id}/status", "patch"): {
        "200",
        "400",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/auth/admin/users/{user_id}/role", "patch"): {
        "200",
        "400",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/auth/token-check", "get"): {"200", "401"},
    ("/api/v1/admin/audit-events", "get"): {"200", "401", "403", "422"},
    ("/api/v1/admin/invitations", "get"): {"200", "401", "403", "422"},
    ("/api/v1/admin/invitations/{invitation_id}", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/admin/invitations/{invitation_id}", "delete"): {
        "200",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/admin/invitations/{invitation_id}/revoke", "post"): {
        "200",
        "401",
        "403",
        "404",
        "409",
        "422",
    },
    ("/api/v1/admin/users", "get"): {"200", "401", "403", "422"},
    ("/api/v1/admin/users/{user_id}", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/admin/users/{user_id}/permissions", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
    },
    ("/api/v1/admin/dashboard/summary", "get"): {"200", "401", "403"},
    ("/api/v1/dashboard/summary", "get"): {"200", "401", "403"},
    ("/api/v1/admin/permissions", "get"): {"200", "401", "403"},
    ("/api/v1/admin/roles", "get"): {"200", "401", "403"},
    ("/api/v1/admin/roles/{role}", "get"): {"200", "401", "403", "422"},
    ("/api/v1/vaccine-content", "get"): {"200", "401", "403", "422", "503"},
    ("/api/v1/vaccine-content/{content_id}", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
        "503",
    },
    ("/api/v1/admin/vaccine-content", "post"): {
        "201",
        "401",
        "403",
        "409",
        "422",
        "503",
    },
    ("/api/v1/questions", "get"): {"200", "401", "403", "503"},
    ("/api/v1/questions", "post"): {
        "201",
        "401",
        "403",
        "422",
        "429",
        "503",
    },
    ("/api/v1/questions/{question_id}", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
        "503",
    },
    ("/api/v1/questions/{question_id}/analysis", "post"): {
        "201",
        "401",
        "403",
        "404",
        "422",
        "429",
        "503",
    },
    ("/api/v1/review/questions", "get"): {"200", "401", "403", "503"},
    ("/api/v1/review/questions/{question_id}", "get"): {
        "200",
        "401",
        "403",
        "404",
        "422",
        "503",
    },
    ("/api/v1/review/questions/{question_id}/response", "post"): {
        "201",
        "401",
        "403",
        "404",
        "422",
        "503",
    },
}

PROTECTED_OPERATIONS = {
    ("/api/v1/auth/invitations", "post"),
    ("/api/v1/narratives", "get"),
    ("/api/v1/narratives", "post"),
    ("/api/v1/narratives/{narrative_id}", "get"),
    ("/api/v1/narratives/{narrative_id}", "patch"),
    ("/api/v1/narratives/{narrative_id}/history", "get"),
    ("/api/v1/narratives/{narrative_id}/assignment", "post"),
    ("/api/v1/narratives/{narrative_id}/assignment/reassign", "post"),
    ("/api/v1/narratives/{narrative_id}/assignment/revoke", "post"),
    ("/api/v1/reviews/assignments", "get"),
    ("/api/v1/reviews/assignments/{assignment_id}", "get"),
    ("/api/v1/reviews/assignments/{assignment_id}/status", "get"),
    ("/api/v1/reviews/assignments/{assignment_id}/status", "post"),
    ("/api/v1/reviews/assignments/{assignment_id}/review", "post"),
    ("/api/v1/reviews/assignments/{assignment_id}/history", "get"),
    ("/api/v1/auth/logout", "post"),
    ("/api/v1/auth/logout-all", "post"),
    ("/api/v1/auth/password/change", "post"),
    ("/api/v1/auth/me", "get"),
    ("/api/v1/auth/me", "patch"),
    ("/api/v1/auth/me", "delete"),
    ("/api/v1/auth/admin/users/{user_id}/status", "patch"),
    ("/api/v1/auth/admin/users/{user_id}/role", "patch"),
    ("/api/v1/auth/token-check", "get"),
    ("/api/v1/admin/audit-events", "get"),
    ("/api/v1/admin/invitations", "get"),
    ("/api/v1/admin/invitations/{invitation_id}", "get"),
    ("/api/v1/admin/invitations/{invitation_id}", "delete"),
    ("/api/v1/admin/invitations/{invitation_id}/revoke", "post"),
    ("/api/v1/admin/users", "get"),
    ("/api/v1/admin/users/{user_id}", "get"),
    ("/api/v1/admin/users/{user_id}/permissions", "get"),
    ("/api/v1/admin/dashboard/summary", "get"),
    ("/api/v1/dashboard/summary", "get"),
    ("/api/v1/admin/permissions", "get"),
    ("/api/v1/admin/roles", "get"),
    ("/api/v1/admin/roles/{role}", "get"),
    ("/api/v1/vaccine-content", "get"),
    ("/api/v1/vaccine-content/{content_id}", "get"),
    ("/api/v1/admin/vaccine-content", "post"),
    ("/api/v1/questions", "get"),
    ("/api/v1/questions", "post"),
    ("/api/v1/questions/{question_id}", "get"),
    ("/api/v1/questions/{question_id}/analysis", "post"),
    ("/api/v1/review/questions", "get"),
    ("/api/v1/review/questions/{question_id}", "get"),
    ("/api/v1/review/questions/{question_id}/response", "post"),
}


def _operation(document, path, method):
    return document["paths"][path][method]


def _response_schema(operation, status_code):
    response = operation["responses"][status_code]
    return response["content"]["application/json"]["schema"]


def test_openapi_document_is_generated_and_served():
    document = app.openapi()
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json() == document
    assert document["info"]["title"] == "VaxInsight API"
    assert document["info"]["version"] == "1.0.0"


def test_openapi_contains_every_registered_endpoint_and_method():
    document = app.openapi()

    actual_operations = {
        path: {method for method in path_item if method in HTTP_METHODS}
        for path, path_item in document["paths"].items()
    }

    assert actual_operations == EXPECTED_OPERATIONS


def test_openapi_operations_have_tags_summaries_descriptions_and_statuses():
    document = app.openapi()

    assert {tag["name"] for tag in document["tags"]} == {
        "Health",
        "Authentication",
        "Accounts",
        "Invitation Management",
        "User Management",
        "Administrator Dashboard",
        "Dashboard",
        "Audit Logs",
        "Permission Management",
        "Narratives",
        "Narrative Reviews",
        "Vaccine Content",
        "Questions",
        "Question Reviews",
    }

    for path, methods in EXPECTED_OPERATIONS.items():
        for method in methods:
            operation = _operation(document, path, method)
            assert operation["tags"] == [EXPECTED_TAGS[path]]
            assert operation["summary"]
            assert operation["description"]
            assert set(operation["responses"]) == EXPECTED_RESPONSES[(path, method)]
            for response in operation["responses"].values():
                assert response["description"]


def test_openapi_documents_jwt_security_for_protected_operations():
    document = app.openapi()

    assert document["components"]["securitySchemes"] == {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT access token. Send the token in the Authorization header as "
                "`Bearer <access_token>`."
            ),
        }
    }

    for path, methods in PROTECTED_OPERATIONS:
        operation = _operation(document, path, methods)
        assert operation["security"] == [{"BearerAuth": []}]

    for path, methods in EXPECTED_OPERATIONS.items():
        for method in methods:
            if (path, method) not in PROTECTED_OPERATIONS:
                assert "security" not in _operation(document, path, method)


def test_openapi_documents_request_and_response_models():
    document = app.openapi()

    login = _operation(document, "/api/v1/auth/login", "post")
    assert (
        login["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/UserLogin"
    )
    assert (
        _response_schema(login, "200")["$ref"] == "#/components/schemas/TokenResponse"
    )

    user_directory = _operation(document, "/api/v1/admin/users", "get")
    assert _response_schema(user_directory, "200")["$ref"] == (
        "#/components/schemas/AdminUserPageResponse"
    )
    assert all(parameter["description"] for parameter in user_directory["parameters"])

    status_update = _operation(
        document,
        "/api/v1/auth/admin/users/{user_id}/status",
        "patch",
    )
    assert (
        status_update["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/AccountStatusUpdate"
    )
    assert _response_schema(status_update, "200")["$ref"] == (
        "#/components/schemas/UserResponse"
    )
    assert _response_schema(status_update, "401")["$ref"] == (
        "#/components/schemas/ErrorResponse"
    )
    assert _response_schema(status_update, "422")["$ref"] == (
        "#/components/schemas/ValidationErrorResponse"
    )

    narrative_create = _operation(document, "/api/v1/narratives", "post")
    assert (
        narrative_create["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/NarrativeCreate"
    )
    assert _response_schema(narrative_create, "201")["$ref"] == (
        "#/components/schemas/NarrativeResponse"
    )

    narrative_history = _operation(
        document,
        "/api/v1/narratives/{narrative_id}/history",
        "get",
    )
    assert _response_schema(narrative_history, "200")["$ref"] == (
        "#/components/schemas/NarrativeRevisionPageResponse"
    )

    personal_dashboard = _operation(document, "/api/v1/dashboard/summary", "get")
    assert _response_schema(personal_dashboard, "200")["$ref"] == (
        "#/components/schemas/PersonalDashboardSummaryResponse"
    )

    reset_request = _operation(
        document,
        "/api/v1/auth/password-reset/request",
        "post",
    )
    assert _response_schema(reset_request, "202")["$ref"] == (
        "#/components/schemas/MessageResponse"
    )
    assert reset_request["responses"]["429"]["headers"]["Retry-After"]["schema"] == {
        "type": "integer",
        "minimum": 0,
    }

    resend_verification = _operation(
        document,
        "/api/v1/auth/email/verify/resend",
        "post",
    )
    assert (
        resend_verification["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ]
        == "#/components/schemas/EmailVerificationResendRequest"
    )

    narrative_response = document["components"]["schemas"]["NarrativeResponse"]
    assert "review_status" in narrative_response["properties"]
    assert "owner" in narrative_response["properties"]["review_status"]["description"]
    assert "notes" not in narrative_response["properties"]


def test_public_response_schemas_do_not_expose_sensitive_fields():
    document = app.openapi()
    schemas = document["components"]["schemas"]
    public_response_models = {
        "AdminInvitationPageResponse",
        "AdminInvitationResponse",
        "AdminUserPageResponse",
        "AdminUserResponse",
        "AuditEventPageResponse",
        "AuditEventResponse",
        "DatabaseHealthResponse",
        "DashboardSummaryResponse",
        "PersonalDashboardSummaryResponse",
        "ErrorResponse",
        "HealthResponse",
        "InvitationResponse",
        "MessageResponse",
        "AssignedNarrativeResponse",
        "NarrativeAssignmentPageResponse",
        "NarrativeAssignmentResponse",
        "NarrativePageResponse",
        "NarrativeResponse",
        "NarrativeRevisionPageResponse",
        "NarrativeRevisionResponse",
        "NarrativeReviewHistoryResponse",
        "NarrativeReviewResponse",
        "PermissionCatalogueResponse",
        "PermissionResponse",
        "RolePermissionsPageResponse",
        "RolePermissionsResponse",
        "ReviewEvidenceResponse",
        "RootResponse",
        "TokenCheckResponse",
        "UserPermissionsResponse",
        "UserResponse",
        "ValidationErrorResponse",
    }
    sensitive_names = {
        "access_token",
        "hashed_password",
        "password",
        "refresh_token",
        "secret_key",
        "smtp_password",
        "token",
        "token_hash",
    }

    for model_name in public_response_models:
        properties = schemas[model_name].get("properties", {})
        assert sensitive_names.isdisjoint(properties), model_name

    token_response_operations = {
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/invitations/accept", "post"),
        ("/api/v1/auth/refresh", "post"),
        ("/api/v1/auth/email/verify", "post"),
    }
    for path, methods in EXPECTED_OPERATIONS.items():
        for method in methods:
            operation = _operation(document, path, method)
            response_refs = {
                response["content"]["application/json"]["schema"].get("$ref")
                for response in operation["responses"].values()
                if "content" in response and "application/json" in response["content"]
            }
            if (path, method) in token_response_operations:
                assert "#/components/schemas/TokenResponse" in response_refs
            else:
                assert "#/components/schemas/TokenResponse" not in response_refs
