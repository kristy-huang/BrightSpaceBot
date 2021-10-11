import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'

function Register(props) {
    const [firstName, setFirstName] = useState('')
    const [lastName, setLastName] = useState('')
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')

    const submitForm = ()=>{
        console.log("form submitted");
        console.log(firstName);
        console.log(lastName);

        setFirstName('');
        setLastName('');
        setUsername('');
        setPassword('');
        setConfirmPassword('');
    }

    return (
        <div className="container">
            <div className="form">
                <h1>Sign Up Page</h1>
                <br></br>
                <form>
                    <Form.Group>
                        <Form.Label>First Name</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="John"
                            value={firstName}
                            name="firstName"
                            onChange={(e)=>{setFirstName(e.target.value)}}/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Last Name</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Doe"
                            value={lastName}
                            name="lastName"
                            onChange={(e)=>{setLastName(e.target.value)}}/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="JDoe123"
                            value={username}
                            name="username"
                            onChange={(e)=>{setUsername(e.target.value)}}/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="123456"
                            value={password}
                            name="password"
                            onChange={(e)=>{setPassword(e.target.value)}}/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Confirm Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="123456"
                            value={confirmPassword}
                            name="confirmPassword"
                            onChange={(e)=>{setConfirmPassword(e.target.value)}}/>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={submitForm}>Sign up</Button>
                    </Form.Group>
                </form>
            </div>
        </div>
    )
}

export default Register