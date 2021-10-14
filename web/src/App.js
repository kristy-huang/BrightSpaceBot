import './App.css';
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