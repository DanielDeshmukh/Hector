export function Skeleton({ className = "" }) {
  return (
    <div
      className={`animate-pulse rounded bg-slate-custom/30 ${className}`}
    />
  );
}

export function ResponseSkeleton() {
  return (
    <div className="space-y-4 animate-fade-in">
      <Skeleton className="h-4 w-24 rounded" />
      <Skeleton className="h-3 w-16 rounded" />
      <div className="space-y-2">
        <Skeleton className="h-3 w-full rounded" />
        <Skeleton className="h-3 w-full rounded" />
        <Skeleton className="h-3 w-3/4 rounded" />
      </div>
      <div className="space-y-2 pt-2">
        <Skeleton className="h-3 w-20 rounded" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-24 rounded-lg" />
          <Skeleton className="h-24 rounded-lg" />
        </div>
      </div>
    </div>
  );
}
