import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";

import { App } from "./App";
import { AuthProvider } from "./auth/AuthContext";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000, // 30s freshness prevents WAN request storms between Oracle Cloud and Neon Tech
      gcTime: 300_000, // 5 min garbage collection
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </HashRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
