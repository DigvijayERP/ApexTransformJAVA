import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { RunProvider } from "./RunContext";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RunProvider>
      <App />
    </RunProvider>
  </StrictMode>,
);
