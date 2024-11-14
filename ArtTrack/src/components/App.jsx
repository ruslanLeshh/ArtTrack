import "../styles/basic.css"
import Header from "./Header.jsx";
import Canvas from "./Canvas.jsx";
import Sidebar from "./Sidebar.jsx";

export default function App() {
    return (
        <>
            <Header/>
            <div className="main-container">
                <Canvas/>
                <Sidebar/>
            </div>
        </>
    );
}