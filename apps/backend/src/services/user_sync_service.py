"""
User Synchronization Service

Handles syncing user data from Authentik JWT tokens to the FairMind database.
Creates/updates user records with roles and permissions from Authentik.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import uuid as uuid_module

from src.infrastructure.db.database.models import User
from config.database import db_manager

logger = logging.getLogger("fairmind.user_sync")


class UserSyncService:
    """Service to sync users from Authentik tokens to database."""

    # Map Authentik groups/roles to FairMind roles
    ROLE_MAPPING = {
        "authentik_default_user": "viewer",
        "authentik_admins": "admin",
        "fairmind_analysts": "analyst",
        "fairmind_admins": "admin",
        "fairmind_viewers": "viewer",
    }

    PERMISSION_MAPPING = {
        "admin": [
            "model:read",
            "model:write",
            "model:delete",
            "reports:create",
            "reports:read",
            "reports:delete",
            "compliance:manage",
            "users:manage",
            "roles:manage",
            "audit:view",
        ],
        "analyst": [
            "model:read",
            "model:write",
            "reports:create",
            "reports:read",
            "compliance:view",
        ],
        "viewer": [
            "model:read",
            "reports:read",
            "compliance:view",
        ],
    }

    async def sync_user_from_token(
        self, token_payload: Dict[str, Any], ip_address: Optional[str] = None
    ) -> Optional[User]:
        """
        Sync user from Authentik JWT token to database.

        Creates a new user if not found, updates existing user's roles/groups.

        Args:
            token_payload: Decoded JWT payload from Authentik
            ip_address: Client IP address for audit trail

        Returns:
            User object if sync successful, None if failed
        """
        try:
            # Extract essential claims from token
            authentik_id = token_payload.get("sub")  # User UUID from Authentik
            email = token_payload.get("email")
            username = token_payload.get("preferred_username") or token_payload.get("name")
            name = token_payload.get("name")

            if not authentik_id or not email:
                logger.error(
                    "Missing required claims in token: sub or email not found"
                )
                return None

            # Extract groups/roles from token
            groups = token_payload.get("groups", [])
            roles = self._extract_roles_from_groups(groups)
            permissions = self._compute_permissions(roles)

            # Get or create user in database
            session = db_manager.get_sync_session()
            try:
                # Try to find existing user by authentik_id
                user = session.query(User).filter(User.authentik_id == authentik_id).first()

                if not user:
                    # Create new user
                    user = User(
                        id=uuid_module.uuid4(),
                        authentik_id=authentik_id,
                        email=email,
                        username=username or email.split("@")[0],
                        name=name or username,
                        roles=roles,
                        groups=groups,
                        permissions=permissions,
                        is_active=True,
                        is_verified_email=token_payload.get("email_verified", False),
                        last_sync=datetime.utcnow(),
                        authentik_data=token_payload,
                        last_ip=ip_address,
                    )
                    logger.info(
                        f"Creating new user: {email} (authentik_id={authentik_id})"
                    )
                    session.add(user)
                else:
                    # Update existing user
                    user.email = email
                    user.name = name or user.name
                    user.roles = roles
                    user.groups = groups
                    user.permissions = permissions
                    user.last_sync = datetime.utcnow()
                    user.authentik_data = token_payload
                    user.is_verified_email = token_payload.get("email_verified", False)
                    user.last_ip = ip_address
                    logger.debug(f"Updating user: {email} (authentik_id={authentik_id})")

                # Update last login
                user.last_login = datetime.utcnow()

                session.commit()
                logger.info(f"User synced successfully: {email}")

                return user

            except Exception as e:
                session.rollback()
                logger.error(f"Error syncing user {email}: {e}")
                raise
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to sync user from token: {e}")
            return None

    async def get_or_create_user(
        self,
        authentik_id: str,
        email: str,
        username: str,
        name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[User]:
        """
        Get existing user or create new one.

        Args:
            authentik_id: Authentik user UUID
            email: User email
            username: User username
            name: User full name
            roles: List of role strings
            groups: List of group strings from Authentik
            ip_address: Client IP for audit trail

        Returns:
            User object if successful, None if failed
        """
        try:
            session = db_manager.get_sync_session()
            try:
                # Try to find existing user
                user = session.query(User).filter(User.authentik_id == authentik_id).first()

                if user:
                    # Update existing user
                    user.email = email
                    user.username = username
                    user.name = name or user.name
                    if roles:
                        user.roles = roles
                    if groups:
                        user.groups = groups
                    user.last_sync = datetime.utcnow()
                    user.last_ip = ip_address
                else:
                    # Create new user
                    computed_roles = roles or ["viewer"]
                    computed_perms = self._compute_permissions(computed_roles)

                    user = User(
                        id=uuid_module.uuid4(),
                        authentik_id=authentik_id,
                        email=email,
                        username=username,
                        name=name or username,
                        roles=computed_roles,
                        groups=groups or [],
                        permissions=computed_perms,
                        is_active=True,
                        last_sync=datetime.utcnow(),
                        last_ip=ip_address,
                    )
                    session.add(user)

                session.commit()
                return user

            except Exception as e:
                session.rollback()
                logger.error(f"Error managing user {email}: {e}")
                raise
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Failed to get or create user: {e}")
            return None

    def _extract_roles_from_groups(self, groups: List[str]) -> List[str]:
        """
        Extract FairMind roles from Authentik groups.

        Args:
            groups: List of Authentik group names

        Returns:
            List of FairMind roles
        """
        roles = []

        for group in groups:
            mapped_role = self.ROLE_MAPPING.get(group.lower())
            if mapped_role and mapped_role not in roles:
                roles.append(mapped_role)

        # Default to viewer if no recognized groups
        if not roles:
            roles = ["viewer"]

        return roles

    def _compute_permissions(self, roles: List[str]) -> List[str]:
        """
        Compute permissions based on roles.

        Args:
            roles: List of role strings

        Returns:
            List of permission strings
        """
        permissions = set()

        for role in roles:
            if role in self.PERMISSION_MAPPING:
                permissions.update(self.PERMISSION_MAPPING[role])

        return list(permissions)

    async def get_user_by_authentik_id(self, authentik_id: str) -> Optional[User]:
        """
        Get user by Authentik ID.

        Args:
            authentik_id: Authentik user UUID

        Returns:
            User object if found, None otherwise
        """
        try:
            session = db_manager.get_sync_session()
            try:
                user = session.query(User).filter(User.authentik_id == authentik_id).first()
                return user
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email address

        Returns:
            User object if found, None otherwise
        """
        try:
            session = db_manager.get_sync_session()
            try:
                user = session.query(User).filter(User.email == email).first()
                return user
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by FairMind user ID.

        Args:
            user_id: FairMind user UUID

        Returns:
            User object if found, None otherwise
        """
        try:
            session = db_manager.get_sync_session()
            try:
                user = session.query(User).filter(User.id == UUID(user_id)).first()
                return user
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None

    async def list_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User objects
        """
        try:
            session = db_manager.get_sync_session()
            try:
                users = (
                    session.query(User)
                    .order_by(User.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )
                return users
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []


# Global service instance
user_sync_service = UserSyncService()
