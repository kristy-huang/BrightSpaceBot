import React, {useState} from 'react'
import {Link} from 'react-router-dom'
import {useAuth} from '../auth'
import {useForm} from 'react-hook-form'
import {Form, Button} from 'react-bootstrap'

function UpdateProfile(props) {
    const {register, watch, handleSubmit, reset, formState:{errors}} = useForm();
    const updateProfile = (data)=>{
        console.log(data)
        const requestOptions = {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body:
              JSON.stringify({

              })
        };

        fetch('http://localhost:5000/updateProfile', requestOptions)
            .then(res=>res.json())
            .then(data=>{
                //console.log(data)
            })
            .catch(err=>console.log(err))
        reset()
    }

    return (
        <div className="container">
            <div className="form">
                <h1>Update Profile</h1>
                <br></br>
                <form>
                    <Form.Group>
                        <Form.Label>Major</Form.Label>
                        <Form.Control
                            type="major"
                            placeholder="Major"/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Storage Location</Form.Label>
                        <Form.Select>
                            <option value="-1">--</option>
                            <option value="Google Drive">Google Drive</option>
                            <option value="Local Machine">Local Machine</option>
                        </Form.Select>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Notification Frequency</Form.Label>
                        <Form.Select>
                            <option value="-1">--</option>
                            <option value="1">Every 4 hours</option>
                            <option value="2">Every 6 hours</option>
                            <option value="3">Once a day</option>
                            <option value="4">Once a week</option>
                            <option value="5">Custom</option>
                        </Form.Select>
                    </Form.Group>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={handleSubmit(updateProfile)}>Update</Button>
                    </Form.Group>
                </form>
            </div>
        </div>
    )
}

export default UpdateProfile