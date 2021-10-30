import './App.css';
import Home from './components/Home';
import Login from './components/Login';
import Navbar from './components/Navbar';
import Register from './components/Register';
import UpdateProfile from './components/UpdateProfile'
import GetBot from './components/GetBot';
import './styles/main.css'
import {
    BrowserRouter as Router,
    Switch,
    Route
} from 'react-router-dom'

function App() {
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
            <Route path="/updateProfile">
                <UpdateProfile/>
            </Route>
            <Route path="/getBot">
                <GetBot/>
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