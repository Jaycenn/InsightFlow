import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router
from app.core import settings
from app.errors import AppError, app_error_handler, validation_error_handler

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
app = FastAPI(title="InsightFlow API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException):
    code = "UNAUTHORIZED" if exc.status_code == 401 else "HTTP_ERROR"
    return JSONResponse(
        status_code=exc.status_code, content={"error": {"code": code, "message": str(exc.detail), "details": []}}
    )


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)
