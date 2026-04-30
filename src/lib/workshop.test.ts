import { describe, expect, it } from "vitest";

import {
  extractWorkshopIds,
  groupTags,
  parseRatingStars,
  workshopUrl,
} from "@/lib/workshop";

describe("workshop helpers", () => {
  it("extracts unique Workshop ids from mixed text", () => {
    expect(
      extractWorkshopIds(
        "https://steamcommunity.com/sharedfiles/filedetails/?id=123456789, 987654321; id=123456789",
      ),
    ).toEqual(["123456789", "987654321"]);
  });

  it("groups valid tags and skips punctuation-only labels", () => {
    expect(
      groupTags(
        [
          { tag: "Scene", category: "Type" },
          { tag: "3D" },
          { tag: "·", category: "." },
          "Anime",
        ],
        "Tags",
      ),
    ).toEqual([
      { category: "Type", values: ["Scene"] },
      { category: "Tags", values: ["3D", "Anime"] },
    ]);
  });

  it("parses rating stars defensively", () => {
    expect(parseRatingStars("4-star.png")).toBe(4);
    expect(parseRatingStars("rating_99.png")).toBe(5);
    expect(parseRatingStars(undefined)).toBe(0);
  });

  it("builds Steam Workshop item urls", () => {
    expect(workshopUrl("123456789")).toBe(
      "https://steamcommunity.com/sharedfiles/filedetails/?id=123456789",
    );
  });
});
