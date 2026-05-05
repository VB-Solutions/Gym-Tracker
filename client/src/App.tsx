import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { Register } from "./views/Register.tsx"
import { Login } from "./views/Login.tsx"
import { Error } from "./views/Error.tsx"
import { Home } from "./views/Home.tsx"


function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<Error />}/>
        <Route path="/" element={<Navigate to="/login" replace />}/>
        <Route path="/home" element={<Home />}/>
        <Route path="/login" element={<Login />}/>
        <Route path="/register" element={<Register />}/>
      </Routes>
    </BrowserRouter>
  )
}

export default App
