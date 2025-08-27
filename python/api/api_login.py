from python.helpers.api import ApiHandler
from database.database import get_db
from database import crud
from sqlalchemy.orm import Session
import jwt, datetime, os

class ApiLogin(ApiHandler):
    def requires_auth(self): return False
    def requires_csrf(self): return False
    async def handle_request(self, request):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        db: Session = next(get_db())
        user = crud.get_user_by_email(db, email=email)
        if not user or not crud.verify_password(password, user.hashed_password):
            return self.json_response({"message": "Invalid credentials"}, status_code=401)
        secret_key = os.environ.get('SECRET_KEY', 'a-very-secret-key-that-should-be-in-env')
        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, secret_key, algorithm="HS256")
        return self.json_response({"token": token})
