from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from database import create_tables
from auth import router as auth_router
from users import router as users_router
from extensions import router as extensions_router
from analysis import router as analysis_router
from reports import router as reports_router
from admin import router as admin_router

# Security scheme
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown

# Create FastAPI app
app = FastAPI(
    title="CheckMe API",
    description="Browser Extension Security Analysis Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(extensions_router, prefix="/api/extensions", tags=["extensions"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "CheckMe API - Browser Extension Security Analysis Platform"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)