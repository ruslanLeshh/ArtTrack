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

    const handleScan = async (e) => {
        if (!UserId) {
            console.error("User ID not found");
            alert("Add images for scanning.");
            return;
        }
    
        try {
            const response = await fetch("http://localhost:8000/images/scan", {
                method: 'POST'
                // headers: { 'user-id': UserId },
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
            }

        } catch (error) {
            console.error("Error uploading file:", error);
            alert("Error uploading file.");
        }
    }


    useEffect(() => {
        if (!UserId) {
            console.error("User ID not found");
            alert("Please log in to view images");
            return;
        }
        // Fetch all images associated with the user
        const fetchMatches = async () => {
            try {
                const response = await fetch(`http://localhost:8000/images/matches`, {
                    method: "GET",
                    headers: { "user-id": UserId },
                });

                if (response.ok) {
                    const data = await response.json();
                    // alert('everything is fine!')
                    console.log("MATCHES FOUND",data)

                    setMatches(data.matches);  // Store the matches in state
                } else {
                    console.error('Error fetching matches');
                    alert('Error fetching matches');
                }
            } catch (error) {
                console.error("Error fetching matches:", error);
                alert('Error fetching matches');
            }
        };

        fetchMatches();
    }, []);


    return (
        <div className='sidebar-container'>
            <div className='hdr'>last scan: {lastScan}</div>
            <div className='menu'>
                <div>
                <p>
                <button className="scan-btn" onClick={handleScan}>Scan</button>
                matches:
                </p>
                <p style={{ wordWrap: "break-word", whiteSpace: "normal" }}>
                    {matches && matches.length > 0 ? matches.map((match, index) => (
                        <div key={index}>
                        <p>Similarity: {match.similarity_score}</p>
                        <p>Matched Image: {match.matched_image_filename}</p>
                        <p>Scraped Image Filename: {match.new_image_filename}</p>
                        <button className="button2" style={{ display: "flex"}} >Submit a takedown request</button>
                        </div>
                    )) : "No matches found"}
                    </p>
                </div>
                
            </div>
        </div>
    );
}