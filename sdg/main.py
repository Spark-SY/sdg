from fastapi import FastAPI

from .poc import poc


app = FastAPI(
    docs_url="/api/docs",
)

app = FastAPI()

@app.get("/")
async def hello() -> dict[str, str]:
    return {"message": "Hello World"}

@app.post("/poc")
async def test():
    poc()
