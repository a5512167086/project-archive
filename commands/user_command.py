from sqlmodel import Session

from models.oauth_model import OAuth
from models.user_model import User
from schemas.user_schema import RegisterRequest


def create_oauth(session: Session, user_id: str, provider: str, oauth_user_id: str):
    new_oauth = OAuth(
        user_id=user_id,
        oauth_provider=provider,
        oauth_user_id=oauth_user_id,
    )
    session.add(new_oauth)
    session.flush()
    session.refresh(new_oauth)
    return new_oauth


def create_user(session: Session, user: RegisterRequest) -> User | None:
    new_user = User(username=user.username, email=user.email, password=user.password)
    session.add(new_user)
    session.flush()
    return new_user


def update_user_password(session: Session, update_user_id: str, new_password: str):
    user = session.get(User, update_user_id)
    user.password = new_password
    session.add(user)
