import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

// 1. Configure PWA Metadata
export const metadata: Metadata = {
  title: "EdgeLock Pro",
  description: "Advanced Sports Value Finder",
  manifest: "/manifest.json", // Points to your file
  icons: {
    icon: "/icons/icon-192x192.png",
    apple: "/icons/icon-512x512.png", // For iPhones
  },
};

// 2. Configure App Viewport (Disables zooming for app-feel)
export const viewport: Viewport = {
  themeColor: "#09090b", // Matches your dark background
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false, // Prevents user from pinching to zoom (app-like feel)
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  );
}