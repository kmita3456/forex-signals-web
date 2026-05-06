// app.js
const firebaseConfig = {
    apiKey: "ВАШ_API_KEY",
    authDomain: "ВАШ_PROJECT.firebaseapp.com",
    projectId: "ВАШ_PROJECT_ID",
    storageBucket: "ВАШ_PROJECT.appspot.com",
    messagingSenderId: "ВАШ_SENDER_ID",
    appId: "ВАШ_APP_ID"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const logoutBtn = document.getElementById('logout-btn');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const authContainer = document.getElementById('auth-container');
const dashboard = document.getElementById('dashboard');
const signalsList = document.getElementById('signals-list');
const scanStatus = document.getElementById('scan-status');

// Аутентификация
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

logoutBtn.addEventListener('click', () => {
    auth.signOut();
});

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
