from fastapi import FastAPI
from . import models
from .database import engine
from .routes import router

app = FastAPI()

# Auto-create tables from models (already done if seeded manually)
models.Base.metadata.create_all(bind=engine)

# Add routes
app.include_router(router)
