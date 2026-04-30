// app.js

// ------------- Переключение форм входа/регистрации -------------
document.getElementById('show-register').addEventListener('click', () => {
  document.getElementById('login-container').style.display = 'none';
  document.getElementById('register-container').style.display = 'block';
});
document.getElementById('show-login').addEventListener('click', () => {
  document.getElementById('register-container').style.display = 'none';
  document.getElementById('login-container').style.display = 'block';
});

// ------------- Логин -------------
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  try {
    await auth.signInWithEmailAndPassword(email, password);
    document.getElementById('login-error').textContent = '';
  } catch (err) {
    document.getElementById('login-error').textContent = err.message;
  }
});

// ------------- Регистрация -------------
document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  try {
    await auth.createUserWithEmailAndPassword(email, password);
    document.getElementById('register-error').textContent = '';
  } catch (err) {
    document.getElementById('register-error').textContent = err.message;
  }
});

// ------------- Выход -------------
document.getElementById('logout-btn').addEventListener('click', () => {
  auth.signOut();
});

// ------------- Отслеживание состояния аутентификации -------------
auth.onAuthStateChanged(user => {
  if (user) {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('register-container').style.display = 'none';
    document.getElementById('signals-container').style.display = 'block';
    loadSignals();
  } else {
    document.getElementById('login-container').style.display = 'block';
    document.getElementById('register-container').style.display = 'none';
    document.getElementById('signals-container').style.display = 'none';
  }
});

// ------------- Загрузка сигналов в реальном времени -------------
function loadSignals() {
  const container = document.getElementById('signals-list');

  // Подписка на изменения в коллекции 'signals'
  db.collection('signals')
    .orderBy('timestamp', 'desc')
    .limit(50)
    .onSnapshot(snapshot => {
      container.innerHTML = ''; // очищаем предыдущие
      snapshot.forEach(doc => {
        const s = doc.data();
        const card = document.createElement('div');
        card.className = 'signal-card';

        // Направление и иконка
        const directionIcon = s.direction === 'UP' ? '📈 BUY' : '📉 SELL';
        const arrow = s.direction === 'UP' ? '▲' : '▼';

        // Форматирование времени
        const ts = s.timestamp ? new Date(s.timestamp).toLocaleString() : '—';

        card.innerHTML = `
          <div class="signal-header">
            <span>${s.symbol} · ${s.timeframe}</span>
            <span class="direction ${s.direction === 'UP' ? 'up' : 'down'}">${arrow} ${directionIcon}</span>
          </div>
          <div class="signal-body">
            <p><strong>Уверенность:</strong> ${s.confidence}%</p>
            <p><strong>Удержание:</strong> ~${s.hold_time_minutes} мин</p>
            <p><strong>Цена входа:</strong> ${s.entry_price} | <strong>ATR:</strong> ${s.atr_value}</p>
            <p class="explanation">${s.explanation}</p>
            <small class="timestamp">${ts}</small>
          </div>
        `;
        container.appendChild(card);
      });

      // Если сигналов нет — подсказка
      if (snapshot.empty) {
        container.innerHTML = '<p>Нет активных сигналов.</p>';
      }
    }, error => {
      console.error('Ошибка получения сигналов: ', error);
      container.innerHTML = '<p style="color:red;">Ошибка загрузки данных.</p>';
    });
}