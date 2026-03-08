import Footer from "@/components/layout/Footer";
import Sidebar from "@/components/layout/Sidebar";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex h-screen overflow-hidden bg-color-background text-color-text-main">
      {/* Blueprint grid overlay */}
      <div className="fixed inset-0 pointer-events-none bg-blueprint opacity-30 z-0" />
      {/* Radial gradient overlay for depth */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_at_top,rgba(0,229,255,0.03)_0%,transparent_60%)]" />
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-auto relative z-10">
        {children}
        <Footer />
      </main>
    </div>
  );
}
