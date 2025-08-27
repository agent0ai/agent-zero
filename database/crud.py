from sqlalchemy.orm import Session
from . import database
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    return db.query(database.User).filter(database.User.email == email).first()

def create_user(db: Session, user_schema: dict):
    hashed_password = pwd_context.hash(user_schema['password'])
    db_user = database.User(email=user_schema['email'], hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user