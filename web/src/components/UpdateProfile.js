import React from 'react'
import {Link} from 'react-router-dom'
import {useAuth} from '../auth'

function LoggedIn() {
    return (
        <div>
            <div className="form">
                <h1>Update Profile</h1>
                <br></br>
                <form>
                    <Form.Group>
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Username"
                          
                            {errors.username && <span style={{color:"red"}}>Username is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="Password"

                            {errors.password && <span style={{color:"red"}}>Password is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="major"
                            placeholder="major"

                            {errors.password && <span style={{color:"red"}}>Password is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={handleSubmit(updateProfile)}>Update</Button>
                    </Form.Group>
                </form>
            </div>
        </div>
    )
}

function LoggedOut() {
    return (
        <>
        </>
    )
}

function UpdateProfile(props) {
    const [loggedIn] = useAuth()

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
            {loggedIn?<LoggedIn/>:<LoggedOut/>}
        </div>
    )
}

export default Home