import React from "react";
import { createRoot } from "react-dom/client";

function App() {
  return <main><h1>AZLAN</h1><p>Web Application Security Auditing Platform</p></main>;
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode><App /></React.StrictMode>
);
