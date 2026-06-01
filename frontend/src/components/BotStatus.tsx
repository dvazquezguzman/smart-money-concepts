"use client";

interface Props {
  label: string;
  running?: boolean;
}

export default function BotStatus({ label, running }: Props) {
  const color = running === undefined ? "bg-yellow-500" : running ? "bg-green-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 text-sm text-gray-300">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      <span>{label}</span>
    </div>
  );
}
