import clsx, { ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let idx = 0;
  let value = bytes;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx += 1;
  }
  return `${value.toFixed(value >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`;
}

export function formatTimestamp(unix: number): string {
  if (!unix) return "—";
  try {
    return new Date(unix * 1000).toLocaleString();
  } catch {
    return "—";
  }
}

export function extractWorkshopIds(input: string): string[] {
  const ids = new Set<string>();
  const tokens = input.split(/[\s,;]+/).filter(Boolean);
  for (const token of tokens) {
    const match = token.match(/(?:id=)?(\d{6,})/);
    if (match) ids.add(match[1]);
  }
  return [...ids];
}
