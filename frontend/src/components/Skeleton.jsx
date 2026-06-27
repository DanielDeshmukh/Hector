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

export function SearchSkeleton() {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Pipeline status skeleton */}
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-5 rounded-full" />
        <Skeleton className="h-2 w-16 rounded" />
        <Skeleton className="h-2 w-16 rounded" />
        <Skeleton className="h-2 w-16 rounded" />
        <Skeleton className="h-2 w-16 rounded" />
      </div>

      {/* Domain and confidence badges */}
      <div className="flex gap-2">
        <Skeleton className="h-6 w-28 rounded-md" />
        <Skeleton className="h-6 w-32 rounded-md" />
        <Skeleton className="h-5 w-20 rounded" />
      </div>

      {/* Response text skeleton */}
      <div className="rounded-lg border border-slate-custom/30 bg-charcoal/40 p-5 space-y-3">
        <Skeleton className="h-4 w-32 rounded" />
        <div className="space-y-2">
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-5/6 rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-2/3 rounded" />
        </div>
        <Skeleton className="h-4 w-40 rounded mt-4" />
        <div className="space-y-2">
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-4/5 rounded" />
        </div>
      </div>

      {/* Source cards skeleton */}
      <div>
        <Skeleton className="h-3 w-32 rounded mb-3" />
        <div className="grid gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-lg border border-slate-custom/30 bg-cream/50 p-3.5">
              <div className="flex items-start gap-3">
                <Skeleton className="h-6 w-6 rounded shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-40 rounded" />
                  <Skeleton className="h-2.5 w-24 rounded" />
                  <Skeleton className="h-2.5 w-full rounded" />
                  <div className="flex gap-2">
                    <Skeleton className="h-4 w-16 rounded" />
                    <Skeleton className="h-4 w-12 rounded" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function CompareSkeleton() {
  return (
    <div className="space-y-4 animate-fade-in">
      <Skeleton className="h-5 w-48 rounded" />
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3">
          <Skeleton className="h-4 w-24 rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-3/4 rounded" />
        </div>
        <div className="space-y-3">
          <Skeleton className="h-4 w-24 rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-3/4 rounded" />
        </div>
      </div>
    </div>
  );
}
