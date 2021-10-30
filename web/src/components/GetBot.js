import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'
import {Link} from 'react-router-dom'
import {useForm} from 'react-hook-form'
import {useAuth} from '../auth'

function GetBot(props) {
    return (
        <div className="container">
            <h1>Instructions</h1>
            <p>1. Create a server on Discord</p>
            <p>2. Click the link below to get bot and select the server you want to add your bot to</p>
            <a href="https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534723950656&scope=bot" target="_blank">Get Bot</a>
        </div>
    )
}

export default GetBot