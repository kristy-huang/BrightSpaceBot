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
                        "firstName": data.firstName,
                        "lastName": data.lastName,
                        "username": data.username,
                        "password": data.password
                    })

            };
            console.log(requestOptions)
            fetch('http://localhost:5000/registerUser', requestOptions)
            .then(res=>{res.json()})
            .then(data=>console.log(data))
            .catch(err=>console.log(err))

            reset();
        }
        else {
            alert("Passwords do not match");
        }

    }

    console.log(watch("username"));

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
                            {...register("firstName", {required:true, maxLength:50})}/>
                        {errors.firstName && <span style={{color:"red"}}>First name is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Last Name</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="Doe"
                            {...register("lastName", {required:true, maxLength:50})}/>
                            {errors.lastName && <span style={{color:"red"}}>Last name is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Username</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="JDoe123"
                            {...register("username", {required:true, maxLength:50})}/>
                            {errors.username && <span style={{color:"red"}}>Username is required</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="123456"
                            {...register("password", {required:true,minLength:6})}/>
                            {errors.password && <span style={{color:"red"}}>Password is required</span>}
                            <br></br>
                            {errors.password?.type==="minLength"&&<span style={{color:"red"}}>Passwords should have at least 8 characters</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Form.Label>Confirm Password</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="123456"
                            {...register("confirmPassword", {required:true,minLength:6})}/>
                            {errors.confirmPassword && <span style={{color:"red"}}>Confirm password is required</span>}
                            <br></br>
                            {errors.confirmPassword?.type==="minLength"&&<span style={{color:"red"}}>Passwords should have at least 8 characters</span>}
                    </Form.Group>
                    <br></br>
                    <Form.Group>
                        <Button as="sub" variant="primary" onClick={handleSubmit(submitForm)}>Sign up</Button>
                    </Form.Group>
                </form>
            </div>
        </div>
    )
}

export default Register