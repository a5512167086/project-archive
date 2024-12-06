from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class GlobalErrorException(Exception):
    def __init__(self, error_code: str, error_message: str):
        self.error_code = error_code
        self.error_message = error_message


def add_global_exception_handler(app: FastAPI):
    @app.exception_handler(GlobalErrorException)
    async def global_exception_handler(request: Request, exc: GlobalErrorException):
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "error_message": exc.error_message,
            }
        )
