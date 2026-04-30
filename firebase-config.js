// firebase-config.js
const firebaseConfig = {
  apiKey: "AIzaSyDN4GiOCtmtEiVGt8rwW2kjPqrFwE_vUzE",
  authDomain: "metatradebot-v1.firebaseapp.com",
  projectId: "metatradebot-v1",
  storageBucket: "metatradebot-v1.firebasestorage.app",
  messagingSenderId: "787315443175",
  appId: "1:787315443175:web:1d1477a76fd5fe87806942",
  measurementId: "G-QER5HLXXS5"
};

// Инициализация Firebase
firebase.initializeApp(firebaseConfig);

// Глобальные объекты сервисов
const db = firebase.firestore();
const auth = firebase.auth();