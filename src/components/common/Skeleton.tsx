import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "shimmer rounded-md bg-surface-raised/70",
        className,
      )}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="card overflow-hidden">
      <Skeleton className="aspect-square w-full" />
      <div className="space-y-2.5 p-3">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}
