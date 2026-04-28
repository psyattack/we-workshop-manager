export const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: "trend", label: "Popular" },
  { value: "mostrecent", label: "Most Recent" },
  { value: "lastupdated", label: "Recently Updated" },
  { value: "totaluniquesubscribers", label: "Most Subscribed" },
];

export const TIME_PERIODS: { value: string; label: string }[] = [
  { value: "1", label: "Today" },
  { value: "7", label: "This Week" },
  { value: "30", label: "This Month" },
  { value: "90", label: "3 Months" },
  { value: "180", label: "6 Months" },
  { value: "365", label: "This Year" },
  { value: "-1", label: "All Time" },
];

export const CATEGORIES: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "Wallpaper", label: "Wallpaper" },
  { value: "Preset", label: "Preset" },
  { value: "Asset", label: "Asset" },
];

export const TYPES: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "Scene", label: "Scene" },
  { value: "Video", label: "Video" },
  { value: "Application", label: "Application" },
  { value: "Web", label: "Web" },
];

export const AGE_RATINGS: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "Everyone", label: "Everyone" },
  { value: "Questionable", label: "Questionable" },
  { value: "Mature", label: "Mature" },
];

export const RESOLUTIONS: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "1920 x 1080", label: "1080p" },
  { value: "2560 x 1440", label: "1440p" },
  { value: "3840 x 2160", label: "4K" },
  { value: "1280 x 720", label: "720p" },
  { value: "1366 x 768", label: "768p" },
  { value: "Ultrawide 2560 x 1080", label: "UW 1080p" },
  { value: "Ultrawide 3440 x 1440", label: "UW 1440p" },
  { value: "Portrait 1080 x 1920", label: "Portrait 1080p" },
  { value: "Dynamic resolution", label: "Dynamic" },
  { value: "Other resolution", label: "Other" },
];

export const MISC_TAGS = [
  "Approved",
  "Audio responsive",
  "3D",
  "Customizable",
  "Puppet Warp",
  "HDR",
  "Media Integration",
  "User Shortcut",
  "Video Texture",
  "Asset Pack",
];

export const GENRE_TAGS = [
  "Abstract",
  "Animal",
  "Anime",
  "Cartoon",
  "CGI",
  "Cyberpunk",
  "Fantasy",
  "Game",
  "Girls",
  "Guys",
  "Landscape",
  "Medieval",
  "Memes",
  "MMD",
  "Music",
  "Nature",
  "Pixel art",
  "Relaxing",
  "Retro",
  "Sci-Fi",
  "Sports",
  "Technology",
  "Television",
  "Vehicle",
  "Unspecified",
];

export const ASSET_TYPES: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "Particle", label: "Particle" },
  { value: "Image", label: "Image" },
  { value: "Sound", label: "Sound" },
  { value: "Model", label: "Model" },
  { value: "Text", label: "Text" },
  { value: "Sprite", label: "Sprite" },
  { value: "Fullscreen", label: "Fullscreen" },
  { value: "Composite", label: "Composite" },
  { value: "Script", label: "Script" },
  { value: "Effect", label: "Effect" },
];

export const ASSET_GENRES: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "Audio Visualizer", label: "Audio Visualizer" },
  { value: "Background", label: "Background" },
  { value: "Character", label: "Character" },
  { value: "Clock", label: "Clock" },
  { value: "Fire", label: "Fire" },
  { value: "Interactive", label: "Interactive" },
  { value: "Magic", label: "Magic" },
  { value: "Post Processing", label: "Post Processing" },
  { value: "Smoke", label: "Smoke" },
  { value: "Space", label: "Space" },
];

export const SCRIPT_TYPES: { value: string; label: string }[] = [
  { value: "", label: "Any" },
  { value: "Boolean", label: "Boolean" },
  { value: "Number", label: "Number" },
  { value: "Vec2", label: "Vec2" },
  { value: "Vec3", label: "Vec3" },
  { value: "Vec4", label: "Vec4" },
  { value: "String", label: "String" },
  { value: "No Animation", label: "No Animation" },
  { value: "Oversized", label: "Oversized" },
];

export const REQUIRED_FLAG_OPTIONS: { value: string; label: string }[] = [
  { value: "notags:exclusive_content", label: "Exclude NSFW" },
];
