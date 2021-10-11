import './App.css';
import React, { useEffect, useState } from 'react';
import axios from 'axios'
import Home from './components/Home';
import Login from './components/Login';
import Navbar from './components/Navbar';
import Register from './components/Register';
import './styles/main.css'
import {
    BrowserRouter as Router,
    Switch,
    Route
} from 'react-router-dom'

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
    <Router>
    <div className="App">
        <Navbar/>
        <Switch>
            <Route path="/login">
                <Login/>
            </Route>
            <Route path="/register">
                <Register/>
            </Route>
            <Route path="/">
                <Home/>
            </Route>
        </Switch>
    </div>
    </Router>
  );
}

export default App;