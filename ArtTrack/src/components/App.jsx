import "../styles/basic.css"
import Header from "./Header.jsx";
import Canvas from "./Canvas.jsx";
import Sidebar from "./Sidebar.jsx";
import Login from "./Login.jsx";
import {BrowserRouter, Routes, Route} from 'react-router-dom'

export default function App() {
    return (
        <>
            <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true}}>
                <Header/>
                <Routes>
                    <Route path="/" element={
                    <div className="main-container">
                        <Canvas/>
                        <Sidebar/>
                    </div> } />
                    <Route path="/login" element={<div style={{ display: "flex", justifyContent: "center", alignItems: "center"}}>
        <Login/>
    </div>
} />
                </Routes>
            </BrowserRouter>
        </>
    );
}