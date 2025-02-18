# Red vs Blue Territory Control Game

A multiplayer web-based tactical game where players control blue units to eliminate red obstacles through strategic placement and coordinated movements.

## Features

- Real-time multiplayer gameplay using WebSocket connections
- User authentication with JWT tokens
- Interactive grid-based tactical gameplay
- Strategic movement system for blue units
- Strength-based elimination mechanics
- Real-time game statistics and scoring
- Territory control visualization
- Cluster analysis for both teams
- Victory conditions and end-game statistics
- Multiple difficulty levels and patterns

## Game Rules

- Red squares are static obstacles that players need to eliminate
- Players can place blue squares in empty cells
- Blue squares will move tactically towards nearby red targets
- Blue units can eliminate red obstacles when sufficient blue strength is nearby
- Game updates occur every 5 seconds
- Victory is achieved when all red obstacles are eliminated

## Technologies Used

- Backend:
  - FastAPI
  - SQLAlchemy
  - WebSockets
  - JWT Authentication
  - Numpy for game logic
  - SQLite for user management

- Frontend:
  - Vanilla JavaScript
  - HTML5
  - CSS3
  - WebSocket client

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd red-blue-territory-control
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add the following variables:
```bash
SECRET_KEY=your_secure_secret_key_here
```
   To generate a secure secret key, you can use:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Running the Application

1. Start the server:
```bash
uvicorn main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Game Mechanics

### Blue Unit Behavior
- Blue units actively seek out the nearest red targets
- Multiple blue units can combine their strength
- When blue strength reaches a threshold, nearby red obstacles are eliminated
- Units move tactically to maintain formation and effectiveness

### Scoring System
- Track territory control percentage
- Count number of clusters for both red and blue
- Monitor activity levels and placement efficiency
- Calculate final victory ranking based on:
  - Point efficiency
  - Speed rating
  - Click efficiency

### Victory Conditions
- Eliminate all red obstacles
- Final score based on:
  - Total rounds taken
  - Number of points placed
  - Efficiency ratio
- Rankings from "Aspiring Strategist" to "Master Tactician"

## Architecture

### Backend Components

- `main.py`: FastAPI application entry point and route definitions
- `game_manager.py`: WebSocket and game state management
- `game_logic.py`: Core game mechanics and tactical rules
- `auth.py`: Authentication and user management
- `models.py`: Database models
- `schemas.py`: Pydantic models for request/response validation
- `patterns.py`: Game pattern definitions and management

### Frontend Components

- `static/js/game.js`: Client-side game logic and WebSocket handling
- `static/css/styles.css`: Game styling and animations
- `templates/index.html`: Main game interface

## Environment Configuration

Create a .env file in the root directory with the following variables:
```bash
# Required - Secret key for JWT token generation
SECRET_KEY=your_secure_secret_key_here

# Required - Comma-separated list of allowed origins for CORS
ALLOWED_ORIGINS=https://your-domain.onrender.com,http://localhost:8000
```

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- WebSocket connection management
- CORS middleware
- Input validation
- Error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.