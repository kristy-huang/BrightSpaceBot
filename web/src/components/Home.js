import React from 'react'
import {Link} from 'react-router-dom'
import {useAuth} from '../auth'
import image from '../Brightspacebot.png';

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
        <br></br>
        <p>Many college students utilize the online platform, BrightSpace, for accessing class content and managing assignments. Downloading lectures, documents, and checking due dates are frequently executed tasks that students spend too much time doing. For example, currently students must manually navigate to each class page and filter through all folders set up by their professor in order to download the appropriate resources to complete assignments. The BrightspaceBot aims to automate these redundant tasks, so that students are well prepared for their classes.</p>
        <br></br>
        <br></br>
        <Link to="/register" className="btn btn-primary">Get Started</Link>
        </>
    )
}

function Home(props) {
    const [loggedIn] = useAuth()
    return (
        <div className="home container">
            <img src={image} height={200} width={480} />
            <br></br>
            <br></br>
            {loggedIn?<LoggedInHome/>:<LoggedOutHome/>}
        </div>
    )
}

export default Home