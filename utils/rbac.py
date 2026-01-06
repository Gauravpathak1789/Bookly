"""
Role-Based Access Control (RBAC) utilities
Provides decorators and functions to check user permissions
"""
from fastapi import HTTPException, status, Depends
from models import User, UserRole
from typing import List, Callable
from functools import wraps


class PermissionDenied(HTTPException):
    """Custom exception for permission denied errors"""
    def __init__(self, detail: str = "You don't have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def require_role(*allowed_roles: UserRole):
    """
    Dependency to require specific roles for an endpoint
    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def get_all_users():
            ...
    """
    def role_checker(current_user: User):
        if current_user.role not in allowed_roles:
            raise PermissionDenied(
                detail=f"This action requires one of these roles: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    
    return role_checker


def require_admin(current_user: User):
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise PermissionDenied("Admin access required")
    return current_user


def require_moderator_or_admin(current_user: User):
    """Require moderator or admin role"""
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise PermissionDenied("Moderator or Admin access required")
    return current_user


def require_verified_email(current_user: User):
    """Require verified email"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address."
        )
    return current_user


def is_admin(user: User) -> bool:
    """Check if user is admin"""
    return user.role == UserRole.ADMIN


def is_moderator(user: User) -> bool:
    """Check if user is moderator"""
    return user.role == UserRole.MODERATOR


def is_moderator_or_admin(user: User) -> bool:
    """Check if user is moderator or admin"""
    return user.role in [UserRole.MODERATOR, UserRole.ADMIN]


def can_modify_resource(current_user: User, resource_owner_id) -> bool:
    """
    Check if user can modify a resource
    Users can modify their own resources, admins can modify any
    """
    if current_user.role == UserRole.ADMIN:
        return True
    return str(current_user.uid) == str(resource_owner_id)


def check_permission(user: User, required_role: UserRole) -> bool:
    """Check if user has required role or higher"""
    role_hierarchy = {
        UserRole.USER: 0,
        UserRole.MODERATOR: 1,
        UserRole.ADMIN: 2
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level


# Example permission decorators for route handlers
class RBACDecorator:
    """Decorator class for role-based access control"""
    
    @staticmethod
    def admin_only(func: Callable):
        """Decorator to restrict endpoint to admins only"""
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if not current_user or current_user.role != UserRole.ADMIN:
                raise PermissionDenied("Admin access required")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    
    @staticmethod
    def moderator_or_admin(func: Callable):
        """Decorator to restrict endpoint to moderators and admins"""
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if not current_user or current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
                raise PermissionDenied("Moderator or Admin access required")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    
    @staticmethod
    def verified_email_required(func: Callable):
        """Decorator to require verified email"""
        @wraps(func)
        async def wrapper(*args, current_user: User = None, **kwargs):
            if not current_user or not current_user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email verification required"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
