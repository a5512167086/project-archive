from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from router import router, privtate_router
from exception import add_global_exception_handler
from schemas import ErrorResponse
import uvicorn


app = FastAPI(
    root_path='/easybot/botapi',
    docs_url='/',
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}})
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(privtate_router)
add_global_exception_handler(app)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8001, reload=True)
