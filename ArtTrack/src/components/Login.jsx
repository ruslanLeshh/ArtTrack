import "../styles/basic.css"
import { useState } from 'react';
import { useNavigate } from "react-router-dom";
 
export default function Login() {
    const [formData, setFormData] = useState({ username: '', password: '' });
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault();
        const response = await fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('userId', data.userId); // Save userId in localStorage
            navigate('/'); 
        } else {
            alert(data.message);
        }
    };

    return (
        <div className='login-container'>
            <input className="input" placeholder="username" onChange={e => setFormData({...formData, username: e.target.value})} />
            <input className="input" placeholder="password"onChange={e => setFormData({...formData, password: e.target.value})} />
            <button type="submit" className="button" onClick={handleSubmit}>Login</button>
        </div>
    );
}
