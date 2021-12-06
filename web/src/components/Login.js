import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'
import {Link} from 'react-router-dom'
import {useForm} from 'react-hook-form'
import {login} from '../auth'
import {useHistory} from 'react-router-dom'

function Login(props) {
    const {register, watch, handleSubmit, reset, formState:{errors}} = useForm();
    const history = useHistory()

    const loginUser = (data)=>{
        console.log(data)
        sessionStorage.setItem('username', data.username);
        const requestOptions = {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body:
              JSON.stringify({
                "username": data.username,
                "password": data.password
              })
        };

        fetch('/login', requestOptions)
            .then(res=>res.json())
            .then(data=>{
                //console.log(data)
                if (data.status === 200) {
                    login(data.access_token)
                    history.push('/')
                }
                else if (data.message === 'User not found') {
                    history.push('register')
                    alert("User not found. Please register for an account.")
                }
                else if (data.message === 'Wrong password') {
                    alert("Wrong password. Please try again.")
                }
                else {
                    alert(data.message)
                }
            })
            .catch(err=>console.log(err))
        reset()
    }

    return (
        <div className="container">
            <div className="form">
                <h1>Login Page</h1>
                <br></br>
                <form>
                    <Form.Group>
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Username"
                            {...register('username', {required: true, maxLength: 50})}/>
                            {errors.username && <span style={{color:"red"}}>Username is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="Password"
                            {...register('password', {required: true, minLength: 6})}/>
                            {errors.password && <span style={{color:"red"}}>Password is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={handleSubmit(loginUser)}>Login</Button>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <small>Don't have an account? <Link to="/register">Create one</Link></small>
                    </Form.Group>
                </form>
            </div>
        </div>
    )
}

export default Login