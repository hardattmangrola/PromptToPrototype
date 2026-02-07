"""
Role-based access control. Patients and Doctors; no medical data leakage between users.
"""
from enum import Enum
from typing import Callable, Set

from fastapi import Depends, status

from app.api.deps import get_current_user_payload
from app.core.exceptions import ForbiddenError


class Role(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"


def require_roles(*allowed_roles: Role) -> Callable:
    """Dependency that ensures the current user has one of the allowed roles."""

    allowed: Set[str] = {r.value for r in allowed_roles}

    async def _check(current: dict = Depends(get_current_user_payload)) -> dict:
        role = current.get("role")
        if role not in allowed:
            raise ForbiddenError(
                message="Insufficient permissions for this resource",
                details={"required_roles": list(allowed), "your_role": role},
            )
        return current

    return _check


def require_patient() -> Callable:
    """Dependency: only patients."""
    return require_roles(Role.PATIENT)


def require_doctor() -> Callable:
    """Dependency: only doctors."""
    return require_roles(Role.DOCTOR)


def require_any_authenticated() -> Callable:
    """Dependency: any authenticated user (patient or doctor)."""
    return require_roles(Role.PATIENT, Role.DOCTOR)
