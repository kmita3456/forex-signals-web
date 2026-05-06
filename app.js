// app.js
const firebaseConfig = {
  apiKey: "AIzaSyDN4GiOCtmtEiVGt8rwW2kjPqrFwE_vUzE",
  authDomain: "metatradebot-v1.firebaseapp.com",
  databaseURL: "https://metatradebot-v1-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "metatradebot-v1",
  storageBucket: "metatradebot-v1.firebasestorage.app",
  messagingSenderId: "787315443175",
  appId: "1:787315443175:web:1d1477a76fd5fe87806942",
  measurementId: "G-QER5HLXXS5"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// === DOM элементы ===
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const logoutBtn = document.getElementById('logout-btn');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const authContainer = document.getElementById('auth-container');
const dashboard = document.getElementById('dashboard');
const signalsList = document.getElementById('signals-list');
const scanStatus = document.getElementById('scan-status');

// === Тема ===
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const body = document.body;

function applyTheme(theme) {
    if (theme === 'light') {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        themeToggleBtn.textContent = '☀️ Светлая';
    } else {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        themeToggleBtn.textContent = '🌙 Тёмная';
    }
    localStorage.setItem('theme', theme);
}

// При загрузке устанавливаем сохранённую тему или тёмную по умолчанию
const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);

themeToggleBtn.addEventListener('click', () => {
    const current = body.classList.contains('dark-theme') ? 'light' : 'dark';
    applyTheme(current);
});

// === Аутентификация ===
loginBtn.addEventListener('click', () => {
    const email = emailInput.value;
    const password = passwordInput.value;
    auth.signInWithEmailAndPassword(email, password).catch(alert);
});
registerBtn.addEventListener('click', () => {
    const email = emailInput.value;
    const password = passwordInput.value;
    auth.createUserWithEmailAndPassword(email, password).catch(alert);
});
logoutBtn.addEventListener('click', () => auth.signOut());

auth.onAuthStateChanged(user => {
    if (user) {
        authContainer.style.display = 'none';
        dashboard.style.display = 'block';
        loadSignals();
        setupControlPanel();
    } else {
        authContainer.style.display = 'block';
        dashboard.style.display = 'none';
    }
});

// === Загрузка сигналов ===
function loadSignals() {
    db.collection('signals').orderBy('timestamp', 'desc').limit(50)
        .onSnapshot(snapshot => {
            signalsList.innerHTML = '';
            snapshot.forEach(doc => {
                const data = doc.data();
                const div = document.createElement('div');
                div.className = 'signal-card';
                div.innerHTML = `
                    <strong>${data.symbol} ${data.timeframe}</strong>
                    <span style="color:${data.direction === 'UP' ? 'green' : 'red'}">${data.direction}</span><br>
                    Confidence: ${data.confidence}%<br>
                    Hold: ${data.hold_time_minutes} min<br>
                    <small>${new Date(data.timestamp).toLocaleString()}</small>
                `;
                signalsList.appendChild(div);
            });
        });
}

// === Панель управления сканированием ===
function setupControlPanel() {
    document.getElementById('start-scan-btn').addEventListener('click', async () => {
        const symbol = document.getElementById('sel-symbol').value;
        const timeframe = document.getElementById('sel-timeframe').value;
        const duration = parseInt(document.getElementById('sel-duration').value);
        const precision = document.getElementById('sel-precision').value;
        const cmdRef = db.collection('commands').doc();
        await cmdRef.set({
            status: "new",
            symbol,
            timeframe,
            duration_minutes: duration,
            precision,
            created_at: firebase.firestore.FieldValue.serverTimestamp()
        });
        scanStatus.textContent = 'Команда отправлена...';
    });
    document.getElementById('default-mode-btn').addEventListener('click', () => {
        scanStatus.textContent = 'Обычный режим активен (бот запущен на сервере).';
    });
}

// ======================================================
//  ИГРА "ЗМЕЙКА"
// ======================================================
const modal = document.getElementById('snake-modal');
const openBtn = document.getElementById('snake-game-btn');
const closeBtn = modal.querySelector('.close-btn');
const canvas = document.getElementById('snake-canvas');
const ctx = canvas.getContext('2d');
const scoreSpan = document.getElementById('snake-score');
const restartBtn = document.getElementById('restart-snake-btn');
const wallRadios = document.getElementsByName('wall-mode');

let gameInterval = null;
let gameActive = false;
let snake = [];
let direction = 'right';
let nextDirection = 'right';
let food = {};
let score = 0;
const gridSize = 20;
let cellSize = 20;
const initialSpeed = 150;
let speed = initialSpeed;
let wallMode = 'walls'; // по умолчанию со стенами

// === Инициализация игры ===
function initGame() {
    // Читаем выбранный режим стен
    for (const radio of wallRadios) {
        if (radio.checked) {
            wallMode = radio.value;
            break;
        }
    }
    const maxSize = Math.min(window.innerWidth - 40, 400);
    cellSize = Math.floor(maxSize / gridSize);
    const canvasSize = cellSize * gridSize;
    canvas.width = canvasSize;
    canvas.height = canvasSize;

    snake = [
        {x: 10, y: 10},
        {x: 9, y: 10},
        {x: 8, y: 10}
    ];
    direction = 'right';
    nextDirection = 'right';
    score = 0;
    speed = initialSpeed;
    scoreSpan.textContent = 'Счёт: 0';
    generateFood();
    draw();
}

