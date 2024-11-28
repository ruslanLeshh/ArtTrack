import "../styles/basic.css"
import { useState, useEffect } from 'react';

export default function Sidebar() {

    const UserId = localStorage.getItem("userId");
    const [lastScan, setLastScan] = useState('');
    const [matches, setMatches] = useState([]);
    
    useEffect(() => {
        const storedScanTime = localStorage.getItem('lastScanTime');
        if (storedScanTime) {
            setLastScan(storedScanTime);
        } else {
            setLastScan("No scan history found");
        }
    }, []);

    const fetchMatches = async () => {
        try {
            const response = await fetch(`http://localhost:5000/matches/${UserId}`, {
                method: "GET"
            });
            if (response.ok) {
                const data = await response.json();
                console.log("MATCHES FOUND",data)

                setMatches(data.matches); 
            } else {
                console.error('Error fetching matches');
            }
        } catch (error) {
            console.error("Error fetching matches:", error);
        }
    };

    const handleScan = async (e) => {
        if (!UserId) {
            console.error("User ID not found");
            alert("Add images for scanning.");
            return;
        }
    
        try {
            const response = await fetch("http://localhost:8000/images/scan", {
                method: 'POST'
            });
    
            if (!response.ok) {
                throw new Error('Error uploading image');
            } else {
                const data = await response.json();
                alert("scan is completed!");
                const currentTime = new Date();
                const formattedTime = `${currentTime.getMonth() + 1}/${currentTime.getDate()}/${currentTime.getFullYear()}, ${currentTime.getHours()}:${currentTime.getMinutes()}:${currentTime.getSeconds()}`;
                localStorage.setItem('lastScanTime', formattedTime);

                setLastScan(formattedTime);
                fetchMatches();
            }

        } catch (error) {
            console.error("Error uploading file:", error);
            alert("Error uploading file.");
        }
    }

    
    useEffect(() => {
        if (!UserId) {
            console.error("User ID not found");
            return;
        }
        fetchMatches();
    }, []);


    return (
        <div className='sidebar-container'>
            <div className='hdr'>last scan: {lastScan}</div>
            <div className='menu'>
                <div style={{ height: "100%"}}>
                <p>
                <button className="scan-btn" onClick={handleScan}>Scan</button>
                matches:
                </p>
                    <div className="menu-container">
                        {matches && matches.length > 0 ? matches.map((match, index) => (
                            <div key={index}>
                            
                            <div style={{backgroundColor: "rgba(255, 0, 0, 0.4)"}}><p style={{ color: "rgba(255, 255, 255, 0.2 )", margin: "0 auto", width: "0%", background_color: "red"}}><strong>{index + 1}</strong></p></div>
                            <p>Matched Image: {match.matched_image_filename}</p><br/>
                            <p>Scraped Image Filename: {match.new_image_filename}</p><br/>
                            <p>Similarity: {match.similarity_score}</p><br/>
                            {match.image_url ? (
                                <p>Image URL: <a href={match.image_url} target="_blank" rel="noopener noreferrer">{match.image_url}</a></p>
                            ) : null}
                            <button className="button2" style={{ display: "flex"}} >Submit a takedown request</button><br/>
                            </div>
                        )) : "No matches found"}
                        <br/><br/>
                    </div>
                </div>
            </div>
        </div>
    );
}
