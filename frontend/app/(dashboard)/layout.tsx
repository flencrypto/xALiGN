import Sidebar from "@/components/layout/Sidebar";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-text-main">
      {/* Blueprint grid overlay */}
      <div className="fixed inset-0 pointer-events-none bg-blueprint opacity-50 z-0" />
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-auto relative z-10">
        {children}
      </main>
    </div>
  );
}
