# SQLModel with FastAPI Integration

## Table of Contents
1. Database Setup and Configuration
2. Dependency Injection Pattern
3. CRUD Endpoints
4. Error Handling
5. Request Validation
6. Response Models
7. Advanced Patterns

---

## 1. Database Setup and Configuration

### Basic Setup

```python
from sqlmodel import SQLModel, create_engine, Session
from fastapi import FastAPI

# Database configuration
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}  # SQLite specific
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

### PostgreSQL Configuration

```python
# PostgreSQL connection
DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Disable in production
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10
)
```

### Environment-Based Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./database.db"
    echo_sql: bool = False

    class Config:
        env_file = ".env"

settings = Settings()

engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
```

---

## 2. Dependency Injection Pattern

### Session Dependency (Standard Pattern)

```python
from typing import Annotated
from fastapi import Depends

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

**Usage in endpoints**:
```python
@app.get("/heroes/", response_model=List[HeroPublic])
def read_heroes(session: SessionDep):
    heroes = session.exec(select(Hero)).all()
    return heroes
```

### Alternative Explicit Dependency

```python
@app.get("/heroes/", response_model=List[HeroPublic])
def read_heroes(*, session: Session = Depends(get_session)):
    heroes = session.exec(select(Hero)).all()
    return heroes
```

### Why Dependency Injection?

- ✅ **Automatic session cleanup**: Context manager ensures session closure
- ✅ **Error handling**: Automatic rollback on exceptions
- ✅ **Testability**: Easy to override with test database
- ✅ **Separation of concerns**: Database logic separate from routing

---

## 3. CRUD Endpoints

### CREATE (POST)

```python
@app.post("/heroes/", response_model=HeroPublic, status_code=201)
def create_hero(*, session: SessionDep, hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

**Key points**:
- `model_validate()`: Converts Create model to Table model
- `session.add()`: Adds to session
- `session.commit()`: Persists to database
- `session.refresh()`: Loads auto-generated fields (id, timestamps)
- `status_code=201`: Correct HTTP status for resource creation

### READ Single (GET)

```python
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(*, session: SessionDep, hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

### READ List (GET)

```python
from fastapi import Query

@app.get("/heroes/", response_model=List[HeroPublic])
def read_heroes(
    *,
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes
```

### UPDATE (PATCH)

```python
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(
    *,
    session: SessionDep,
    hero_id: int,
    hero: HeroUpdate
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # Only update provided fields
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)

    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

**Key points**:
- `model_dump(exclude_unset=True)`: Only fields user provided
- `sqlmodel_update()`: Updates model attributes
- Allows partial updates (PATCH semantics)

### DELETE

```python
@app.delete("/heroes/{hero_id}")
def delete_hero(*, session: SessionDep, hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    session.delete(hero)
    session.commit()
    return {"ok": True}
```

---

## 4. Error Handling

### Not Found Errors

```python
from fastapi import HTTPException

def get_hero_or_404(session: Session, hero_id: int) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(
            status_code=404,
            detail=f"Hero with id {hero_id} not found"
        )
    return hero

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(*, session: SessionDep, hero_id: int):
    hero = get_hero_or_404(session, hero_id)
    return hero
```

### Unique Constraint Violations

```python
from sqlalchemy.exc import IntegrityError

@app.post("/users/", response_model=UserPublic)
def create_user(*, session: SessionDep, user: UserCreate):
    db_user = User.model_validate(user)
    session.add(db_user)

    try:
        session.commit()
        session.refresh(db_user)
        return db_user
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )
```

### Global Exception Handler

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Database constraint violation"}
    )
```

---

## 5. Request Validation

### Path Parameters

```python
from pydantic import Field as PydanticField

@app.get("/heroes/{hero_id}")
def read_hero(
    *,
    session: SessionDep,
    hero_id: int = Path(gt=0, description="The ID of the hero")
):
    # hero_id validated to be > 0
    hero = get_hero_or_404(session, hero_id)
    return hero
```

### Query Parameters

```python
@app.get("/heroes/")
def search_heroes(
    *,
    session: SessionDep,
    name: Optional[str] = Query(None, min_length=1, max_length=100),
    min_age: Optional[int] = Query(None, ge=0),
    max_age: Optional[int] = Query(None, le=150)
):
    statement = select(Hero)

    if name:
        statement = statement.where(Hero.name.ilike(f"%{name}%"))
    if min_age is not None:
        statement = statement.where(Hero.age >= min_age)
    if max_age is not None:
        statement = statement.where(Hero.age <= max_age)

    heroes = session.exec(statement).all()
    return heroes
```

### Request Body Validation

```python
# Automatic validation from SQLModel
class HeroCreate(HeroBase):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)

