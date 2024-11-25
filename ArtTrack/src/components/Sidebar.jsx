import "../styles/basic.css"

export default function Sidebar() {

    const UserId = localStorage.getItem("userId");

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
                alert("no matches!");
            }

        } catch (error) {
            console.error("Error uploading file:", error);
            alert("Error uploading file.");
        }
    }


    return (
        <div className='sidebar-container'>
            <div className='hdr'>last scan:</div>
            <div className='menu'>
                <div><p>matches:</p>
                    <p style={{ wordWrap: "break-word", whiteSpace: "normal"}}>(1) Unauthorized use found on [https://www.artstation.com/romain_jouandeau].</p>
                    <p style={{ marginTop: "1em"}}>Recommended action:</p>
                </div>
                <button className="button2" style={{ display: "flex"}} >Submit a takedown request</button>
            </div>
        </div>
    );
}