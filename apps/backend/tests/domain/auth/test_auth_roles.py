import pytest
from unittest.mock import MagicMock, patch
from domain.auth.services.auth_service import AuthService

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session

@pytest.fixture
def auth_service(mock_db_session):
    service = AuthService()
    # Mock db_manager
    with patch('domain.auth.services.auth_service.db_manager.get_session') as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = mock_db_session
        yield service

@pytest.mark.asyncio
async def test_register_user_default_role(auth_service, mock_db_session):
    # Setup
    email = "test@example.com"
    password = "password"
    
    # Mock no existing user
    mock_db_session.execute.return_value.fetchone.return_value = None
    
    # Execute
    user = await auth_service.register_user(email, password)
    
    # Verify
    assert user.role == "user"
    # Verify INSERT args
    insert_call = mock_db_session.execute.call_args_list[1] # 0 is SELECT, 1 is INSERT
    assert insert_call[0][1]["role"] == "user"

@pytest.mark.asyncio
async def test_register_user_admin_role(auth_service, mock_db_session):
    # Setup
    email = "admin@example.com"
    password = "password"
    role = "admin"
    
    # Mock no existing user
    mock_db_session.execute.return_value.fetchone.return_value = None
    
    # Execute
    user = await auth_service.register_user(email, password, role=role)
    
    # Verify
    assert user.role == "admin"
    # Verify INSERT args
    insert_call = mock_db_session.execute.call_args_list[1]
    assert insert_call[0][1]["role"] == "admin"

@pytest.mark.asyncio
async def test_register_user_invalid_role(auth_service, mock_db_session):
    # Setup
    email = "hacker@example.com"
    password = "password"
    role = "superuser" # Invalid
    
    # Execute & Verify
    with pytest.raises(ValueError) as excinfo:
        await auth_service.register_user(email, password, role=role)
    
    assert "Invalid role" in str(excinfo.value)
