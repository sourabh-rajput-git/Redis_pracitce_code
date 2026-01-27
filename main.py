from fastapi import FastAPI
from database import Base, engine
import users as u

#this creates all tables with all associated with Base.metadata into the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(u.router)

