import { StrictMode } from 'react'
import { polyfillCountryFlagEmojis } from 'country-flag-emoji-polyfill'
import flagFontUrl from 'country-flag-emoji-polyfill/dist/TwemojiCountryFlags.woff2?url'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Windows does not draw flag emojis; this loads a small flag-only font there (served by the app).
polyfillCountryFlagEmojis('Twemoji Country Flags', flagFontUrl)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
