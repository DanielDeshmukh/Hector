"use client";

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  actionLabel,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center animate-fade-in">
      {Icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-custom/20 text-silver/40">
          <Icon size={22} />
        </div>
      )}
      {title && (
        <h3 className="mb-1 text-[13px] font-medium text-silver/70">
          {title}
        </h3>
      )}
      {description && (
        <p className="max-w-xs text-[12px] leading-relaxed text-silver/40">
          {description}
        </p>
      )}
      {action && actionLabel && (
        <button
          onClick={action}
          className="mt-4 rounded-lg border border-gold/20 bg-gold/5 px-4 py-1.5 text-[12px] font-medium text-gold transition-colors hover:bg-gold/10"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
