# SQLModel Queries and Filtering

## Table of Contents
1. Basic SELECT Queries
2. WHERE Clauses and Filtering
3. Joins
4. Pagination and Limiting
5. Ordering and Sorting
6. Aggregations and Grouping
7. Complex Query Patterns

---

## 1. Basic SELECT Queries

### Select All

```python
from sqlmodel import select, Session

with Session(engine) as session:
    statement = select(Hero)
    heroes = session.exec(statement).all()
```

### Select Single Record

```python
# By primary key (most efficient)
hero = session.get(Hero, 1)

# First match
statement = select(Hero).where(Hero.name == "Spider-Boy")
hero = session.exec(statement).first()

# One result (raises error if 0 or >1 results)
hero = session.exec(statement).one()
```

### Select Specific Columns

```python
statement = select(Hero.name, Hero.age)
results = session.exec(statement).all()
# Returns tuples: [('Spider-Boy', 15), ...]
```

---

## 2. WHERE Clauses and Filtering

### Equality

```python
statement = select(Hero).where(Hero.name == "Spider-Boy")
```

### Multiple Conditions (AND)

```python
statement = select(Hero).where(
    Hero.age > 30,
    Hero.team_id == 1
)
# Equivalent to: WHERE age > 30 AND team_id = 1
```

### OR Conditions

```python
from sqlmodel import or_

statement = select(Hero).where(
    or_(Hero.name == "Iron Man", Hero.name == "Thor")
)
```

### Comparison Operators

```python
# Greater than
statement = select(Hero).where(Hero.age > 30)

# Less than or equal
statement = select(Hero).where(Hero.age <= 25)

# Not equal
statement = select(Hero).where(Hero.name != "Deadpool")

# BETWEEN
from sqlmodel import and_
statement = select(Hero).where(and_(Hero.age >= 20, Hero.age <= 40))
```

### IN Clause

```python
names = ["Iron Man", "Thor", "Hulk"]
statement = select(Hero).where(Hero.name.in_(names))
```

### LIKE Pattern Matching

```python
# Contains
statement = select(Hero).where(Hero.name.like("%man%"))

# Starts with
statement = select(Hero).where(Hero.name.like("Spider%"))

# Case-insensitive (PostgreSQL)
statement = select(Hero).where(Hero.name.ilike("%MAN%"))
```

### NULL Checks

```python
# IS NULL
statement = select(Hero).where(Hero.age.is_(None))

# IS NOT NULL
statement = select(Hero).where(Hero.age.is_not(None))
```

---

## 3. Joins

### Implicit Join (via Relationship)

```python
statement = select(Hero).where(Hero.team.has(Team.name == "Avengers"))
```

### Explicit Inner Join

```python
statement = select(Hero, Team).join(Team)
results = session.exec(statement).all()
# Returns tuples: [(Hero, Team), ...]
```

### Left Outer Join

```python
statement = select(Hero).join(Team, isouter=True)
```

### Join with WHERE

```python
statement = (
    select(Hero)
    .join(Team)
    .where(Team.name == "Avengers")
)
```

### Filtering Joined Data

```python
from sqlalchemy.orm import selectinload

# Eager load team data
statement = select(Hero).options(selectinload(Hero.team))
heroes = session.exec(statement).all()

# Now team.name doesn't trigger additional queries
for hero in heroes:
    if hero.team:
        print(f"{hero.name} -> {hero.team.name}")
```

---

## 4. Pagination and Limiting

### LIMIT

```python
statement = select(Hero).limit(10)
heroes = session.exec(statement).all()
```

### OFFSET and LIMIT (Pagination)

```python
page = 2
page_size = 10

statement = select(Hero).offset((page - 1) * page_size).limit(page_size)
heroes = session.exec(statement).all()
```

### Pagination in FastAPI

```python
@app.get("/heroes/", response_model=List[HeroPublic])
def read_heroes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    statement = select(Hero).offset(offset).limit(limit)
    heroes = session.exec(statement).all()
    return heroes
```

---

## 5. Ordering and Sorting

### ORDER BY (Ascending)

```python
statement = select(Hero).order_by(Hero.name)
```

### ORDER BY (Descending)

```python
from sqlmodel import desc

statement = select(Hero).order_by(desc(Hero.age))
```

### Multiple ORDER BY

```python
statement = select(Hero).order_by(Hero.team_id, desc(Hero.age))
```

---

## 6. Aggregations and Grouping

### COUNT

```python
from sqlmodel import func

statement = select(func.count(Hero.id))
count = session.exec(statement).one()
```

### COUNT with WHERE

```python
statement = select(func.count(Hero.id)).where(Hero.age > 30)
count = session.exec(statement).one()
```

### GROUP BY

```python
statement = (
    select(Hero.team_id, func.count(Hero.id))
    .group_by(Hero.team_id)
)
results = session.exec(statement).all()
# Returns: [(1, 5), (2, 3), ...] (team_id, count)
```

### Other Aggregates

```python
# Average
statement = select(func.avg(Hero.age))

# Min/Max
statement = select(func.min(Hero.age), func.max(Hero.age))

# Sum
statement = select(func.sum(Hero.age))
```

---

## 7. Complex Query Patterns

### Subqueries

```python
# Find heroes in teams with > 3 members
subquery = (
    select(Hero.team_id)
    .group_by(Hero.team_id)
    .having(func.count(Hero.id) > 3)
)

statement = select(Hero).where(Hero.team_id.in_(subquery))
```

### EXISTS

```python
statement = select(Team).where(
    Team.id.in_(select(Hero.team_id))
)
# Teams that have at least one hero
```

### DISTINCT

```python
statement = select(Hero.team_id).distinct()
```

### Union

```python
from sqlmodel import union

statement1 = select(Hero).where(Hero.age < 20)
statement2 = select(Hero).where(Hero.age > 60)

statement = union(statement1, statement2)
```

### Window Functions

```python
from sqlalchemy import over

statement = select(
    Hero.name,
    Hero.age,
    func.rank().over(order_by=desc(Hero.age))
)
```

---

## Complete Query Examples

### Search with Multiple Filters

```python
def search_heroes(
    session: Session,
    name: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    team_id: Optional[int] = None
) -> List[Hero]:
    statement = select(Hero)

    if name:
        statement = statement.where(Hero.name.ilike(f"%{name}%"))

    if min_age is not None:
        statement = statement.where(Hero.age >= min_age)

    if max_age is not None:
        statement = statement.where(Hero.age <= max_age)

    if team_id is not None:
        statement = statement.where(Hero.team_id == team_id)

    heroes = session.exec(statement).all()
    return heroes
```

### Pagination with Total Count

```python
def get_heroes_paginated(
    session: Session,
    page: int = 1,
    page_size: int = 10
) -> dict:
    # Get total count
    count_statement = select(func.count(Hero.id))
    total = session.exec(count_statement).one()

    # Get paginated results
    statement = (
        select(Hero)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .order_by(Hero.id)
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

### Complex Join with Aggregation

```python
# Get teams with hero count and average age
statement = (
    select(
        Team.id,
        Team.name,
        func.count(Hero.id).label("hero_count"),
        func.avg(Hero.age).label("avg_age")
    )
    .join(Hero, isouter=True)
    .group_by(Team.id, Team.name)
    .order_by(desc("hero_count"))
)

results = session.exec(statement).all()
for team_id, name, count, avg_age in results:
    print(f"{name}: {count} heroes, avg age {avg_age:.1f}")
```