function generateFood() {
    const max = gridSize - 1;
    let newFood;
    const snakeSet = new Set(snake.map(s => `${s.x},${s.y}`));
    do {
        newFood = {
            x: Math.floor(Math.random() * (max + 1)),
            y: Math.floor(Math.random() * (max + 1))
        };
    } while (snakeSet.has(`${newFood.x},${newFood.y}`));
    food = newFood;
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#222';
    for (let i = 0; i <= gridSize; i++) {
        ctx.beginPath();
        ctx.moveTo(i * cellSize, 0);
        ctx.lineTo(i * cellSize, canvas.height);
        ctx.stroke();
        ctx.moveTo(0, i * cellSize);
        ctx.lineTo(canvas.width, i * cellSize);
        ctx.stroke();
    }
    ctx.fillStyle = 'red';
    ctx.fillRect(food.x * cellSize, food.y * cellSize, cellSize, cellSize);
    snake.forEach((seg, index) => {
        ctx.fillStyle = index === 0 ? '#00ff00' : '#00cc00';
        ctx.fillRect(seg.x * cellSize, seg.y * cellSize, cellSize - 1, cellSize - 1);
    });
}

function step() {
    if (!gameActive) return;
    direction = nextDirection;
    const head = snake[0];
    let newHead = {x: head.x, y: head.y};
    switch (direction) {
        case 'up': newHead.y--; break;
        case 'down': newHead.y++; break;
        case 'left': newHead.x--; break;
        case 'right': newHead.x++; break;
    }

    // Проверка границ с учётом wallMode
    if (wallMode === 'walls') {
        if (newHead.x < 0 || newHead.x >= gridSize || newHead.y < 0 || newHead.y >= gridSize) {
            gameOver();
            return;
        }
    } else { // без стен – телепортация
        if (newHead.x < 0) newHead.x = gridSize - 1;
        if (newHead.x >= gridSize) newHead.x = 0;
        if (newHead.y < 0) newHead.y = gridSize - 1;
        if (newHead.y >= gridSize) newHead.y = 0;
    }

    // Проверка столкновения с собой
    if (snake.some(seg => seg.x === newHead.x && seg.y === newHead.y)) {
        gameOver();
        return;
    }

    snake.unshift(newHead);
    if (newHead.x === food.x && newHead.y === food.y) {
        score++;
        scoreSpan.textContent = 'Счёт: ' + score;
        generateFood();
        if (speed > 80) speed = initialSpeed - (score * 2);
        clearInterval(gameInterval);
        gameInterval = setInterval(step, speed);
    } else {
        snake.pop();
    }
    draw();
}

function gameOver() {
    gameActive = false;
    clearInterval(gameInterval);
    gameInterval = null;
    alert(`Игра окончена! Ваш счёт: ${score}`);
}

function startGame() {
    if (gameInterval) clearInterval(gameInterval);
    initGame();
    gameActive = true;
    gameInterval = setInterval(step, speed);
}

function stopGame() {
    gameActive = false;
    if (gameInterval) {
        clearInterval(gameInterval);
        gameInterval = null;
    }
}

function changeDirection(dir) {
    if (!gameActive) return;
    const opposites = { up: 'down', down: 'up', left: 'right', right: 'left' };
    if (dir !== opposites[direction]) {
        nextDirection = dir;
    }
}

// Клавиши (ПК)
document.addEventListener('keydown', (e) => {
    if (!gameActive || modal.style.display !== 'flex') return;
    const keyMap = {
        ArrowUp: 'up', ArrowDown: 'down',
        ArrowLeft: 'left', ArrowRight: 'right',
        w: 'up', s: 'down', a: 'left', d: 'right'
    };
    const dir = keyMap[e.key];
    if (dir) {
        e.preventDefault();
        changeDirection(dir);
    }
});

// Экранные кнопки
document.querySelectorAll('.ctrl-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const dir = btn.getAttribute('data-dir');
        if (dir) changeDirection(dir);
    });
    btn.addEventListener('contextmenu', e => e.preventDefault());
});

// Свайпы на canvas
let touchStartX = 0, touchStartY = 0;
canvas.addEventListener('touchstart', (e) => {
    const touch = e.touches[0];
    touchStartX = touch.clientX;
    touchStartY = touch.clientY;
    e.preventDefault();
}, {passive: false});

canvas.addEventListener('touchend', (e) => {
    if (!gameActive || touchStartX === 0) return;
    const touch = e.changedTouches[0];
    const dx = touch.clientX - touchStartX;
    const dy = touch.clientY - touchStartY;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);
    if (Math.max(absDx, absDy) < 20) return;
    if (absDx > absDy) {
        changeDirection(dx > 0 ? 'right' : 'left');
    } else {
        changeDirection(dy > 0 ? 'down' : 'up');
    }
    touchStartX = 0;
    e.preventDefault();
}, {passive: false});

// Открытие/закрытие модалки
openBtn.addEventListener('click', () => {
    modal.style.display = 'flex';
    startGame();
});

closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
    stopGame();
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
        stopGame();
    }
});

restartBtn.addEventListener('click', startGame);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.style.display === 'flex') {
        modal.style.display = 'none';
        stopGame();
    }
});
