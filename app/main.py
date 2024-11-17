from fastapi import FastAPI
from .database import engine
from . import models
from .routers import user, auth, business, service, vote, category, subscription, transaction
from .config import Settings
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind = engine)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(business.router)
app.include_router(service.router)
app.include_router(auth.router)
app.include_router(vote.router)
app.include_router(category.router)
app.include_router(subscription.router)
app.include_router(transaction.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
