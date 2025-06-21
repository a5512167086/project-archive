from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from exception import add_global_exception_handler
from models import *  # noqa: F403
from routers.bot_router import bot_router
from routers.knowledge_router import knowledge_router
from routers.module_router import module_router
from routers.reservation_router import reservation_router
from routers.user_router import user_router
from schemas.common_schema import ErrorResponse

app = FastAPI(responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:5173",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://platform-web-gnod.onrender.com",
        "https://liff-web.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_global_exception_handler(app)

app.include_router(user_router)
app.include_router(knowledge_router)
app.include_router(module_router)
app.include_router(bot_router)
app.include_router(reservation_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )
