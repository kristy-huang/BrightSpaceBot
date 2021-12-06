import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'
import {Link} from 'react-router-dom'
import {useForm} from 'react-hook-form'
import {useAuth, logout} from '../auth'

function LoggedIn() {
    const {register, watch, handleSubmit, reset, formState:{errors}} = useForm();
    const submitForm = (data)=>{
        const username = sessionStorage.getItem('username');
        console.log(username)
        console.log(data)
        let major
        if (data.major === "") {
            major = '-1';
        }
        else {
            major = data.major
        }
        const requestOptions = {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body:
              JSON.stringify({
                "username": username,
                "major": major,
                "storageLocation": data.storageLocation,
                "notificationFrequency": data.notificationFrequency
              })
        };

        fetch('/updateProfile', requestOptions)
            .then(res=>res.json())
            .then(data=>{
                alert(data.message)
            })
            .catch(err=>console.log(err))
        reset()
    }
    return (
        <>
            <div className="form">
                <h1>Update Profile</h1>
                <br></br>
                <form>
                    <Form.Group>
                        <Form.Label>Major</Form.Label>
                        <Form.Control
                            type="major"
                            placeholder="Major"
                            {...register('major')}/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Storage Location</Form.Label>
                        <Form.Select {...register('storageLocation')}>
                            <option value="-1">--</option>
                            <option value="Google Drive">Google Drive</option>
                            <option value="Local Machine">Local Machine</option>
                        </Form.Select>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Notification Frequency</Form.Label>
                        <Form.Select {...register('notificationFrequency')}>
                            <option value="-1">--</option>
                            <option value="1">Every 4 hours</option>
                            <option value="2">Every 6 hours</option>
                            <option value="3">Once a day</option>
                            <option value="4">Once a week</option>
                            <option value="5">Custom</option>
                        </Form.Select>
                    </Form.Group>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={handleSubmit(submitForm)}>Update</Button>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Button as="sub" variant="primary"><Link className="nav-link active" aria-current="page" to="/">Cancel</Link></Button>
                    </Form.Group>
                </form>
            </div>
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

function UpdateProfile(props) {
    const [loggedIn] = useAuth()
    return (
        <div className="container">
            {loggedIn?<LoggedIn/>:<LoggedOut/>}
        </div>
    )
}

export default UpdateProfile