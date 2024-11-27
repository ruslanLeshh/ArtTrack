import "../styles/basic.css";
/* Importing the CSS stylesheet for global styling */

import Header from "./Header.jsx";
import Canvas from "./Canvas.jsx";
import Sidebar from "./Sidebar.jsx";
import Login from "./Login.jsx";
/* Importing the required React components */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
/* Importing routing components from React Router for navigation */

export default function App() {
    return (
        <>
            {/* Using React Router for handling different routes in the app */}
            <BrowserRouter 
                future={{ 
                    v7_startTransition: true, 
                    v7_relativeSplatPath: true 
                }}
                /* `future` config options (for newer React Router features) */
            >
                <Header/>
                {/* Header component visible across all routes */}
                
                <Routes>
                    <Route 
                        path="/" 
                        element={
                            <div className="main-container">
                                <Canvas/>
                                <Sidebar/>
                            </div> 
                        } 
                    />
                    {/* Defines the root route (`/`) with a `Canvas` and `Sidebar` in a `main-container` */}

                    <Route 
                        path="/login" 
                        element={
                            <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
                                <Login/>
                            </div>
                        } 
                    />
                    {/* Defines the `/login` route displaying the `Login` component centered in the viewport */}
                </Routes>
            </BrowserRouter>
        </>
    );
}
/* The App component renders the routing logic, controlling which component appears based on the URL path */
