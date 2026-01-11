# SQLModel Relationships and Foreign Keys

## Table of Contents
1. Foreign Keys Basics
2. One-to-Many Relationships
3. Many-to-One Relationships
4. One-to-One Relationships
5. Many-to-Many Relationships
6. Relationship Configuration
7. Loading Strategies

---

## 1. Foreign Keys Basics

### Simple Foreign Key

```python
from sqlmodel import Field, SQLModel
from typing import Optional

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
```

**Key Points**:
- `foreign_key="team.id"` references the `id` column of the `team` table
- Table name is lowercase by default
- `team_id` is nullable (`Optional[int]`) - heroes can exist without teams

### Non-Nullable Foreign Key

```python
class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: int = Field(foreign_key="team.id")  # Required, not Optional
```

### Custom Table Names

```python
class Team(SQLModel, table=True):
    __tablename__ = "teams_table"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="teams_table.id")
```

---

## 2. One-to-Many Relationships

### Basic One-to-Many Setup

```python
from sqlmodel import Relationship
from typing import List

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # One team has many heroes
    heroes: List["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # Many heroes belong to one team
    team: Optional[Team] = Relationship(back_populates="heroes")
```

**Usage**:
```python
with Session(engine) as session:
    # Create team
    team = Team(name="Avengers")
    session.add(team)
    session.commit()
    session.refresh(team)

    # Create heroes linked to team
    hero1 = Hero(name="Iron Man", team_id=team.id)
    hero2 = Hero(name="Thor", team_id=team.id)
    session.add(hero1)
    session.add(hero2)
    session.commit()

    # Access relationship
    print(f"Team: {team.name}")
    print(f"Heroes: {[h.name for h in team.heroes]}")
    # Output: Team: Avengers
    #         Heroes: ['Iron Man', 'Thor']

    # Reverse direction
    session.refresh(hero1)
    print(f"{hero1.name} belongs to {hero1.team.name}")
    # Output: Iron Man belongs to Avengers
```

### Multiple Model Pattern with Relationships

```python
from typing import List

# ===== TEAM MODELS =====
class TeamBase(SQLModel):
    name: str = Field(index=True)
    headquarters: str

class Team(TeamBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    heroes: List["Hero"] = Relationship(back_populates="team")

class TeamCreate(TeamBase):
    pass

class TeamPublic(TeamBase):
    id: int

class TeamPublicWithHeroes(TeamPublic):
    heroes: List["HeroPublic"] = []

# ===== HERO MODELS =====
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = None

class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team: Optional[Team] = Relationship(back_populates="heroes")

class HeroCreate(HeroBase):
    team_id: Optional[int] = None

class HeroPublic(HeroBase):
    id: int

class HeroPublicWithTeam(HeroPublic):
    team: Optional[TeamPublic] = None
```

**API Usage**:
```python
@app.get("/teams/{team_id}", response_model=TeamPublicWithHeroes)
def read_team_with_heroes(team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team  # SQLModel automatically serializes heroes
```

---

## 3. Many-to-One Relationships

Many-to-one is the **inverse** of one-to-many (already covered above).

```python
class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # Many heroes -> One team
    team: Optional["Team"] = Relationship(back_populates="heroes")
```

**Accessing the relationship**:
```python
hero = session.get(Hero, 1)
print(f"{hero.name} is in team: {hero.team.name}")
```

---

## 4. One-to-One Relationships

### Example: User and Profile

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)

    # One-to-one: sa_relationship_kwargs for uniqueness
    profile: Optional["UserProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}  # One-to-one
    )

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    # Foreign key with unique constraint for one-to-one
    user_id: int = Field(foreign_key="user.id", unique=True)

    # One-to-one back reference
    user: User = Relationship(back_populates="profile")
```

**Usage**:
```python
with Session(engine) as session:
    user = User(username="alice")
    session.add(user)
    session.commit()
    session.refresh(user)

    profile = UserProfile(user_id=user.id, bio="Software Engineer")
    session.add(profile)
    session.commit()

    # Access
    session.refresh(user)
    print(f"{user.username}'s bio: {user.profile.bio}")
```

---

## 5. Many-to-Many Relationships

Requires a **link table** (association table).

### Basic Many-to-Many

```python
# Link table
class HeroTeamLink(SQLModel, table=True):
    hero_id: Optional[int] = Field(
        default=None, foreign_key="hero.id", primary_key=True
    )
    team_id: Optional[int] = Field(
        default=None, foreign_key="team.id", primary_key=True
    )

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    heroes: List["Hero"] = Relationship(
        back_populates="teams",
        link_model=HeroTeamLink
    )

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    teams: List[Team] = Relationship(
        back_populates="heroes",
        link_model=HeroTeamLink
    )
