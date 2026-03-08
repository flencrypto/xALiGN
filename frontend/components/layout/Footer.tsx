export default function Footer() {
  return (
    <footer className="relative border-t border-color-border-subtle/30 bg-color-background/60 backdrop-blur-md">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-color-primary/20 to-transparent" />

      <div className="relative z-10 px-6 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-color-success opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-color-success"></span>
            </span>
            <span className="text-[10px] text-color-text-faint font-mono tracking-wider">SYSTEM ONLINE</span>
          </div>
          <span className="text-color-border-subtle">|</span>
          <p className="text-[10px] text-color-text-faint font-mono tracking-wide">
            aLiGN OS &middot; AI-native Bid &amp; Delivery Platform
          </p>
        </div>
        <p className="text-[10px] text-color-text-faint font-mono tracking-wider">v0.2.0</p>
      </div>
    </footer>
  );
}