@app.post("/heroes/")
def create_hero(*, session: SessionDep, hero: HeroCreate):
    # Pydantic validates hero automatically
    # Raises 422 if validation fails
    ...
```

---

## 6. Response Models

### Basic Response Model

```python
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(*, session: SessionDep, hero_id: int):
    hero = get_hero_or_404(session, hero_id)
    return hero  # Automatically serialized to HeroPublic
```

### List Response

```python
@app.get("/heroes/", response_model=List[HeroPublic])
def read_heroes(*, session: SessionDep):
    heroes = session.exec(select(Hero)).all()
    return heroes
```

### Paginated Response

```python
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: List[HeroPublic]
    total: int
    page: int
    page_size: int
    pages: int

@app.get("/heroes/", response_model=PaginatedResponse)
def read_heroes(
    *,
    session: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    # Count total
    count_statement = select(func.count(Hero.id))
    total = session.exec(count_statement).one()

    # Get page
    statement = (
        select(Hero)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    heroes = session.exec(statement).all()

    return {
        "items": heroes,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }
```

### Nested Relationships

```python
# Model with nested relationship
class HeroPublicWithTeam(HeroPublic):
    team: Optional[TeamPublic] = None

@app.get("/heroes/{hero_id}", response_model=HeroPublicWithTeam)
def read_hero_with_team(*, session: SessionDep, hero_id: int):
    hero = get_hero_or_404(session, hero_id)
    return hero  # SQLModel automatically includes team
```

---

## 7. Advanced Patterns

### Filtering with Query Models

```python
class HeroFilter(BaseModel):
    name: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    team_id: Optional[int] = None

@app.get("/heroes/search", response_model=List[HeroPublic])
def search_heroes(
    *,
    session: SessionDep,
    filters: HeroFilter = Depends()
):
    statement = select(Hero)

    if filters.name:
        statement = statement.where(Hero.name.ilike(f"%{filters.name}%"))
    if filters.min_age is not None:
        statement = statement.where(Hero.age >= filters.min_age)
    if filters.max_age is not None:
        statement = statement.where(Hero.age <= filters.max_age)
    if filters.team_id is not None:
        statement = statement.where(Hero.team_id == filters.team_id)

    heroes = session.exec(statement).all()
    return heroes
```

### Bulk Operations

```python
@app.post("/heroes/bulk", response_model=List[HeroPublic])
def create_heroes_bulk(*, session: SessionDep, heroes: List[HeroCreate]):
    db_heroes = [Hero.model_validate(hero) for hero in heroes]
    session.add_all(db_heroes)
    session.commit()

    for db_hero in db_heroes:
        session.refresh(db_hero)

    return db_heroes
```

### Transactions

```python
from sqlmodel import Session

@app.post("/transfer")
def transfer_hero(
    *,
    session: SessionDep,
    hero_id: int,
    new_team_id: int
):
    try:
        hero = get_hero_or_404(session, hero_id)
        team = session.get(Team, new_team_id)

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Update in transaction
        hero.team_id = new_team_id
        session.add(hero)
        session.commit()

        return {"message": f"{hero.name} transferred to {team.name}"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_notification(hero_name: str):
    # Send email, webhook, etc.
    print(f"Notification: {hero_name} was created")

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(
    *,
    session: SessionDep,
    hero: HeroCreate,
    background_tasks: BackgroundTasks
):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)

    background_tasks.add_task(send_notification, db_hero.name)

    return db_hero
```

### Middleware for Session Management

```python
from starlette.middleware.base import BaseHTTPMiddleware

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        with Session(engine) as session:
            request.state.db = session
            response = await call_next(request)
        return response

app.add_middleware(DBSessionMiddleware)

# Use in endpoints
from starlette.requests import Request

@app.get("/heroes/")
def read_heroes(request: Request):
    session = request.state.db
    heroes = session.exec(select(Hero)).all()
    return heroes
```
