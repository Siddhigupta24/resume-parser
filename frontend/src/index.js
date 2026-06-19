// index.js

import React from 'react';                    // Line 1
import ReactDOM from 'react-dom/client';      // Line 2
import './index.css';                         // Line 3
import App from './App';                      // Line 4

const root = ReactDOM.createRoot(            // Line 6
  document.getElementById('root')           // Line 7
);

root.render(                                 // Line 10
  <React.StrictMode>                         
    <App />                                  
  </React.StrictMode>                        
);