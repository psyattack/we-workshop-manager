import type { RawTag } from "@/types/workshop";

export interface TagGroup {
  category: string;
  values: string[];
}

export function workshopUrl(pubfileid: string): string {
  return `https://steamcommunity.com/sharedfiles/filedetails/?id=${pubfileid}`;
}

export function parseRatingStars(ratingStarFile?: string): number {
  if (!ratingStarFile) return 0;
  const match = ratingStarFile.match(/(\d+)/);
  if (!match) return 0;
  const value = Number.parseInt(match[1], 10);
  return Number.isFinite(value) ? Math.max(0, Math.min(5, value)) : 0;
}

export function groupTags(
  rawTags: RawTag[] | undefined,
  fallbackCategory: string,
): TagGroup[] {
  const groups = new Map<string, string[]>();
  for (const raw of rawTags ?? []) {
    const label = typeof raw === "string" ? raw : (raw.tag ?? "");
    const rawCategory = typeof raw === "string" ? "" : (raw.category ?? "");
    if (!label || /^\W*$/.test(label)) continue;
    const category =
      rawCategory && /\w/.test(rawCategory) ? rawCategory : fallbackCategory;
    const values = groups.get(category) ?? [];
    values.push(label);
    groups.set(category, values);
  }
  return Array.from(groups.entries()).map(([category, values]) => ({
    category,
    values,
  }));
}

export function extractTagLabel(raw: RawTag): string {
  return typeof raw === "string" ? raw : (raw.tag ?? "");
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
