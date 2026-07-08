import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatWindow from "./ChatWindow";
import ApplicantForm from "./ApplicantForm";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatWindow />} />
        <Route path="/user" element={<ApplicantForm />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
