from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from exception import add_global_exception_handler
from router import privtate_router, router
from schemas import ErrorResponse

app = FastAPI(
    root_path="/userapi",
    docs_url="/",
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_global_exception_handler(app)
app.include_router(router)
app.include_router(privtate_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )
