from fastapi import Header, HTTPException


async def get_auth_response_headers(
    x_user_id: str = Header(description="The user ID", alias="X-User-ID"),
    x_user_email: str = Header(description="The user email", alias="X-User-Email"),
):
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header is missing")

    if not x_user_email:
        raise HTTPException(status_code=400, detail="X-User-Email header is missing")

    return {"X-User-ID": x_user_id, "X-User-Email": x_user_email}
