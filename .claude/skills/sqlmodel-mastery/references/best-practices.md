# SQLModel Best Practices and Common Patterns

## Table of Contents
1. Model Design Best Practices
2. Session Management
3. Performance Optimization
4. Security Considerations
5. Database Migrations
6. Testing Strategies
7. Common Pitfalls and Solutions

---

## 1. Model Design Best Practices

### ✅ DO: Use Multiple Model Pattern

```python
# GOOD: Separate models for different purposes
class HeroBase(SQLModel):
    name: str
    secret_name: str

class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class HeroCreate(HeroBase):
    pass

class HeroPublic(HeroBase):
    id: int

class HeroUpdate(SQLModel):
    name: Optional[str] = None
    secret_name: Optional[str] = None
```

### ❌ DON'T: Expose Table Models in API

```python
# BAD: Exposes internal fields, no security
@app.get("/heroes/", response_model=List[Hero])  # ❌ Using table model
def read_heroes(session: Session = Depends(get_session)):
    return session.exec(select(Hero)).all()

# GOOD: Use Public model
@app.get("/heroes/", response_model=List[HeroPublic])  # ✅ Using public model
def read_heroes(session: Session = Depends(get_session)):
    return session.exec(select(Hero)).all()
```

### ✅ DO: Add Indexes to Frequently Queried Fields

```python
class Hero(SQLModel, table=True):
    name: str = Field(index=True)  # Frequently searched
    email: str = Field(index=True, unique=True)  # Unique lookup
    age: Optional[int] = Field(default=None, index=True)  # Filtered often
```

### ✅ DO: Use Appropriate Field Types

```python
from decimal import Decimal
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Product(SQLModel, table=True):
    # Use Decimal for money
    price: Decimal = Field(max_digits=10, decimal_places=2)

    # Use datetime for timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Use Enum for status fields
    status: ProductStatus = Field(default=ProductStatus.ACTIVE)

    # Use bool for flags
    is_featured: bool = Field(default=False)
```

---

## 2. Session Management

### ✅ DO: Use Context Managers

```python
# GOOD: Automatic cleanup
with Session(engine) as session:
    hero = Hero(name="Spider-Boy")
    session.add(hero)
    session.commit()
# Session automatically closed
```

### ❌ DON'T: Forget to Commit or Refresh

```python
# BAD: Changes not persisted
session.add(hero)
# Missing session.commit()

# BAD: ID not available
hero = Hero(name="Spider-Boy")
session.add(hero)
session.commit()
print(hero.id)  # May be None without refresh()

# GOOD: Commit and refresh
session.add(hero)
session.commit()
session.refresh(hero)
print(hero.id)  # Now available
```

### ✅ DO: Handle Transactions Properly

```python
try:
    with Session(engine) as session:
        hero = Hero(name="Iron Man")
        session.add(hero)

        team = Team(name="Avengers")
        session.add(team)

        session.commit()  # Both or neither
except Exception as e:
    session.rollback()  # Rollback on error
    raise
```

### ✅ DO: Use FastAPI Dependency Injection

```python
# GOOD: Automatic session management
def get_session():
    with Session(engine) as session:
        yield session

@app.get("/heroes/")
def read_heroes(session: Session = Depends(get_session)):
    # Session automatically cleaned up
    return session.exec(select(Hero)).all()
```

---

## 3. Performance Optimization

### ✅ DO: Use Pagination

```python
# GOOD: Limit results
@app.get("/heroes/")
def read_heroes(
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    statement = select(Hero).offset(offset).limit(limit)
    return session.exec(statement).all()
```

### ✅ DO: Use Eager Loading to Avoid N+1 Queries

```python
from sqlalchemy.orm import selectinload

# BAD: N+1 queries
heroes = session.exec(select(Hero)).all()
for hero in heroes:
    print(hero.team.name)  # Separate query for each hero!

# GOOD: Single query with join
statement = select(Hero).options(selectinload(Hero.team))
heroes = session.exec(statement).all()
for hero in heroes:
    print(hero.team.name)  # No additional queries
```

### ✅ DO: Select Only Needed Columns

```python
# If you only need specific fields
statement = select(Hero.id, Hero.name)
results = session.exec(statement).all()
```

### ✅ DO: Use Indexes on Foreign Keys

```python
class Hero(SQLModel, table=True):
    # Index on foreign key for join performance
    team_id: Optional[int] = Field(
        default=None,
        foreign_key="team.id",
        index=True  # Improves join performance
    )
```

### ✅ DO: Use Connection Pooling

```python
# GOOD: Configure connection pool
engine = create_engine(
    database_url,
    pool_size=5,  # Min connections
    max_overflow=10,  # Additional connections when needed
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

---

## 4. Security Considerations

### ✅ DO: Hide Sensitive Fields

```python
class UserBase(SQLModel):
    username: str
    email: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str  # Never expose this!

class UserPublic(UserBase):
    id: int
    # password_hash intentionally excluded
