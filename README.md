# Red vs Blue Game of Life

A multiplayer web-based variant of Conway's Game of Life where players compete to eliminate red obstacles using blue cells that follow Game of Life rules.

## Features

- Real-time multiplayer gameplay using WebSocket connections
- User authentication with JWT tokens
- Interactive grid-based gameplay
- Conway's Game of Life rules for blue cells
- Strategic placement mechanics
- Real-time game statistics and scoring
- Territory control visualization
- Cluster analysis for both teams
- Victory conditions and end-game statistics

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

## Game Rules

- Red squares are static obstacles that players need to eliminate
- Players can place blue squares in empty cells
- Blue squares follow Conway's Game of Life rules:
  - Survival: 2-3 neighbors
  - Birth: Exactly 3 neighbors
  - Death: <2 or >3 neighbors
- Blue squares can eliminate red obstacles when sufficient blue cells are nearby
- Game updates occur every 5 seconds
- Victory is achieved when all red obstacles are eliminated

## Architecture

### Backend Components

- `main.py`: FastAPI application entry point and route definitions
- `game_manager.py`: WebSocket and game state management
- `game_logic.py`: Core game mechanics and rules
- `auth.py`: Authentication and user management
- `models.py`: Database models
- `schemas.py`: Pydantic models for request/response validation

### Frontend Components

- `static/js/game.js`: Client-side game logic and WebSocket handling
- `static/css/styles.css`: Game styling and animations
- `templates/index.html`: Main game interface

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