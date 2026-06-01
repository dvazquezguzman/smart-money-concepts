export default function OverviewPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatCard title="Active Strategies" value="0" />
        <StatCard title="Open Positions" value="0" />
        <StatCard title="Total P&L" value="$0.00" />
      </div>
      <p className="text-gray-500 text-sm">
        Configure strategies and start paper trading to see your performance here.
      </p>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-sm text-gray-400">{title}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}
