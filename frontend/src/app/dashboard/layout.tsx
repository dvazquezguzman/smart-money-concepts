import Link from "next/link";
import BotStatus from "@/components/BotStatus";

const NAV_ITEMS = [
  { href: "/dashboard/overview", label: "Overview" },
  { href: "/dashboard/charts", label: "Charts" },
  { href: "/dashboard/strategies", label: "Strategies" },
  { href: "/dashboard/paper-trading", label: "Paper Trading" },
  { href: "/dashboard/live-trading", label: "Live Trading" },
  { href: "/dashboard/config", label: "Config" },
  { href: "/dashboard/history", label: "History" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full">
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-white">SMC Dashboard</h1>
          <p className="text-xs text-gray-500 mt-1">Smart Money Concepts</p>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block px-3 py-2 text-sm text-gray-400 rounded hover:bg-gray-800 hover:text-white transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <BotStatus label="Data Engine" running />
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
