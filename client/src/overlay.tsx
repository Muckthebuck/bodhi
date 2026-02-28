import { createRoot } from "react-dom/client";
import { OverlayApp } from "./components/OverlayApp";

createRoot(document.getElementById("overlay-root")!).render(<OverlayApp />);
