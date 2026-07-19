"use client";

import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          backgroundColor: "#111315",
          color: "#e8d5a3",
          fontFamily: "Inter, sans-serif",
          padding: "2rem",
          textAlign: "center",
        }}>
          <h1 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>Something went wrong</h1>
          <p style={{ color: "#888", marginBottom: "1.5rem", maxWidth: "500px" }}>
            An unexpected error occurred. Please refresh the page or try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "0.5rem 1.5rem",
              backgroundColor: "#c9a962",
              color: "#111315",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.9rem",
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
