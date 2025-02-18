from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import uvicorn
import os

from models import User, SessionLocal
from schemas import Token, UserCreate
from game_manager import GameManager
from auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    game_loop = asyncio.create_task(update_game_loop())
    yield
    # Shutdown
    game_loop.cancel()
    try:
        await game_loop
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

# Use pathlib for cross-platform path handling
STATIC_DIR = Path("static")
TEMPLATES_DIR = Path("templates")
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates configuration
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize game manager
game_manager = GameManager()

# Database dependency using context manager
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    
    # Add to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": new_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "message": "Registration successful",
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Verify user credentials
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        ),
        "token_type": "bearer"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await game_manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                if data["type"] == "add_point":
                    await game_manager.add_player_point(data["x"], data["y"])
            except WebSocketDisconnect:
                await game_manager.handle_disconnect(websocket)
                break
            except Exception as e:
                await game_manager.handle_disconnect(websocket)
                break
    except Exception as e:
        await game_manager.handle_disconnect(websocket)

# Add this at the top of main.py
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def update_game_loop():
    while True:
        try:
            # Count down from 5 to 0
            for i in range(5, -1, -1):
                await game_manager.update_timer(i)
                if i > 0:  # Only sleep if not at 0
                    await asyncio.sleep(1)
            
            # When timer hits 0, update game state with timeout
            try:
                async with asyncio.timeout(2.0):  # Use 2 second timeout
                    await game_manager.update_game()
            except TimeoutError:
                logging.error("Game state update timed out")
            except Exception as e:
                logging.error(f"Error updating game state: {e}")            
        except asyncio.CancelledError:
            logging.info("Game loop cancelled")
            break
        except Exception as e:
            logging.error(f"Unexpected error in game loop: {e}")
            # Add a small delay before retrying
            await asyncio.sleep(0.5)

@app.get("/grid")
async def get_grid():
    try:
        return {"grid": game_manager.game_state.get_state().tolist()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving grid state: {str(e)}"
        )

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  
        port=port,
        reload=True  
    )