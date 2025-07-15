from typing import List

from sqlmodel import Session, select

from modules.user.oauth_model import OAuth
from modules.user.user_model import User


class UserQuery:
    def __init__(self, session: Session):
        self.session = session

    def get_oauth_by_oauth_user_id(self, provider: str, oauth_user_id: str) -> OAuth | None:
        statement = select(OAuth).where(
            OAuth.oauth_provider == provider, OAuth.oauth_user_id == oauth_user_id
        )
        return self.session.exec(statement).first()

    def get_oauth_by_user_id(self, user_id: str) -> List[OAuth]:
        return self.session.exec(select(OAuth).where(OAuth.user_id == user_id)).all()

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.session.exec(select(User).where(User.user_id == user_id)).first()

    def get_user_by_email(self, email: str) -> User | None:
        return self.session.exec(select(User).where(User.email == email)).first()
