# SQLModel Model Design Patterns

## Table of Contents
1. Single Model vs. Multiple Model Pattern
2. Base Model Pattern
3. Table Models
4. API Models (Create, Public, Update)
5. Field Configuration
6. Type Hints and Validation

---

## 1. Single Model vs. Multiple Model Pattern

### Single Model (Simple Use Cases)

```python
from sqlmodel import Field, SQLModel
from typing import Optional

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None
```

**When to use**:
- Simple CRUD applications
- Internal tools
- Prototyping
- No sensitive fields to hide

**Limitations**:
- Exposes all fields in API responses
- Cannot enforce different validation rules for create vs. update
- Less flexible for evolving requirements

### Multiple Model Pattern (Industry Standard)

```python
from sqlmodel import Field, SQLModel
from typing import Optional

# 1. Base Model - Shared fields
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = Field(default=None, index=True)

# 2. Table Model - Database representation
class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# 3. Create Model - API input for creation
class HeroCreate(HeroBase):
    pass

# 4. Public Model - API output (safe for external use)
class HeroPublic(HeroBase):
    id: int

# 5. Update Model - API input for updates (all fields optional)
class HeroUpdate(SQLModel):
    name: Optional[str] = None
    secret_name: Optional[str] = None
    age: Optional[int] = None
```

**Benefits**:
- **Security**: `HeroPublic` doesn't expose internal/sensitive fields
- **Validation**: Different rules for create vs. update operations
- **Flexibility**: Easy to add computed fields to Public model
- **Type Safety**: Compiler catches misuse of models
- **Evolution**: Easy to modify without breaking API contracts

**When to use**:
- Production applications
- Public APIs
- Applications with sensitive data
- Systems requiring audit trails
- Complex validation requirements

---

## 2. Base Model Pattern

### Purpose

Base models contain **shared fields** that are common across multiple model variants.

### Basic Base Model

```python
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = Field(default=None, index=True)
```

**Key Points**:
- Does NOT have `table=True`
- Contains only business logic fields
- No `id` or database-specific fields
- Inherited by Table, Create, and Public models

### Advanced Base Model with Validation

```python
from pydantic import field_validator

class HeroBase(SQLModel):
    name: str = Field(index=True, min_length=1, max_length=100)
    secret_name: str = Field(min_length=1)
    age: Optional[int] = Field(default=None, ge=0, le=150)

    @field_validator('name')
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        if not v[0].isupper():
            raise ValueError('Name must start with capital letter')
        return v
```

### Multiple Base Models for Complex Hierarchies

```python
# Timestamp mixin
class TimestampBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Soft delete mixin
class SoftDeleteBase(SQLModel):
    deleted_at: Optional[datetime] = None
    is_deleted: bool = Field(default=False)

# Business logic base
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = None

# Combine all bases
class Hero(HeroBase, TimestampBase, SoftDeleteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
```

---

## 3. Table Models

### Basic Table Model

```python
class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
```

**Key characteristics**:
- Has `table=True` parameter
- Contains database-specific fields (`id`, foreign keys, timestamps)
- Inherits from Base model
- Becomes both Pydantic model AND SQLAlchemy table

### Table Model with Foreign Keys

```python
class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
```

### Table Model with Indexes and Constraints

```python
class Hero(HeroBase, table=True):
    __tablename__ = "heroes"  # Custom table name

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)  # Unique constraint
    email: str = Field(index=True, unique=True, sa_column_kwargs={"unique": True})
    age: Optional[int] = Field(default=None, index=True)

    class Config:
        # Additional SQLAlchemy configuration
        arbitrary_types_allowed = True
```

### Table Model with Computed Columns

```python
from sqlalchemy import Column, Integer, String, Computed

class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    # Computed column (database-level)
    full_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String, Computed("first_name || ' ' || last_name"))
    )
```

---

## 4. API Models (Create, Public, Update)

### Create Model

Used for **accepting data when creating new records**.

```python
class HeroCreate(HeroBase):
    pass  # Uses all fields from HeroBase
```

**With additional validation**:
```python
class HeroCreate(HeroBase):
    password: str = Field(min_length=8)  # Required for creation

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

**Excluding certain fields**:
```python
class HeroCreate(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = None
    # No team_id - will be set by application logic
```

### Public Model

Used for **API responses** - what users see.

```python
class HeroPublic(HeroBase):
    id: int  # Required in responses, not Optional
```

**With computed/additional fields**:
```python
from pydantic import computed_field

class HeroPublic(HeroBase):
    id: int
    created_at: datetime

    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.secret_name})"
