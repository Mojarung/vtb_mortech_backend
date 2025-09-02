# FastAPI Auth/User Example

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## User Model

Users now have comprehensive profiles with:
- **Required fields:** username, email, password
- **Optional fields:** about, phone, birth_date, skills, education
- **System fields:** id, is_active, created_at

## Endpoints

### Authentication
- **POST /auth/register** - Create new user
  ```json
  {
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "secret123",
    "about": "Software developer",
    "phone": "+1234567890",
    "birth_date": "1990-01-01",
    "skills": "Python, FastAPI, SQL",
    "education": "Computer Science Degree"
  }
  ```

- **POST /auth/login** - Login with username/email + password
  - Query params: `username` (can be username or email), `password`

### User Management
- **GET /users/me** - Get current user profile (Authorization: Bearer <token>)
- **PUT /auth/me** - Update current user profile (Authorization: Bearer <token>)
- **GET /users** - List all users (Authorization: Bearer <token>)
- **GET /users/{user_id}** - Get specific user (Authorization: Bearer <token>)

## Environment

- APP_DATABASE_URL: default sqlite+aiosqlite:///./app.db
- APP_SECRET_KEY: set a strong key
- APP_ACCESS_TOKEN_EXPIRE_MINUTES: default 1440

## Database

The app uses SQLite by default. If you need to recreate the database after schema changes:
```bash
rm -f app.db
uvicorn app.main:app --reload
```
