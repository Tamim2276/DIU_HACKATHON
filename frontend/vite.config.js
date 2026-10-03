import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API only accepts browser calls from the addresses in its ALLOWED_ORIGINS setting,
// which is http://localhost:5173 on a developer's machine. So the port must not move:
// with strictPort, a busy port is an error instead of a silent switch to 5174.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  preview: { port: 5173, strictPort: true },
});
