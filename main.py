from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from exception import add_global_exception_handler
from router import router
from schemas import ErrorResponse

app = FastAPI(
    root_path="/moduleapi",
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
app.include_router(router)
add_global_exception_handler(app)
