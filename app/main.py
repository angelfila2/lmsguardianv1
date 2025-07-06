from fastapi import FastAPI
from app.routes.unitCoordinator import router as unitCoordinatorRouter
from app.routes.module import router as moduleRouter
from app.routes.scrapedContent import router as scrapedContentRouter
from app.routes.scrapedSession import router as scrapedSessionRouter
from app.database.database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(unitCoordinatorRouter)
app.include_router(moduleRouter)
app.include_router(scrapedContentRouter)
app.include_router(scrapedSessionRouter)
