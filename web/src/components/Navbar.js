import React from 'react'
import {Link} from 'react-router-dom'
import {useAuth, logout} from '../auth'

function LoggedInLinks() {
    return (
        <>
            <li className="nav-item">
                <Link className="nav-link active" aria-current="page" to="/">Home</Link>
            </li>
            <li className="nav-item">
                <Link className="nav-link active" aria-current="page" to="/updateProfile">Update Profile</Link>
            </li>
            <li className="nav-item">
                <Link className="nav-link" to="/getBot">Get Bot</Link>
            </li>
            <li className="nav-item">
                <a className="nav-link" onClick={()=>logout()}>Log Out</a>
            </li>
        </>
    )
}

function LoggedOutLinks() {
    return (
        <>
            <li className="nav-item">
                <Link className="nav-link active" aria-current="page" to="/">Home</Link>
            </li>
            <li className="nav-item">
                <Link className="nav-link" to="/register">Sign Up</Link>
            </li>
            <li className="nav-item">
                <Link className="nav-link" to="/login">Login</Link>
            </li>
        </>
    )
}

function Navbar() {
    const [loggedIn] = useAuth()

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <div className="container-fluid">
                <Link className="navbar-brand" to="/">BrightSpaceBot</Link>
                <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span className="navbar-toggler-icon"></span>
                </button>
                <div className="collapse navbar-collapse" id="navbarNav">
                    <ul className="navbar-nav">
                        {loggedIn?<LoggedInLinks/>:<LoggedOutLinks/>}
                    </ul>
                </div>
            </div>
        </nav>
    )
}

export default Navbar