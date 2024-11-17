import "../styles/basic.css"
import { useState, useEffect } from 'react';

export default function Canvas() {

    const [ImagePaths, setImagePaths] = useState([]);
    const UserId = localStorage.getItem("userId");

    useEffect(() => {
        if (!UserId) {
            console.error('User ID not found');
            alert('Please log in to view images');
            return;
        }
        // Fetch all images associated with the user
        const fetchImages = async () => {
            try {
                const response = await fetch(`http://localhost:5000/images/${UserId}`, {
                    method: 'GET',
                    headers: { 'user-id': UserId },
                });

                if (response.ok) {
                    const images = await response.json();
                    const updatedImages = images.map(imagePath => 
                        `http://localhost:5000/images/${imagePath.replace(/\\/g, '/')}` // If necessary, replace backslashes with forward slashes
                    );
                    
                    setImagePaths(updatedImages.reverse());
                } else if (response.status === 404) {
                    console.error('No images found for this user.');
                    alert('No images available for your account.');
                } else {
                    console.error('Error fetching images');
                    alert('Error fetching images');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error occurred while fetching images');
            }
        };

        fetchImages();
    }, [`UserId`]);


    // image uploading
    async function handleUpload(e) {
        if (!UserId) {
            console.error('User ID not found');
            alert('Please log in before uploading.');
            return;
        }
    
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('image', file);
    
        try {
            const response = await fetch('http://localhost:5000/images/upload', {
                method: 'POST',
                headers: { 'user-id': UserId },
                body: formData,
            });
    
            if (response.ok) {
                const { imagePath } = await response.json();

                // Fix the path: replace backslashes with forward slashes
                const correctedImagePath = imagePath.replace(/\\/g, '/');
    
                // Construct the full URL for the image
                const fullImagePath = `http://localhost:5000/images/${correctedImagePath}`;
                // alert(fullImagePath)

                setImagePaths(prevPaths => [fullImagePath, ...prevPaths]);
            } else {
                console.error('Error uploading image');
                alert('Error uploading image');
            }
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload failed');
        }
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
                {ImagePaths.map((image, index) => (
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