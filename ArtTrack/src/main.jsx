// Import the StrictMode component from the React library to help identify potential problems in the application.
import { StrictMode } from 'react';

// Import the createRoot function from the React DOM library to create the root node for the React application.
import { createRoot } from 'react-dom/client';

// Import the main application component App from the App.jsx file located in the components folder.
import App from './components/App.jsx';

// Create the root node of the React application and mount it to the DOM element with the ID 'root'.
createRoot(document.getElementById('root')).render(
  // Use StrictMode to enable additional checks and warnings.
  <StrictMode>
    {/* Render the main App component */}
    <App />
  </StrictMode>
);