```

**Usage**:
```python
with Session(engine) as session:
    # Create teams
    avengers = Team(name="Avengers")
    xmen = Team(name="X-Men")
    session.add(avengers)
    session.add(xmen)
    session.commit()

    # Create hero in multiple teams
    wolverine = Hero(name="Wolverine")
    wolverine.teams = [avengers, xmen]

    session.add(wolverine)
    session.commit()

    # Access
    session.refresh(wolverine)
    print(f"{wolverine.name} is in: {[t.name for t in wolverine.teams]}")
    # Output: Wolverine is in: ['Avengers', 'X-Men']
```

### Many-to-Many with Extra Fields on Link Table

```python
from datetime import datetime

# Link table with additional data
class HeroTeamLink(SQLModel, table=True):
    hero_id: Optional[int] = Field(
        default=None, foreign_key="hero.id", primary_key=True
    )
    team_id: Optional[int] = Field(
        default=None, foreign_key="team.id", primary_key=True
    )

    # Additional fields
    joined_date: datetime = Field(default_factory=datetime.utcnow)
    role: str = Field(default="Member")

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    hero_links: List[HeroTeamLink] = Relationship()

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    team_links: List[HeroTeamLink] = Relationship()
```

**Usage with extra fields**:
```python
with Session(engine) as session:
    hero = Hero(name="Iron Man")
    team = Team(name="Avengers")
    session.add(hero)
    session.add(team)
    session.commit()

    # Create link with extra fields
    link = HeroTeamLink(
        hero_id=hero.id,
        team_id=team.id,
        role="Leader",
        joined_date=datetime(2012, 5, 4)
    )
    session.add(link)
    session.commit()

    # Access
    session.refresh(hero)
    for link in hero.team_links:
        print(f"Role: {link.role}, Joined: {link.joined_date}")
```

---

## 6. Relationship Configuration

### back_populates

Establishes **bidirectional** relationship.

```python
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    heroes: List["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team: Optional[Team] = Relationship(back_populates="heroes")
```

### sa_relationship_kwargs

Pass additional SQLAlchemy relationship parameters.

```python
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    heroes: List["Hero"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={
            "lazy": "selectin",  # Loading strategy
            "cascade": "all, delete-orphan",  # Cascade deletes
            "order_by": "Hero.name"  # Order results
        }
    )
```

### Cascade Deletes

```python
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    heroes: List["Hero"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team: Optional[Team] = Relationship(back_populates="heroes")
```

**Effect**:
```python
# Deleting team also deletes all heroes in that team
session.delete(team)
session.commit()
```

---

## 7. Loading Strategies

### Lazy Loading (Default)

Relationships are loaded when accessed.

```python
hero = session.get(Hero, 1)
# No database query yet for team

print(hero.team.name)
# NOW queries database for team
```

**Pros**: Efficient if relationship not always needed
**Cons**: N+1 query problem

### Eager Loading with selectin

```python
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    heroes: List["Hero"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
```

**Effect**: Loads related data with minimal queries

### Manual Eager Loading with Joins

```python
from sqlmodel import select
from sqlalchemy.orm import selectinload

statement = select(Hero).options(selectinload(Hero.team))
heroes = session.exec(statement).all()

# All teams are pre-loaded, no additional queries
for hero in heroes:
    print(f"{hero.name} -> {hero.team.name}")
```

---

## Complete Example: Blog with Posts and Comments

```python
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, List
from datetime import datetime

# ===== USER MODELS =====
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)

    posts: List["Post"] = Relationship(back_populates="author")
    comments: List["Comment"] = Relationship(back_populates="author")

# ===== POST MODELS =====
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship(back_populates="posts")

    comments: List["Comment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

# ===== COMMENT MODELS =====
class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    post_id: int = Field(foreign_key="post.id")
    post: Post = Relationship(back_populates="comments")

    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship(back_populates="comments")
```

**Usage**:
```python
with Session(engine) as session:
    # Create user
    user = User(username="alice", email="alice@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create post
    post = Post(
        title="My First Post",
        content="Hello World!",
        author_id=user.id
    )
    session.add(post)
    session.commit()
    session.refresh(post)

    # Create comment
    comment = Comment(
        content="Great post!",
        post_id=post.id,
        author_id=user.id
    )
    session.add(comment)
    session.commit()

    # Query with relationships
    statement = select(Post).where(Post.author_id == user.id)
    user_posts = session.exec(statement).all()

    for post in user_posts:
        print(f"Post: {post.title} by {post.author.username}")
        print(f"Comments: {len(post.comments)}")
        for comment in post.comments:
            print(f"  - {comment.author.username}: {comment.content}")
```
