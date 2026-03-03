import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ContractGHOST",
  description: "AI-native Bid + Delivery OS for Data Centre Refurbs & New Builds",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-white antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
