from fastapi import FastAPI
from app.endpoints import links, auth
from app.initial_db import init_db

app = FastAPI(
    title="Shorturler API",
    description="Сокращатель ссылок",
    version="1.0"
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(links.router, prefix="/links", tags=["Links"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Shorturler!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
