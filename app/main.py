from fastapi import FastAPI
from routers import flight

app = FastAPI()

app.include_router(flight.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.31.114", port=1596)