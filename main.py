from fastapi import FastAPI
import users as u

app = FastAPI()

app.include_router(u.router)

