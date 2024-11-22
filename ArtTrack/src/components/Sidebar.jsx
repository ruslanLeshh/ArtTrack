import "../styles/basic.css"

export default function Sidebar() {
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