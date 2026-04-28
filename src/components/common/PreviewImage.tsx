import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { convertFileSrc } from "@tauri-apps/api/core";
import { Image as ImageIcon } from "lucide-react";

import { inTauri } from "@/lib/tauri";
import { cn } from "@/lib/utils";

interface Props {
  src?: string;
  alt?: string;
  className?: string;
  fallback?: React.ReactNode;
  fit?: "cover" | "contain";
}

function isRemote(src: string): boolean {
  return /^(https?:|data:|blob:|asset:|tauri:)/i.test(src);
}

function toDisplaySrc(src?: string): string | undefined {
  if (!src) return undefined;
  if (isRemote(src)) return src;
  // Local absolute filesystem path -> convert via Tauri's asset protocol.
  if (inTauri) {
    try {
      return convertFileSrc(src);
    } catch {
      return src;
    }
  }
  return src;
}

export default function PreviewImage({
  src,
  alt,
  className,
  fallback,
  fit = "cover",
}: Props) {
  const [resolved, setResolved] = useState<string | undefined>(
    toDisplaySrc(src),
  );
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
    setResolved(toDisplaySrc(src));
  }, [src]);

  if (!src || failed) {
    return (
      <div
        className={cn(
          "flex h-full w-full items-center justify-center bg-surface-sunken text-subtle",
          className,
        )}
      >
        {fallback ?? <ImageIcon className="h-6 w-6" />}
      </div>
    );
  }

  return (
    <motion.img
      src={resolved}
      alt={alt ?? ""}
      loading="lazy"
      draggable={false}
      onError={() => {
        setFailed(true);
      }}
      initial={{ opacity: 0, scale: 1.02 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.25 }}
      className={cn(
        "h-full w-full",
        fit === "cover" ? "object-cover" : "object-contain",
        className,
      )}
    />
  );
}
