import React from 'react'
import ReactDOM from 'react-dom/client'
import '@telegram-apps/telegram-ui/dist/styles.css'
import { App } from './App'

// Initialize Telegram WebApp SDK
const tg = (window as unknown as { Telegram?: { WebApp?: { ready: () => void; expand: () => void } } }).Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