```

**Excluding sensitive fields**:
```python
class UserBase(SQLModel):
    username: str
    email: str
    password_hash: str  # Sensitive!

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class UserPublic(SQLModel):
    id: int
    username: str
    email: str
    # password_hash excluded for security
```

### Update Model

Used for **partial updates** - all fields optional.

```python
class HeroUpdate(SQLModel):
    name: Optional[str] = None
    secret_name: Optional[str] = None
    age: Optional[int] = None
```

**Why all fields are optional**:
- Allows partial updates (PATCH semantics)
- Only provided fields are updated
- Unset fields remain unchanged in database

**With validation**:
```python
class HeroUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    secret_name: Optional[str] = Field(default=None, min_length=1)
    age: Optional[int] = Field(default=None, ge=0, le=150)
```

---

## 5. Field Configuration

### Primary Keys

```python
# Auto-incrementing integer (most common)
id: Optional[int] = Field(default=None, primary_key=True)

# UUID primary key
from uuid import UUID, uuid4
id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)

# String primary key
id: str = Field(primary_key=True)
```

### Indexes

```python
# Single field index
name: str = Field(index=True)

# Unique constraint
email: str = Field(index=True, unique=True)

# Composite index (using SQLAlchemy)
from sqlalchemy import Index

class Hero(SQLModel, table=True):
    __table_args__ = (
        Index('idx_name_age', 'name', 'age'),
    )
    name: str
    age: int
```

### Default Values

```python
from datetime import datetime

class Hero(SQLModel, table=True):
    # Static default
    is_active: bool = Field(default=True)

    # Dynamic default (function called at creation time)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Database-level default (using SQLAlchemy)
    from sqlalchemy import Column, DateTime, func
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now())
    )
```

### Nullable Fields

```python
# Nullable (allows NULL in database)
age: Optional[int] = None

# Not nullable (database constraint)
name: str  # No Optional, no default

# Nullable with default
description: Optional[str] = Field(default=None)
```

### Field Validation

```python
from pydantic import Field

class Hero(SQLModel):
    # String constraints
    name: str = Field(min_length=1, max_length=100)

    # Numeric constraints
    age: int = Field(ge=0, le=150)  # ge = greater than or equal

    # Regex pattern
    phone: str = Field(pattern=r'^\+?1?\d{9,15}$')

    # Multiple constraints
    email: str = Field(
        min_length=3,
        max_length=255,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
```

---

## 6. Type Hints and Validation

### Python 3.10+ Union Types

```python
# Modern syntax (Python 3.10+)
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    age: int | None = None
```

### Python 3.9+ with typing.Optional

```python
from typing import Optional

# Older syntax (Python 3.9)
class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    age: Optional[int] = None
```

### Complex Types

```python
from typing import List, Dict, Optional
from pydantic import Json

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # JSON field
    metadata: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))

    # List (stored as JSON)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
```

### Enums

```python
from enum import Enum

class HeroType(str, Enum):
    HERO = "hero"
    VILLAIN = "villain"
    ANTI_HERO = "anti_hero"

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    hero_type: HeroType = Field(default=HeroType.HERO)
```

---

## Complete Example: E-Commerce Product Models

```python
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal

class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

# Base model with shared fields
class ProductBase(SQLModel):
    name: str = Field(index=True, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(ge=0)
    sku: str = Field(unique=True, index=True, min_length=1, max_length=50)

# Table model
class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: ProductStatus = Field(default=ProductStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")

# Create model (for POST requests)
class ProductCreate(ProductBase):
    category_id: int  # Required when creating

# Public model (for GET responses)
class ProductPublic(ProductBase):
    id: int
    status: ProductStatus
    created_at: datetime
    updated_at: datetime

# Update model (for PATCH requests)
class ProductUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[Decimal] = Field(default=None, ge=0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    status: Optional[ProductStatus] = None
    category_id: Optional[int] = None
```

**Usage in FastAPI**:
```python
@app.post("/products/", response_model=ProductPublic)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@app.patch("/products/{product_id}", response_model=ProductPublic)
def update_product(
    product_id: int,
    product: ProductUpdate,
    session: Session = Depends(get_session)
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_data = product.model_dump(exclude_unset=True)
    db_product.sqlmodel_update(product_data)
    db_product.updated_at = datetime.utcnow()

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product
```
