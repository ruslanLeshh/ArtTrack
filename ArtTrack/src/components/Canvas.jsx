import "../styles/basic.css"
import { useState, useEffect } from 'react';
 
export default function Canvas() {
    const [filenames, setFilenames] = useState([]); // Renamed to filenames
    const UserId = localStorage.getItem("userId");

    useEffect(() => {
        if (!UserId) {
            console.error("User ID not found");
            alert("Please log in to view images");
            return;
        }
        // Fetch all images associated with the user
        const fetchImages = async () => {
            try {
                const response = await fetch(`http://localhost:5000/images/${UserId}`, {
                    method: "GET",
                    headers: { "user-id": UserId },
                });

                if (response.ok) {
                    const filenames = await response.json(); // Assuming the server sends back only filenames

                    const updatedImages = filenames
                    .map(name => `http://localhost:5000/images/users-images/${name}`)
                    .reverse(); // Reverse to show the latest uploaded first
    
                    setFilenames(updatedImages);

                } else if (response.status === 404) {
                    console.error("No images found for this user.");
                    alert("No images available for your account.");
                } else {
                    console.error("Error fetching images");
                    alert("Error fetching images");
                }
            } catch (error) {
                console.error("Error:", error);
                alert("Server is not running");
            }
        };

        fetchImages();
    }, []);

    // Image uploading
    async function handleUpload(e) {
        if (!UserId) {
            console.error("User ID not found");
            alert("Please log in before uploading.");
            return;
        }

        const file = e.target.files[0];
        const formData = new FormData();
        formData.append("image", file);

        try {
            const response = await fetch("http://localhost:5000/images/users-images", {
                method: "POST",
                headers: { "user-id": UserId },
                body: formData,
            });

            if (response.ok) {
                const { filename } = await response.json(); // The server returns the filename
                const newFilename = `http://localhost:5000/images/users-images/${filename}`;
                setFilenames((prevFilenames) => [newFilename, ...prevFilenames]); // Add the new filename to the list
            } else {
                console.error("Error uploading image");
                alert("Error uploading image");
            }
        } catch (error) {
            console.error("Upload failed:", error);
            alert("Upload failed");
        }

        // try {
        //     const response = await fetch("http://localhost:8000/images/internet-images", {
        //         method: 'POST',
        //         headers: { 'user-id': UserId },
        //         body: formData, 
        //     });

        //     if (!response.ok) {
        //         throw new Error('Error uploading image');
        //     } else {
        //         alert("FastAPI works!");
        //     }

        //     const data = await response.json();
        //     // alert(data.message);
        // } catch (error) {
        //     console.error("Error uploading file:", error);
        //     alert("Error uploading file.");
        // }
    }

    

    return (
        <div className='canvas-container'>
            <div className='hdr'>project name</div>
            <div className='canvas'>
                <button className="upload" onClick={() => document.getElementById('getFile').click()}>
                    Upload
                </button>
                <input 
                    type='file' 
                    id="getFile" 
                    style={{ display: 'none' }} 
                    onChange={handleUpload}
                />
                {filenames.map((image, index) => (
                    <img 
                    className="img" 
                    key={index} 
                    src={image} 
                    alt={`Uploaded ${index}`} 
                    />
                ))}
                {/* <img className="img" src={`http://localhost:5000/images/6/image-1731807869025-320950992`} alt="hahahhaha" /> */}
            </div>
        </div>
    );
}
