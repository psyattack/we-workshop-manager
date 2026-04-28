export interface CollectionRef {
  id: string;
  title: string;
  item_count: number;
}

export interface WorkshopItem {
  pubfileid: string;
  title: string;
  preview_url: string;
  author: string;
  author_url: string;
  description: string;
  file_size: string;
  posted_date: string;
  updated_date: string;
  tags: unknown;
  rating_star_file: string;
  num_ratings: string;
  is_collection: boolean;
  collections?: CollectionRef[];
}

export interface WorkshopPage {
  items: WorkshopItem[];
  total_pages: number;
  total_items: number;
  current_page: number;
}

export interface InstalledWallpaper {
  pubfileid: string;
  folder: string;
  project_json_path: string;
  has_pkg: boolean;
  title: string;
  preview: string;
  description: string;
  file_type: string;
  tags: string[];
  size_bytes: number;
  installed_ts: number;
}
