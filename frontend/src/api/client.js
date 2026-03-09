// src/api/client.js
import axios from "axios";

const apiClient = axios.create({
  baseURL: "/",         // this makes /api/... work
  withCredentials: true, // this send session cookies with every request
});

// Defining how Django names CSRF cookie/header
apiClient.defaults.xsrfCookieName = "csrftoken";
apiClient.defaults.xsrfHeaderName = "X-CSRFToken";

export default apiClient;
