import './App.css';
import React, { useEffect, useState } from 'react';
import axios from 'axios'
import UserLogin from './components/UserLogin';

function App() {
  const [user, setUser] = useState([]);
  useEffect(()=> {
    fetch('http://localhost:5000/getUsers', {
        'method':'GET',
        headers: {
            'Content-Type':'applications/json'
        }
    })
    .then(res => res.json())
    .then(res => setUser(res))
    .catch(err => console.log(err))
  })
  return (
    <div className="App">
        <h1>Welcome to BrightSpaceBot</h1>
        <UserLogin user = {user}/>
    </div>
  );
}

export default App;