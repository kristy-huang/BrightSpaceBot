import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'
import {useForm} from 'react-hook-form'

function Register(props) {
    const {register, watch, handleSubmit, reset, formState:{errors}} = useForm();

    const submitForm = (data)=>{
        console.log(data);
        if (data.password === data.confirmPassword) {
            const requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body:
                    JSON.stringify({
                        "username": data.username,
                        "firstName": data.firstName,
                        "lastName": data.lastName,
                        "password": data.password,
                        "major": data.major,
                        "storageLocation": data.storageLocation,
                        "notificationFrequency": data.notificationFrequency
                    })
            };
            console.log(requestOptions)
            fetch('http://localhost:5000/registerUser', requestOptions)
            .then(res=>res.json())
            .then(data=>alert(data.message))
            .catch(err=>console.log(err))

            reset();
        }
        else {
            alert("Passwords do not match");
        }
    }

    //console.log(watch("username"));

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
                            placeholder="First Name"
                            {...register("firstName", {required:true, maxLength:50})}/>
                        {errors.firstName && <span style={{color:"red"}}>First name is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Last Name</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Last Name"
                            {...register("lastName", {required:true, maxLength:50})}/>
                            {errors.lastName && <span style={{color:"red"}}>Last name is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Major</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Major"
                            {...register("major", {required:true, maxLength:50})}/>
                            {errors.major && <span style={{color:"red"}}>Major is required.</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Username"
                            {...register("username", {required:true, maxLength:50})}/>
                            {errors.username && <span style={{color:"red"}}>Username is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="Password"
                            {...register("password", {required:true, minLength:6})}/>
                            {errors.password && <span style={{color:"red"}}>Password is required.</span>}
                            {errors.password?.type==="minLength" && <span style={{color:"red"}}> Passwords should have at least 6 characters</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Confirm Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="Confirm Password"
                            {...register("confirmPassword", {required:true, minLength:6})}/>
                            {errors.confirmPassword && <span style={{color:"red"}}>Confirm password is required.</span>}
                            {errors.confirmPassword?.type==="minLength"&&<span style={{color:"red"}}> Passwords should have at least 6 characters</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Choose a Storage Location</Form.Label>
                        <Form.Select {...register("storageLocation", {required:true})}>
                            <option value="Google Drive">Google Drive</option>
                            <option value="Local Machine">Local Machine</option>
                        </Form.Select>
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Configure Your Notification Frequency</Form.Label>
                        <Form.Select {...register("notificationFrequency", {required:true})}>
                            <option value="1">Every 4 hours</option>
                            <option value="2">Every 6 hours</option>
                            <option value="3">Once a day</option>
                            <option value="4">Once a week</option>
                            <option value="5">Custom</option>
                        </Form.Select>
                    </Form.Group>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={handleSubmit(submitForm)}>Sign up</Button>
                    </Form.Group>
                </form>
            </div>
        </div>
    )
}

export default Register