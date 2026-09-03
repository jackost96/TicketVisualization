from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))


class ProjectRole(Base):
    __tablename__ = "project_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ProjectRoleMember(Base):
    __tablename__ = "project_role_members"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("project_roles.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    role = relationship("ProjectRole")
    user = relationship("User")


class PermissionScheme(Base):
    __tablename__ = "permission_schemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    grants = relationship(
        "PermissionSchemeGrant", back_populates="permission_scheme", cascade="all, delete-orphan"
    )


class PermissionSchemeGrant(Base):
    __tablename__ = "permission_scheme_grants"

    id: Mapped[int] = mapped_column(primary_key=True)
    permission_scheme_id: Mapped[int] = mapped_column(
        ForeignKey("permission_schemes.id"), nullable=False
    )
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("project_roles.id"), nullable=False)

    permission_scheme = relationship("PermissionScheme", back_populates="grants")
    permission = relationship("Permission")
    role = relationship("ProjectRole")
