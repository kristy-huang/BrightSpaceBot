import React from 'react'
import {Link} from 'react-router-dom'
import {useAuth} from '../auth'

function LoggedInHome() {
    return (
        <div>
            <p>You are logged in</p>
        </div>
    )
}

function LoggedOutHome() {
    return (
        <>
        <h1>Welcome to BrightSpaceBot</h1>
        <br></br>
        <Link to="/register" className="btn btn-primary">Get Started</Link>
        </>
    )
}

function Home(props) {
    const [loggedIn] = useAuth()
    return (
        <div className="home container">
            {loggedIn?<LoggedInHome/>:<LoggedOutHome/>}
        </div>
    )
}

export default Home