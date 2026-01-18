from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from modules.bot.bot_router import bot_router
from modules.ecomm.ecomm_router import (
    brand_router,
    category_router,
    ecomm_router,
    order_router,
    product_router,
)
from modules.knowledge.knowledge_router import knowledge_router
from modules.module.module_router import module_router
from modules.reservation.reservation_router import reservation_router, service_router
from modules.user.user_router import user_router
from shared.clients.mongodb import init_monogo_db
from shared.exception import add_global_exception_handler
from shared.models import *  # noqa: F403
from shared.schemas.common_schema import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_monogo_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
    root_path="/easybot-api",
)
Instrumentator().instrument(app).expose(app)
# Global exception handler
add_global_exception_handler(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://localhost:5173",
        "http://127.0.0.1:5173",
        "https://127.0.0.1:5173",
        "http://localhost:5174",
        "https://localhost:5174",
        "http://127.0.0.1:5174",
        "https://127.0.0.1:5174",
        "https://platform-web-gnod.onrender.com",
        "https://liff-web.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# User module routers
app.include_router(user_router)
# Knowledge module routers
app.include_router(knowledge_router)
# Module setting routers
app.include_router(module_router)
# Bot module routers
app.include_router(bot_router)
# Reservation module routers
app.include_router(reservation_router)
app.include_router(service_router)
# E-commerce module routers
app.include_router(ecomm_router)
app.include_router(brand_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(order_router)
