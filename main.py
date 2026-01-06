from fastapi import FastAPI     
from routers import books, auth, oauth
from contextlib import asynccontextmanager
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await init_db()
    yield
    print("Shutting down...")





version = "2.0.0"

app = FastAPI(
    title="Bookly",
    description="A REST API for a book review web service with advanced authentication",
    version=version,
    lifespan=lifespan
)

# Include routers
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(books.router)



