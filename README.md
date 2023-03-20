# SQLAlchemy Boilerplate

SQLAlchemy Boilerplate is a wrapper around SQLAlchemy that provides 2 minimal boilerplate classes to connect to PGSQL and SQLite databases:
 - **Boilerplate**: SQL database abstraction class.
 - **AsyncBoilerplate**: SQL database abstraction class with async methods

## Examples
Classes can be used as a method:
```
database = AsyncBoilerplate(
    url="sqlite://",
    echo=False,
    create_tables=True
)
database = await database()
async for row in database.execute(...):
    print(row)
await databse.disconnect()
```

# Within a context:
```
async with AsyncBoilerplate(
    url="sqlite://",
    echo=False,
    create_tables=True
) as database:
    async for row in database.execute(...):
        print(row)
```

# Or as regular classes:
```
database = AsyncBoilerplate(
    url="sqlite://",
    echo=False,
    create_tables=True
)
await database.connext()
async for row in database.execute(...):
    print(row)
await database.disconnect()
```
