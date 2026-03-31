import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

import "bootstrap/dist/css/bootstrap.min.css";
import 'bootstrap/dist/js/bootstrap.bundle.min.js'; // 1) Bootstrap trước               // 1) Global của bạn
import "./styles/premium.css";                 // 2) Premium/Global của bạn
import "./styles/responsive.css";              // 3) Responsive
import "./styles/client.css";
import "./index.css";

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
