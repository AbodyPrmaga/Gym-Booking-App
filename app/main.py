from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth, bookings, services, slots, users

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Main Endpoints"])
async def root():
    return {"message": "API is running successfully 🚀", "status": "ok"}


routers = [auth.router, bookings.router, services.router, slots.router, users.router]

for router in routers:
    app.include_router(router)