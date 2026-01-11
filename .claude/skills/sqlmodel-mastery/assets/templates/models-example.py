"""
Comprehensive SQLModel Models Example

This file demonstrates best practices for SQLModel model design including:
- Multiple model pattern (Base, Table, Create, Public, Update)
- Relationships (one-to-many, many-to-many)
- Field validation and constraints
- Timestamps and soft deletes
- Enums and complex types
"""

from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import field_validator, EmailStr


# ===== ENUMS =====

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class ProductStatus(str, Enum):
    """Product status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# ===== MIXINS (Reusable Base Classes) =====

class TimestampMixin(SQLModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SoftDeleteMixin(SQLModel):
    """Mixin for soft delete functionality."""
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None


# ===== USER MODELS =====

class UserBase(SQLModel):
    """Base user model with shared fields."""
    username: str = Field(
        index=True,
        unique=True,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$"
    )
    email: EmailStr = Field(index=True, unique=True)
    full_name: str = Field(min_length=1, max_length=100)
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Ensure username is alphanumeric."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        return v.lower()


class User(UserBase, TimestampMixin, SoftDeleteMixin, table=True):
    """User table model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str  # Never expose in Public models!

    # Relationships
    products: List["Product"] = Relationship(back_populates="owner")
    orders: List["Order"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    """Model for user registration."""
    password: str = Field(min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Validate password complexity."""
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserPublic(UserBase):
    """Model for API responses (excludes password_hash)."""
    id: int
    created_at: datetime


class UserPublicWithProducts(UserPublic):
    """User model with related products."""
    products: List["ProductPublic"] = []


class UserUpdate(SQLModel):
    """Model for updating users."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ===== CATEGORY MODELS =====

class CategoryBase(SQLModel):
    """Base category model."""
    name: str = Field(index=True, unique=True, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class Category(CategoryBase, table=True):
    """Category table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    products: List["Product"] = Relationship(back_populates="category")


class CategoryCreate(CategoryBase):
    """Model for creating categories."""
    pass


class CategoryPublic(CategoryBase):
    """Model for API responses."""
    id: int


class CategoryUpdate(SQLModel):
    """Model for updating categories."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None


# ===== PRODUCT MODELS =====

class ProductBase(SQLModel):
    """Base product model."""
    name: str = Field(index=True, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(ge=0)
    sku: str = Field(unique=True, index=True, min_length=1, max_length=50)
    status: ProductStatus = Field(default=ProductStatus.DRAFT)


class Product(ProductBase, TimestampMixin, table=True):
    """Product table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    category_id: int = Field(foreign_key="category.id")
    owner_id: int = Field(foreign_key="user.id")

    # Relationships
    category: Category = Relationship(back_populates="products")
    owner: User = Relationship(back_populates="products")
    order_items: List["OrderItem"] = Relationship(back_populates="product")


class ProductCreate(ProductBase):
    """Model for creating products."""
    category_id: int
    # owner_id set from authenticated user, not from request


class ProductPublic(ProductBase):
    """Model for API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    category: CategoryPublic


class ProductUpdate(SQLModel):
    """Model for updating products."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    status: Optional[ProductStatus] = None
    category_id: Optional[int] = None


# ===== ORDER MODELS (Many-to-Many with Link Table) =====

class OrderItemBase(SQLModel):
    """Base order item model (link table with extra fields)."""
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class OrderItem(OrderItemBase, table=True):
    """Order item link table."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys (many-to-many)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")

    # Relationships
    order: "Order" = Relationship(back_populates="order_items")
    product: Product = Relationship(back_populates="order_items")


class OrderItemPublic(OrderItemBase):
    """Public order item model."""
    id: int
    product: ProductPublic


class OrderBase(SQLModel):
    """Base order model."""
    status: str = Field(default="pending")
    notes: Optional[str] = Field(default=None, max_length=1000)


class Order(OrderBase, TimestampMixin, table=True):
    """Order table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    user_id: int = Field(foreign_key="user.id")

    # Relationships
    user: User = Relationship(back_populates="orders")
    order_items: List[OrderItem] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class OrderCreate(OrderBase):
    """Model for creating orders."""
    items: List[dict]  # [{"product_id": 1, "quantity": 2}, ...]


class OrderPublic(OrderBase):
    """Model for API responses."""
    id: int
    created_at: datetime
    user_id: int
    order_items: List[OrderItemPublic]


# ===== EXAMPLE: Advanced Patterns =====

class AuditLog(TimestampMixin, table=True):
    """Audit log for tracking changes."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    action: str = Field(index=True)  # "create", "update", "delete"
    entity_type: str  # "product", "order", etc.
    entity_id: int
    changes: Optional[str] = None  # JSON string of changes


class Setting(SQLModel, table=True):
    """Key-value settings table."""
    key: str = Field(primary_key=True, max_length=100)
    value: str
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ===== UTILITY FUNCTIONS =====

def create_all_tables(engine):
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all database tables (use with caution!)."""
    SQLModel.metadata.drop_all(engine)


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    from sqlmodel import create_engine, Session

    # Create in-memory database for demonstration
    engine = create_engine("sqlite:///:memory:", echo=True)
    create_all_tables(engine)

    with Session(engine) as session:
        # Create user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            username="johndoe",
            email="john@example.com",
            full_name="John Doe",
            password_hash=pwd_context.hash("SecurePass123"),
            role=UserRole.USER
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create category
        category = Category(
            name="Electronics",
            description="Electronic products"
        )
        session.add(category)
        session.commit()
        session.refresh(category)

        # Create product
        product = Product(
            name="Laptop",
            description="High-performance laptop",
            price=Decimal("999.99"),
            stock_quantity=10,
            sku="LAPTOP-001",
            status=ProductStatus.ACTIVE,
            category_id=category.id,
            owner_id=user.id
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        # Create order with items
        order = Order(user_id=user.id, status="pending")
        session.add(order)
        session.commit()
        session.refresh(order)

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=2,
            unit_price=product.price
        )
        session.add(order_item)
        session.commit()

        print(f"Created order {order.id} for user {user.username}")
        print(f"Order contains {len(order.order_items)} items")
