import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { initPostHog } from './lib/posthog'
import { initSentry } from './lib/sentry'
import { registerServiceWorker } from './lib/pwa'
import './index.css'

initSentry()
initPostHog()
registerServiceWorker()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
