from fastapi import FastAPI
from routers import flight

app = FastAPI()

app.include_router(flight.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="172.30.238.204", port=1596)