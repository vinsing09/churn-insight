from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import Account
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_account(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Account:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        account_id: str | None = payload.get("sub")
        if account_id is None:
            raise exc
    except JWTError:
        raise exc

    account = db.get(Account, account_id)
    if account is None:
        raise exc
    return account
