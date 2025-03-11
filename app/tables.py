from sqlalchemy import inspect
from .models import Base, path # Dependency to get the database session


# Function to check and create tables if they don't exist
def check_tables(engine):
    inspector = inspect(engine)
    for table in path.values():
        if not inspector.has_table(table):
            Base.metadata.create_all(bind=engine)
            print(f"Table '{table}' created.")
        else:
            print(f"Table '{table}' already exists.")