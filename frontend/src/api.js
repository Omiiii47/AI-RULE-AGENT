import axios from "axios";

const API_URL = "http://localhost:8000";

export async function sendMessage(message) {
  const res = await axios.post(`${API_URL}/chat`, { message });
  return res.data.response;
}
