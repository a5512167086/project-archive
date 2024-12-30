from utils import create_jwt_token
from datetime import timedelta


def generate_access_token(user_id: str, email: str, is_remeber: bool):
    data = {"sub": user_id, "email": email}
    if is_remeber:
        access_token = create_jwt_token(data=data, expires_delta=timedelta(days=7))
    else:
        access_token = create_jwt_token(data=data)
    return {"token": access_token, "token_type": "bearer"}
