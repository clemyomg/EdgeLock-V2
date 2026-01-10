import type { NextConfig } from "next";

const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development", // Disable PWA in local development
});

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
};

// Export the config wrapped with PWA
export default withPWA(nextConfig);