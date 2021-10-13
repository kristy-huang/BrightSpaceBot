import React from 'react'
import {Link} from 'react-router-dom'

function Home(props) {
    return (
        <div className="home container">
            <h1>Welcome to BrightSpaceBot</h1>
            <Link to="/register" className="btn btn-primary">Get Started</Link>
        </div>
    )
}

export default Home