from fastapi import FastAPI                          # Line 1
from fastapi.middleware.cors import CORSMiddleware  # Line 2
from motor.motor_asyncio import AsyncIOMotorClient  # Line 3
from contextlib import asynccontextmanager          # Line 4
from config import MONGODB_URL, DATABASE_NAME       # Line 5
from routes.resume import router                    # Line 6


# STARTUP & SHUTDOWN — Database Connection

@asynccontextmanager                                # Line 13
async def lifespan(app: FastAPI):                   # Line 14

    # --- This runs when server STARTS ---
    print("Connecting to MongoDB...")               # Line 17
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URL)  # Line 18
    app.db = app.mongodb_client[DATABASE_NAME]      # Line 19
    print("MongoDB connected successfully!")        # Line 20

    yield                                           # Line 22

    # --- This runs when server STOPS ---
    print("Closing MongoDB connection...")          # Line 25
    app.mongodb_client.close()                      # Line 26
    print("MongoDB connection closed.")             # Line 27



# CREATE THE FASTAPI APP

app = FastAPI(                                      # Line 33
    title="Resume Parser API",                      # Line 34
    description="Automatically parse resumes and extract candidate information.",  # Line 35
    version="1.0.0",                               # Line 36
    lifespan=lifespan                              # Line 37
)


# CORS — Allow Frontend to Talk to Backend


app.add_middleware(                                 # Line 44
    CORSMiddleware,                                 # Line 45
    allow_origins=["http://localhost:3000"],        # Line 46
    allow_credentials=True,                         # Line 47
    allow_methods=["*"],                            # Line 48
    allow_headers=["*"],                            # Line 49
)


# REGISTER ROUTES

app.include_router(router, prefix="/api/resumes", tags=["Resumes"])  # Line 55



# ROOT ENDPOINT — Health Check


@app.get("/")                                       # Line 61
async def root():                                   # Line 62
    return {                                        # Line 63
        "message": "Resume Parser API is running!",
        "docs": "Visit /docs to see all endpoints",
        "status": "healthy"
    }