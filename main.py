from fastapi import FastAPI
from app.users import router as user_router

# Create the FastAPI app
app = FastAPI()

# # Start Mode : Check and create the tables when the app starts
# # option : delete > create, trunced, no action
# from app.database import engine  # Dependency to get the database session
# from app.tables import check_tables
# check_tables(engine)
# # if any table, set auto increament

# Include the user routes in the FastAPI app
app.include_router(user_router)
