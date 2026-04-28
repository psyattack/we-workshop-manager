import { useTranslation } from "react-i18next";
import { ExternalLink, User, Calendar, RefreshCw, Heart, Eye, Users, Star, Package } from "lucide-react";
import { openUrl as openExternal } from "@tauri-apps/plugin-opener";

import Dialog from "@/components/common/Dialog";
import PreviewImage from "@/components/common/PreviewImage";
import { useNavStore } from "@/stores/nav";
import { inTauri } from "@/lib/tauri";
import type { CollectionContents } from "@/components/views/CollectionsView";

interface Props {
  open: boolean;
  onClose: () => void;
  collection: CollectionContents | null;
}

/**
 * Replicates the Python `CollectionInfoDialog`: clicking the collection
 * title in the header brings up its preview, author and description.
 * Items count is also useful here so the user doesn't have to look at the
 * grid count separately.
 */
export default function CollectionInfoDialog({
  open,
  onClose,
  collection,
}: Props) {
  const { t } = useTranslation();
  const openAuthor = useNavStore((s) => s.openAuthor);

  if (!collection) return null;

  const openWorkshop = async () => {
    const url = `https://steamcommunity.com/sharedfiles/filedetails/?id=${collection.collection_id}`;
    if (inTauri) await openExternal(url);
    else window.open(url, "_blank");
  };

  const goAuthor = () => {
    if (!collection.author_url) return;
    openAuthor(collection.author_url, collection.author);
    onClose();
  };

  const info = collection.info || {};
  const ratingStars = info.rating_star_file ? parseInt(info.rating_star_file.replace(/\D/g, '')) : 0;

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => !o && onClose()}
      title={collection.title || t("labels.collections")}
      size="md"
    >
      <div className="flex flex-col gap-4 text-sm">
        {/* Preview Image */}
        {collection.preview_url && (
          <div className="overflow-hidden rounded-lg border border-border bg-surface-sunken">
            <PreviewImage
              src={collection.preview_url}
              alt={collection.title}
              className="aspect-[16/9] w-full object-cover"
            />
          </div>
        )}

        {/* Action Button */}
        <button
          type="button"
          onClick={openWorkshop}
          className="flex items-center justify-center gap-2 rounded-lg border border-border-strong bg-surface px-4 py-2.5 text-sm font-semibold hover:bg-surface-raised"
        >
          <ExternalLink className="h-4 w-4" />
          {t("buttons.open_workshop")}
        </button>

        {/* Main Info Grid */}
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-surface-sunken/50 p-3 text-xs">
          {/* ID */}
          <div className="col-span-2 flex items-center gap-2 border-b border-border pb-2">
            <span className="text-subtle">ID:</span>
            <span className="font-mono text-foreground">{collection.collection_id}</span>
          </div>

          {/* Author */}
          {collection.author && (
            <div className="col-span-2 flex items-center gap-2">
              <User className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">{t("labels.author", { author: "" })}</span>
              <button
                type="button"
                className="font-semibold text-primary hover:underline disabled:opacity-60 disabled:no-underline"
                disabled={!collection.author_url}
                onClick={goAuthor}
              >
                {collection.author}
              </button>
            </div>
          )}

          {/* Rating */}
          {ratingStars > 0 && (
            <div className="flex items-center gap-2">
              <Star className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Rating:</span>
              <div className="flex items-center gap-0.5">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-3.5 w-3.5 ${
                      i < ratingStars
                        ? "fill-yellow-500 text-yellow-500"
                        : "text-border"
                    }`}
                  />
                ))}
              </div>
              {info.num_ratings && (
                <span className="text-subtle">({info.num_ratings})</span>
              )}
            </div>
          )}

          {/* Items Count */}
          <div className="flex items-center gap-2">
            <Package className="h-3.5 w-3.5 text-subtle" />
            <span className="text-subtle">Items:</span>
            <span className="font-semibold text-foreground">{collection.items.length}</span>
          </div>

          {/* Statistics Row 1 */}
          {info.unique_visitors && (
            <div className="flex items-center gap-2">
              <Eye className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Visitors:</span>
              <span className="text-foreground">{info.unique_visitors}</span>
            </div>
          )}

          {info.subscribers && (
            <div className="flex items-center gap-2">
              <Users className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Subscribers:</span>
              <span className="text-foreground">{info.subscribers}</span>
            </div>
          )}

          {/* Statistics Row 2 */}
          {info.favorited && (
            <div className="flex items-center gap-2">
              <Heart className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Favorited:</span>
              <span className="text-foreground">{info.favorited}</span>
            </div>
          )}

          {info.total_favorited && info.total_favorited !== info.favorited && (
            <div className="flex items-center gap-2">
              <Heart className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Total:</span>
              <span className="text-foreground">{info.total_favorited}</span>
            </div>
          )}

          {/* Dates */}
          {info.posted_date && (
            <div className="flex items-center gap-2">
              <Calendar className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Posted:</span>
              <span className="text-foreground">{info.posted_date}</span>
            </div>
          )}

          {info.updated_date && (
            <div className="flex items-center gap-2">
              <RefreshCw className="h-3.5 w-3.5 text-subtle" />
              <span className="text-subtle">Updated:</span>
              <span className="text-foreground">{info.updated_date}</span>
            </div>
          )}
        </div>

        {/* Tags Section */}
        {info && Object.keys(info).some(key => 
          ['Miscellaneous', 'Genre', 'Category', 'Age Rating', 'Type', 'Resolution', 'Content Descriptors'].includes(key)
        ) && (
          <div className="space-y-1.5 rounded-lg border border-border bg-surface-sunken/50 p-3 text-xs">
            {['Genre', 'Category', 'Type', 'Resolution', 'Age Rating', 'Miscellaneous', 'Content Descriptors'].map(tagKey => {
              if (!info[tagKey]) return null;
              const values = info[tagKey].split(',').map((v: string) => v.trim());
              return (
                <div key={tagKey} className="flex flex-wrap items-center gap-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-subtle">
                    {tagKey}:
                  </span>
                  {values.map((v: string, i: number) => (
                    <span
                      key={`${v}-${i}`}
                      className="chip !py-0 text-[11px]"
                    >
                      {v}
                    </span>
                  ))}
                </div>
              );
            })}
          </div>
        )}

        {/* Description */}
        {collection.description ? (
          <div className="max-h-60 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-surface-sunken/50 p-3 text-xs leading-relaxed text-foreground">
            {collection.description}
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-surface-sunken p-3 text-xs text-subtle">
            {t("labels.no_description")}
          </div>
        )}
      </div>
    </Dialog>
  );
}
