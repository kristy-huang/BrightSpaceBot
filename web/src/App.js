import logo from './logo.svg';
import './App.css';
import React, { useEffect, useState } from 'react';
import axios from 'axios'

function App() {
  const [getMessage, setGetMessage] = useState({})

  useEffect(()=>{
    axios.post('http://localhost:5000/register').then(response => {
      console.log("SUCCESS", response)
      setGetMessage(response)
    }).catch(error => {
      console.log(error)
    })

  }, [])
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>Welcome to BrightSpace Bot</p>
        <div>{getMessage.status === 200 ?
          <button>{getMessage.data.message}</button>
          :
          <h3>LOADING</h3>}</div>
      </header>
    </div>
  );
}

export default App;