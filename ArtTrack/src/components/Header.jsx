import "../styles/basic.css"
import {Link} from "react-router-dom";

export default function Header() {
    return (
        <div className='header'>
            <Link to={'/login'}><div className='account pixel-corners'/></Link>
            <Link to={'/'} className="link">ArtTrack</Link>
        </div>
    );
}