```

### ✅ DO: Hash Passwords

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(UserBase):
    password: str  # Plain text from user

@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=pwd_context.hash(user.password)  # Hash before storing
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

### ✅ DO: Validate and Sanitize Input

```python
class HeroCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)

    @field_validator('name')
    @classmethod
    def name_alphanumeric(cls, v: str) -> str:
        if not v.replace(' ', '').isalnum():
            raise ValueError('Name must be alphanumeric')
        return v
```

### ❌ DON'T: Use String Concatenation for Queries

```python
# BAD: SQL injection vulnerability
name = request.query_params.get("name")
query = f"SELECT * FROM hero WHERE name = '{name}'"  # ❌ DANGEROUS

# GOOD: Use parameterized queries (SQLModel/SQLAlchemy handles this)
statement = select(Hero).where(Hero.name == name)  # ✅ Safe
```

---

## 5. Database Migrations

### ✅ DO: Use Alembic for Migrations

SQLModel doesn't have built-in migrations. Use Alembic:

```bash
# Install Alembic
pip install alembic

# Initialize
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Add hero table"

# Apply migration
alembic upgrade head
```

**Configure Alembic with SQLModel**:

```python
# alembic/env.py
from sqlmodel import SQLModel
from your_app.models import Hero, Team  # Import all models

target_metadata = SQLModel.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

### ✅ DO: Version Control Database Schema

- Commit migration files to version control
- Never manually edit database in production
- Test migrations on staging first

---

## 6. Testing Strategies

### ✅ DO: Use In-Memory SQLite for Tests

```python
import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",  # In-memory
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
```

### ✅ DO: Override Dependencies in Tests

```python
from fastapi.testclient import TestClient

def get_test_session():
    # Test database session
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = get_test_session

client = TestClient(app)

def test_create_hero():
    response = client.post(
        "/heroes/",
        json={"name": "Test Hero", "secret_name": "Tester"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Hero"
```

---

## 7. Common Pitfalls and Solutions

### ❌ Pitfall: DetachedInstanceError

```python
# BAD: Accessing relationship outside session
with Session(engine) as session:
    hero = session.get(Hero, 1)

print(hero.team.name)  # ❌ Error: instance is not bound to a Session

# SOLUTION 1: Access within session
with Session(engine) as session:
    hero = session.get(Hero, 1)
    team_name = hero.team.name  # ✅ OK

# SOLUTION 2: Eager load
with Session(engine) as session:
    statement = select(Hero).options(selectinload(Hero.team))
    hero = session.exec(statement).first()

print(hero.team.name)  # ✅ OK, data already loaded
```

### ❌ Pitfall: Forgetting `exclude_unset` in Updates

```python
# BAD: Overwrites with None
hero_update = HeroUpdate(name="New Name")  # age is None
hero_data = hero_update.model_dump()  # {"name": "New Name", "age": None}
db_hero.sqlmodel_update(hero_data)  # ❌ Sets age to None!

# GOOD: Only update provided fields
hero_data = hero_update.model_dump(exclude_unset=True)  # {"name": "New Name"}
db_hero.sqlmodel_update(hero_data)  # ✅ Only updates name
```

### ❌ Pitfall: Not Handling Unique Constraints

```python
# BAD: No error handling
session.add(user)
session.commit()  # ❌ May fail if username exists

# GOOD: Handle IntegrityError
from sqlalchemy.exc import IntegrityError

try:
    session.add(user)
    session.commit()
except IntegrityError:
    session.rollback()
    raise HTTPException(status_code=400, detail="Username already exists")
```

### ❌ Pitfall: Circular Imports

```python
# BAD: models.py and api.py import each other
# models.py
from api import some_function  # ❌

# SOLUTION: Use string references for relationships
class Hero(SQLModel, table=True):
    team: Optional["Team"] = Relationship(back_populates="heroes")  # ✅ String reference
```

### ❌ Pitfall: Not Using Type Hints

```python
# BAD: No type hints
def get_hero(id):
    return session.get(Hero, id)

# GOOD: Type hints enable IDE support and validation
def get_hero(hero_id: int) -> Optional[Hero]:
    return session.get(Hero, hero_id)
```

---

## Checklist: Production-Ready SQLModel Application

- [ ] Use multiple model pattern (Base, Table, Create, Public, Update)
- [ ] Configure database connection pooling
- [ ] Add indexes to frequently queried fields
- [ ] Implement pagination on list endpoints
- [ ] Use eager loading to prevent N+1 queries
- [ ] Handle database errors (IntegrityError, etc.)
- [ ] Never expose sensitive fields in API responses
- [ ] Use Alembic for database migrations
- [ ] Write tests with in-memory SQLite
- [ ] Configure proper logging (disable echo in production)
- [ ] Use environment variables for database URL
- [ ] Implement proper transaction management
- [ ] Add input validation on all models
- [ ] Use proper HTTP status codes (201, 404, etc.)
- [ ] Document API with OpenAPI/Swagger (automatic with FastAPI)
