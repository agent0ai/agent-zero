from python.helpers.api import ApiHandler
from database.database import get_db
from database import crud, schemas
from sqlalchemy.orm import Session

class ApiRegister(ApiHandler):
    def requires_auth(self): return False
    def requires_csrf(self): return False
    async def handle_request(self, request):
        json_data = request.get_json()
        try:
            user_data = schemas.UserCreate(**json_data)
        except Exception:
            return self.json_response({"message": "Invalid data format"}, status_code=400)
        db: Session = next(get_db())
        if crud.get_user_by_email(db, email=user_data.email):
            return self.json_response({"message": "Email already registered"}, status_code=409)
        new_user = crud.create_user(db=db, user=user_data)
        return self.json_response({"message": "User registered successfully", "user_id": new_user.id}, status_code=201)