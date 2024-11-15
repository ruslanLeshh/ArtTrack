import "../styles/basic.css"

export default function Login() {
    return (
        <div className='login-container'>
            <input className="input" placeholder="username"/>
            <input className="input" placeholder="password"/>
            <button className="button">Login</button>
        </div>
    );
}