from python.helpers.api import ApiHandler, Input, Output
from database import crud, schemas
from database.database import SessionLocal
from flask import Request, Response, json

class ApiRegister(ApiHandler):
    @classmethod
    def requires_auth(cls):
        return False

    async def process(self, input: Input, request: Request) -> Output:
        db = SessionLocal()
        try:
            user_schema = schemas.UserCreate(**input)

            db_user = crud.get_user_by_email(db, email=user_schema.email)
            if db_user:
                return Response(response=json.dumps({"message": "Email already registered"}), status=400, mimetype="application/json")

            new_user = crud.create_user(db=db, user_schema=input)
            return Response(response=json.dumps({"message": f"User {new_user.email} created successfully"}), status=201, mimetype="application/json")
        finally:
            db.close()