"use client";

interface Props {
  dday: number | null;
}

export default function DdayBadge({ dday }: Props) {
  if (dday === null) return null;

  let cls = "text-xs font-bold px-2 py-0.5 rounded-full ";
  let label = `D-${dday}`;

  if (dday < 0) {
    cls += "bg-gray-100 text-gray-400";
    label = "마감";
  } else if (dday === 0) {
    cls += "bg-red-600 text-white animate-pulse";
    label = "D-Day";
  } else if (dday <= 3) {
    cls += "bg-red-100 text-red-700";
  } else if (dday <= 7) {
    cls += "bg-orange-100 text-orange-700";
  } else {
    cls += "bg-blue-100 text-blue-700";
  }

  return <span className={cls}>{label}</span>;
}
