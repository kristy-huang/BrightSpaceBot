import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'
import {Link} from 'react-router-dom'
import {useForm} from 'react-hook-form'
import {useAuth, logout} from '../auth'

function LoggedIn() {
    return (
        <>
            <h1>Instructions</h1>
            <p>1. Create a server on Discord</p>
            <p>2. Click the link below to get bot and select the server you want to add your bot to</p>
            <a href="https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534992387152&scope=bot" target="_blank">Get Bot</a>
        </>
    )
}

function LoggedOut() {
    return (
        <>
            <p>Please login to see this page</p>
        </>
    )
}

function GetBot(props) {
    const [loggedIn] = useAuth()
    return (
        <div className="container">
            {loggedIn?<LoggedIn/>:<LoggedOut/>}
        </div>
    )
}

export default GetBot