from sqlmodel import Field, SQLModel, UniqueConstraint


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("class_id", "role_type", "role_id", name="uq_permissions"),
    )

    class_id: int = Field(
        foreign_key="classes.class_id", nullable=False, primary_key=True
    )
    role_type: bool = Field(nullable=False, description="0表示是群組，1表示是使用者")
    role_id: int = Field(
        nullable=False, description="由RoleType決定值為Groups.GID或Member.MID"
    )
    permission_bits: int = Field(default=1, nullable=False)
