from fastapi import FastAPI
from fastapi.responses import JSONResponse


class GlobalErrorException(Exception):
    def __init__(
        self,
        error_code: str,
        error_message: str,
        status_code: int = 400,
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.status_code = status_code


def add_global_exception_handler(app: FastAPI):
    @app.exception_handler(GlobalErrorException)
    async def global_error_exception_handler(request, exc: GlobalErrorException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "error_message": exc.error_message,
            },
        )
