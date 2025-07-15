from sqlmodel import Session

from modules.user.oauth_model import OAuth
from modules.user.user_model import User


class UserCommand:
    def __init__(self, session: Session):
        self.session = session

    def create_oauth(self, user_id: str, provider: str, oauth_user_id: str):
        new_oauth = OAuth(
            user_id=user_id,
            oauth_provider=provider,
            oauth_user_id=oauth_user_id,
        )
        self.session.add(new_oauth)
        self.session.flush()
        self.session.refresh(new_oauth)
        return new_oauth

    def create_user(self, username: str, email: str, password: str) -> User | None:
        new_user = User(username=username, email=email, password=password)
        self.session.add(new_user)
        self.session.flush()
        return new_user

    def update_user_password(self, update_user_id: str, new_password: str):
        user = self.session.get(User, update_user_id)
        user.password = new_password
        self.session.add(user)
