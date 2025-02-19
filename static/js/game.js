// Game constants and state
const GRID_SIZE = 30;
let isDrawing = false;
let lastCell = null;
const visitedCells = new Set();
let grid = Array(GRID_SIZE)
  .fill()
  .map(() => Array(GRID_SIZE).fill(0));
let updateTimer = 5;
let serverTimer = 5;
let timerInterval = null;

// WebSocket connection management
class WebSocketManager {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.baseReconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.intentionalClose = false;
    this.pingInterval = null;
    this.pongTimeout = null;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("WebSocket already connected");
      return;
    }

    if (this.ws?.readyState === WebSocket.CONNECTING) {
      console.log("WebSocket connection in progress");
      return;
    }

    this.cleanup(); // Clean up any existing connection

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
      this.setupHeartbeat();
    } catch (error) {
      console.error("WebSocket creation error:", error);
      this.handleConnectionError();
    }
  }

  setupEventHandlers() {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log("Connected to game server");
      this.reconnectAttempts = 0;
      this.intentionalClose = false;
      showGame();
      createGrid();
    };

    this.ws.onmessage = (event) => {
      // Reset pong timeout on any message
      if (this.pongTimeout) {
        clearTimeout(this.pongTimeout);
        this.pongTimeout = null;
      }
      handleServerMessage(event);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.handleConnectionError();
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed with code ${event.code}`);
      this.cleanup();

      if (!this.intentionalClose) {
        this.handleConnectionError();
      }
    };
  }

  setupHeartbeat() {
    // Clear any existing intervals
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    // Send ping every 30 seconds
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));

        // Set timeout for pong response
        this.pongTimeout = setTimeout(() => {
          console.log("Pong timeout - reconnecting");
          this.handleConnectionError();
        }, 5000); // 5 second timeout
      }
    }, 30000);
  }

  handleConnectionError() {
    this.cleanup();

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log("Max reconnection attempts reached");
      this.handleMaxReconnectFailure();
      return;
    }

    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    console.log(
      `Attempting to reconnect in ${delay}ms (attempt ${
        this.reconnectAttempts + 1
      }/${this.maxReconnectAttempts})`
    );

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
    if (this.ws) {
      try {
        this.ws.close(1000, "Normal closure");
      } catch (e) {
        console.warn("Error closing websocket:", e);
      }
      this.ws = null;
    }
  }

  handleMaxReconnectFailure() {
    const errorMsg = document.createElement("div");
    errorMsg.className = "error-message";
    errorMsg.textContent =
      "Unable to connect to game server. Please refresh the page or try again later.";
    document.getElementById("gameContainer").prepend(errorMsg);

    this.cleanup();
    this.reconnectAttempts = 0;
    this.intentionalClose = false;
  }

  sendMessage(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error("Error sending message:", error);
        this.handleConnectionError();
      }
    } else {
      console.warn("Cannot send message: WebSocket is not connected");
    }
  }

  disconnect() {
    this.intentionalClose = true;
    this.cleanup();
  }
}

// Initialize WebSocket manager
const wsManager = new WebSocketManager();

// Cache DOM elements
const elements = {
  loginSection: document.getElementById("loginSection"),
  registerSection: document.getElementById("registerSection"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  showRegisterLink: document.getElementById("showRegister"),
  showLoginLink: document.getElementById("showLogin"),
  authContainer: document.getElementById("authContainer"),
  gameContainer: document.getElementById("gameContainer"),
  logoutBtn: document.getElementById("logoutBtn"),
  timer: document.getElementById("timer"),
  redScore: document.getElementById("redScore"),
  blueScore: document.getElementById("blueScore"),
  roundCounter: document.getElementById("roundCounter"),
  gridContainer: document.getElementById("grid"),
};

// Event listeners
elements.loginForm.addEventListener("submit", handleLogin);
elements.registerForm.addEventListener("submit", handleRegister);
elements.showRegisterLink.addEventListener("click", () =>
  toggleForms("register")
);
elements.showLoginLink.addEventListener("click", () => toggleForms("login"));
elements.logoutBtn.addEventListener("click", handleLogout);

// Form handling
function toggleForms(form) {
  elements.loginSection.classList.toggle("hidden", form === "register");
  elements.registerSection.classList.toggle("hidden", form === "login");
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const errorElement = document.getElementById("loginError");

  try {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch("/token", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    errorElement.classList.add("hidden");
    connectWebSocket();
  } catch (error) {
    errorElement.textContent = "Login failed. Please check your credentials.";
    errorElement.classList.remove("hidden");
    console.error("Login error:", error);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById("regUsername").value;
  const password = document.getElementById("regPassword").value;
  const errorElement = document.getElementById("registerError");
  const successElement = document.getElementById("registerSuccess");

  try {
    const response = await fetch("/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed");
    }

    const data = await response.json();
    localStorage.setItem("token", data.access_token);

    successElement.textContent = "Registration successful!";
    successElement.classList.remove("hidden");
    errorElement.classList.add("hidden");

    connectWebSocket();
  } catch (error) {
    errorElement.textContent =
      error.message || "Registration failed. Please try again.";
    errorElement.classList.remove("hidden");
    successElement.classList.add("hidden");
    console.error("Registration error:", error);
  }
}

function handleLogout() {
  localStorage.removeItem("token");
  cleanupGame();
  showAuth();
}

// Game functions
function startTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
  }

  updateTimer = 5;
  updateTimerDisplay();

  timerInterval = setInterval(() => {
    updateTimer = Math.max(0, updateTimer - 1);
    updateTimerDisplay();

    if (updateTimer <= 0) {
      updateTimer = 5;
    }
  }, 1000);
}

function updateTimerDisplay() {
  const timerElement = document.getElementById("timer");
  if (timerElement) {
    timerElement.textContent = `${serverTimer}s`;
  }
}

function handleServerMessage(event) {
  try {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case "game_reset":
        // Handle game reset
        isGameOver = false;
        gameOverOverlay.classList.remove("visible");

        // Reset stats display
        document.getElementById("finalRounds").textContent = "0";
        document.getElementById("finalPoints").textContent = "0";
        document.getElementById("finalEfficiency").textContent = "0";

        // Update pattern info if you have UI elements for it
        if (data.pattern_info) {
          updatePatternInfo(data.pattern_info);
        }
        break;

        case "timer_update":
          // Handle timer-only updates
          if (typeof data.timer === "number") {
            serverTimer = data.timer;
            updateTimerDisplay();
          }
          break;
  
        case "grid_update":
          if (Array.isArray(data.grid)) {
            updateGrid(data.grid);
            updateGameInfo(data);
  
            // Check for game over
            if (data.game_over && data.final_stats) {
              handleGameOver(data.final_stats);
            }
  
            if (typeof data.timer === "number") {
              serverTimer = data.timer;
              updateTimerDisplay();
            }
          }
          break;

      default:
        console.warn("Unknown message type:", data.type);
    }
  } catch (error) {
    console.error("Error processing message:", error);
    console.error("Raw message:", event.data);
  }
}

function updatePatternInfo(patternInfo) {
  const patternNameElement = document.getElementById("patternName");
  const patternDescElement = document.getElementById("patternDescription");
  const difficultyElement = document.getElementById("difficultyLevel");

  if (patternNameElement) {
    patternNameElement.textContent = patternInfo.name;
  }
  if (patternDescElement) {
    patternDescElement.textContent = patternInfo.description;
  }
  if (difficultyElement) {
    difficultyElement.textContent = `Difficulty: ${patternInfo.difficulty}/5`;
  }
}

function updateGameInfo(data) {
  // Update scores
  if (data.scores) {
    elements.redScore.textContent = data.scores.red || 0;
    elements.blueScore.textContent = data.scores.blue || 0;
  }

  // Update stats
  if (data.stats) {
    // Update clusters
    document.getElementById(
      "redClusters"
    ).textContent = `Clusters: ${data.stats.red_clusters}`;
    document.getElementById(
      "blueClusters"
    ).textContent = `Clusters: ${data.stats.blue_clusters}`;

    // Update round and activity
    elements.roundCounter.textContent = data.stats.current_round;
    document.getElementById(
      "activityScore"
    ).textContent = `Activity: ${data.stats.activity}`;

    // Update territory control
    const territoryControl = document.getElementById("territoryControl");
    const territoryPercent = document.getElementById("territoryPercent");
    territoryControl.style.width = `${data.stats.territory_control}%`;
    territoryPercent.textContent = `${data.stats.territory_control.toFixed(
      1
    )}%`;
  }

  // Update timer
  if (data.timer !== undefined) {
    updateTimer = data.timer;
    updateTimerDisplay();
  }
}

function createGrid() {
  elements.gridContainer.style.gridTemplateColumns = `repeat(${GRID_SIZE}, 30px)`;
  elements.gridContainer.innerHTML = "";

  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.dataset.x = x;
      cell.dataset.y = y;
      
      // Mouse events for desktop
      cell.addEventListener("mousedown", (e) => {
        e.preventDefault(); // Prevent default drag behavior
        isDrawing = true;
        handleCellInteraction(x, y);
      });
      
      cell.addEventListener("mouseover", (e) => {
        if (isDrawing) {
          handleCellInteraction(x, y);
        }
      });
      
      // Touch events for mobile
      cell.addEventListener("touchstart", (e) => {
        e.preventDefault(); // Prevent scrolling
        isDrawing = true;
        const touch = e.touches[0];
        const target = document.elementFromPoint(touch.clientX, touch.clientY);
        if (target && target.classList.contains("cell")) {
          const { x, y } = target.dataset;
          handleCellInteraction(parseInt(x), parseInt(y));
        }
      });
      
      cell.addEventListener("touchmove", (e) => {
        e.preventDefault(); // Prevent scrolling
        if (isDrawing) {
          const touch = e.touches[0];
          const target = document.elementFromPoint(touch.clientX, touch.clientY);
          if (target && target.classList.contains("cell")) {
            const { x, y } = target.dataset;
            handleCellInteraction(parseInt(x), parseInt(y));
          }
        }
      });
      
      elements.gridContainer.appendChild(cell);
    }
  }
  
  // Global event listeners for ending drawing
  document.addEventListener("mouseup", () => {
    isDrawing = false;
    lastCell = null;
    visitedCells.clear();
  });
  
  document.addEventListener("touchend", () => {
    isDrawing = false;
    lastCell = null;
    visitedCells.clear();
  });
  
  // Prevent context menu on right click
  elements.gridContainer.addEventListener("contextmenu", (e) => {
    e.preventDefault();
  });
}

function handleCellInteraction(x, y) {
  // Create a unique cell identifier
  const cellId = `${x},${y}`;
  
  // Check if we've already visited this cell during this drag
  if (visitedCells.has(cellId)) {
    return;
  }
  
  // Add cell to visited set
  visitedCells.add(cellId);
  
  // Get the cell's current state
  const cellState = grid[y][x];
  
  // Only send message if cell is empty (value 0)
  if (cellState === 0) {
    wsManager.sendMessage({
      type: "add_point",
      x: parseInt(x),
      y: parseInt(y),
    });
  }
  
  lastCell = { x, y };
}

function updateGrid(newGrid) {
  if (!Array.isArray(newGrid) || !Array.isArray(newGrid[0])) {
    console.error("Invalid grid data received:", newGrid);
    return;
  }

  grid = newGrid;

  const cells = document.getElementsByClassName("cell");
  const height = newGrid.length;
  const width = newGrid[0].length;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const index = y * GRID_SIZE + x;
      if (index < cells.length) {
        const cell = cells[index];
        cell.classList.remove("red", "blue");

        if (newGrid[y] && typeof newGrid[y][x] !== "undefined") {
          if (newGrid[y][x] === 1) {
            cell.classList.add("red");
          } else if (newGrid[y][x] === 2) {
            cell.classList.add("blue");
          }
        }
      }
    }
  }
}

function handleCellClick(x, y) {
  wsManager.sendMessage({
    type: "add_point",
    x: parseInt(x),
    y: parseInt(y),
  });
}

let isGameOver = false;
const gameOverOverlay = document.getElementById("gameOverOverlay");

// Function to handle game over state
function handleGameOver(finalStats) {
  isGameOver = true;

  const stats = finalStats.stats;
  const rankInfo = finalStats.rank_info;

  // Calculate time metrics
  const minPossibleRounds = Math.ceil(stats.initial_red_count / 2);
  const extraRoundsPercent = Math.round(((stats.total_rounds - minPossibleRounds) / minPossibleRounds) * 100);

  // Update title and description
  document.querySelector('.game-over-title').textContent = rankInfo.title;
  document.querySelector('.game-over-message').textContent = rankInfo.description;

  const statCards = [
      {
          label: "Final Score",
          value: rankInfo.score,
          suffix: "/1000",
          subtext: "Overall performance rating"
      },
      {
          label: "Resource Usage",
          value: stats.efficiency_ratio,
          suffix: "%",
          subtext: `Used ${stats.points_placed} points to clear ${stats.initial_red_count} red`
      },
      {
          label: "Time Efficiency",
          value: stats.total_rounds,
          subtext: `+${extraRoundsPercent}% over minimum (${minPossibleRounds} rounds)`
      },
      {
          label: "Actions",
          value: stats.points_placed,
          suffix: "",
          subtext: `${stats.clicks_per_round.toFixed(1)} points per round`
      }
  ];

  // Get all stat card elements
  const statsContainer = document.querySelector('.game-over-stats');
  statsContainer.innerHTML = ''; // Clear existing stats

  // Create and append stat cards
  statCards.forEach(stat => {
      const card = document.createElement('div');
      card.className = 'stat-card';
      
      card.innerHTML = `
          <div class="stat-label">${stat.label}</div>
          <div class="stat-value">0${stat.suffix || ''}</div>
          <div class="stat-subtext">${stat.subtext}</div>
      `;
      
      statsContainer.appendChild(card);
      
      // Store final value and suffix for animation
      const valueElement = card.querySelector('.stat-value');
      valueElement.dataset.finalValue = stat.value;
      valueElement.dataset.suffix = stat.suffix || '';
  });

  // Show the overlay
  gameOverOverlay.classList.add('visible');

  // Animate the stats
  const statElements = document.querySelectorAll('.stat-card');
  statElements.forEach(statCard => {
      const valueElement = statCard.querySelector('.stat-value');
      if (valueElement) {
          const finalValue = parseFloat(valueElement.dataset.finalValue);
          const suffix = valueElement.dataset.suffix;
          
          animateValue(
              valueElement,
              0,
              finalValue,
              1500,
              finalValue % 1 === 0 ? 0 : 1,
              suffix
          );
      }
  });
}

// Function to handle play again button click
function handlePlayAgain() {
  isGameOver = false;
  gameOverOverlay.classList.remove("visible");

  // Reset stats display
  document.getElementById("finalRounds").textContent = "0";
  document.getElementById("finalPoints").textContent = "0";
  document.getElementById("finalEfficiency").textContent = "0";

  // Reset game state
  wsManager.disconnect();
  cleanupGame();

  // Reconnect to start new game
  setTimeout(() => {
    connectWebSocket();
  }, 500);
}

// Utility function to animate number counting
function animateValue(element, start, end, duration, decimals = 0, suffix = "") {
  const range = end - start;
  const minTimer = 50;
  let stepTime = Math.abs(Math.floor(duration / range));
  stepTime = Math.max(stepTime, minTimer);

  let current = start;
  const step = range / (duration / stepTime);

  function updateValue() {
      current += step;
      if ((step > 0 && current >= end) || (step < 0 && current <= end)) {
          element.textContent = end.toFixed(decimals) + suffix;
          return;
      }
      element.textContent = current.toFixed(decimals) + suffix;
      requestAnimationFrame(updateValue);
  }

  requestAnimationFrame(updateValue);
}

// WebSocket connection
function connectWebSocket() {
  wsManager.connect();
}

function cleanupGame() {
  wsManager.disconnect();
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  grid = Array(GRID_SIZE)
    .fill()
    .map(() => Array(GRID_SIZE).fill(0));
  elements.gridContainer.innerHTML = "";
  serverTimer = 5;
  updateTimerDisplay();
  isGameOver = false;
  gameOverOverlay.classList.remove("visible");
}

// UI state management
function showAuth() {
  elements.loginSection.classList.remove("hidden");
  elements.registerSection.classList.add("hidden");
  elements.authContainer.classList.remove("hidden");
  elements.gameContainer.classList.add("hidden");
}

function showGame() {
  elements.authContainer.classList.add("hidden");
  elements.gameContainer.classList.remove("hidden");
}

// Initialize game if token exists
const token = localStorage.getItem("token");
if (token) {
  connectWebSocket();
}
