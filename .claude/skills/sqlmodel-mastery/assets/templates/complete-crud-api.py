"""
Complete SQLModel + FastAPI CRUD API Template

This template provides a production-ready implementation of:
- Database setup and configuration
- Multiple model pattern (Base, Table, Create, Public, Update)
- CRUD endpoints with proper error handling
- Pagination and filtering
- Dependency injection for session management
- Input validation

Usage:
1. Customize the models to match your domain
2. Update database URL in settings
3. Run: uvicorn main:app --reload
"""

from typing import Annotated, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select
from pydantic import field_validator

# ===== DATABASE CONFIGURATION =====

DATABASE_URL = "sqlite:///./database.db"

connect_args = {"check_same_thread": False}  # SQLite only
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for database sessions."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# ===== MODELS: Team =====

class TeamBase(SQLModel):
    """Base model with shared Team fields."""
    name: str = Field(index=True, min_length=1, max_length=100)
    headquarters: str = Field(max_length=200)


class Team(TeamBase, table=True):
    """Team table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    heroes: List["Hero"] = Relationship(back_populates="team")


class TeamCreate(TeamBase):
    """Model for creating teams."""
    pass


class TeamPublic(TeamBase):
    """Model for API responses."""
    id: int


class TeamPublicWithHeroes(TeamPublic):
    """Team model including related heroes."""
    heroes: List["HeroPublic"] = []


class TeamUpdate(SQLModel):
    """Model for updating teams (all fields optional)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    headquarters: Optional[str] = Field(default=None, max_length=200)


# ===== MODELS: Hero =====

class HeroBase(SQLModel):
    """Base model with shared Hero fields."""
    name: str = Field(index=True, min_length=1, max_length=100)
    secret_name: str = Field(min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, ge=0, le=150, index=True)

    @field_validator('name')
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        """Validate that name starts with a capital letter."""
        if not v[0].isupper():
            raise ValueError('Name must start with a capital letter')
        return v


class Hero(HeroBase, table=True):
    """Hero table model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # Relationships
    team: Optional[Team] = Relationship(back_populates="heroes")


class HeroCreate(HeroBase):
    """Model for creating heroes."""
    team_id: Optional[int] = None


class HeroPublic(HeroBase):
    """Model for API responses."""
    id: int


class HeroPublicWithTeam(HeroPublic):
    """Hero model including related team."""
    team: Optional[TeamPublic] = None


class HeroUpdate(SQLModel):
    """Model for updating heroes (all fields optional)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    secret_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    team_id: Optional[int] = None


# ===== FASTAPI APP =====

app = FastAPI(
    title="SQLModel CRUD API",
    description="Complete CRUD API with SQLModel and FastAPI",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    """Initialize database on application startup."""
    create_db_and_tables()


# ===== HERO ENDPOINTS =====

@app.post("/heroes/", response_model=HeroPublic, status_code=201, tags=["heroes"])
def create_hero(*, session: SessionDep, hero: HeroCreate):
    """Create a new hero."""
    # Validate team exists if provided
    if hero.team_id:
        team = session.get(Team, hero.team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.get("/heroes/", response_model=List[HeroPublic], tags=["heroes"])
def read_heroes(
    *,
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    name: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
):
    """
    Get list of heroes with optional filtering and pagination.

    - **offset**: Number of records to skip
    - **limit**: Maximum number of records to return (max 100)
    - **name**: Filter by name (partial match)
    - **min_age**: Minimum age filter
    - **max_age**: Maximum age filter
    """
    statement = select(Hero)

    # Apply filters
    if name:
        statement = statement.where(Hero.name.ilike(f"%{name}%"))
    if min_age is not None:
        statement = statement.where(Hero.age >= min_age)
    if max_age is not None:
        statement = statement.where(Hero.age <= max_age)

    # Apply pagination
    statement = statement.offset(offset).limit(limit)

    heroes = session.exec(statement).all()
    return heroes


@app.get("/heroes/{hero_id}", response_model=HeroPublicWithTeam, tags=["heroes"])
def read_hero(*, session: SessionDep, hero_id: int):
    """Get a specific hero by ID."""
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.patch("/heroes/{hero_id}", response_model=HeroPublic, tags=["heroes"])
def update_hero(*, session: SessionDep, hero_id: int, hero: HeroUpdate):
    """Update a hero (partial update allowed)."""
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    # Validate team exists if being updated
    if hero.team_id is not None:
        team = session.get(Team, hero.team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

    # Update only provided fields
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)

    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@app.delete("/heroes/{hero_id}", tags=["heroes"])
def delete_hero(*, session: SessionDep, hero_id: int):
    """Delete a hero."""
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    session.delete(hero)
    session.commit()
    return {"ok": True, "message": f"Hero {hero.name} deleted"}


# ===== TEAM ENDPOINTS =====

@app.post("/teams/", response_model=TeamPublic, status_code=201, tags=["teams"])
def create_team(*, session: SessionDep, team: TeamCreate):
    """Create a new team."""
    db_team = Team.model_validate(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.get("/teams/", response_model=List[TeamPublic], tags=["teams"])
def read_teams(
    *,
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    """Get list of teams with pagination."""
    teams = session.exec(select(Team).offset(offset).limit(limit)).all()
    return teams


@app.get("/teams/{team_id}", response_model=TeamPublicWithHeroes, tags=["teams"])
def read_team(*, session: SessionDep, team_id: int):
    """Get a specific team by ID with its heroes."""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.patch("/teams/{team_id}", response_model=TeamPublic, tags=["teams"])
def update_team(*, session: SessionDep, team_id: int, team: TeamUpdate):
    """Update a team (partial update allowed)."""
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")

    team_data = team.model_dump(exclude_unset=True)
    db_team.sqlmodel_update(team_data)

    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.delete("/teams/{team_id}", tags=["teams"])
def delete_team(*, session: SessionDep, team_id: int):
    """Delete a team."""
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    session.delete(team)
    session.commit()
    return {"ok": True, "message": f"Team {team.name} deleted"}


# ===== HEALTH CHECK =====

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
