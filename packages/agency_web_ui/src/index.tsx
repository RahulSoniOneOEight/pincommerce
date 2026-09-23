import type { ReactNode } from "react";

export type CommerceFixture =
  | "default" | "loading" | "empty" | "failure" | "approval-pending" | "payment-failed"
  | "disabled"
  | "validation-error" | "out-of-stock" | "discounted"
  | "editing" | "open" | "resolved";

export function ProductCard({
  title, priceLabel, previousPriceLabel, state = "default", onActivate,
}: {
  title: string; priceLabel: string; previousPriceLabel?: string;
  state?: CommerceFixture; onActivate?: () => void;
}) {
  if (state === "loading") return <div className="agency-card" role="status">Loading product…</div>;
  if (state === "failure") return <div className="agency-card" role="alert">Product unavailable</div>;
  const unavailable = state === "out-of-stock";
  return (
    <article className="agency-card" data-state={state}>
      <button className="agency-card-action" disabled={unavailable} onClick={onActivate}>
        <span className="agency-body">{title}</span>
        <span className="agency-price">
          <strong className="agency-title">{priceLabel}</strong>
          {state === "discounted" && previousPriceLabel ? <del>{previousPriceLabel}</del> : null}
        </span>
        {unavailable ? <span className="agency-muted">Out of stock</span> : null}
      </button>
    </article>
  );
}

export function CategoryRail({ categories, state = "default", onSelect }: {
  categories: string[]; state?: CommerceFixture; onSelect?: (category: string) => void;
}) {
  if (state === "loading") return <div role="status">Loading categories…</div>;
  if (state === "failure") return <div role="alert">Categories unavailable</div>;
  if (state === "empty" || categories.length === 0) return <div className="agency-card">No categories</div>;
  return (
    <nav className="agency-rail" aria-label="Product categories">
      {categories.map((category) => (
        <button className="agency-chip" key={category} onClick={() => onSelect?.(category)}>{category}</button>
      ))}
    </nav>
  );
}

export type QuickOrderLine = { sku: string; name: string; quantity: number };

export function B2BQuickOrder({ lines, state = "default", onQuantityChange }: {
  lines: QuickOrderLine[]; state?: CommerceFixture;
  onQuantityChange?: (sku: string, quantity: number) => void;
}) {
  if (state === "loading") return <div role="status">Loading quick order…</div>;
  if (state === "failure") return <div role="alert">Quick order unavailable</div>;
  if (state === "empty" || lines.length === 0) return <div className="agency-card">No order lines</div>;
  return (
    <div className="agency-table-wrap">
      <table className="agency-table">
        <caption>B2B quick order</caption>
        <thead><tr><th>SKU</th><th>Product</th><th>Qty</th></tr></thead>
        <tbody>{lines.map((line) => (
          <tr key={line.sku}>
            <td>{line.sku}</td><td>{line.name}</td>
            <td><div className="agency-quantity">
              <button aria-label={`Decrease ${line.name}`} onClick={() => onQuantityChange?.(line.sku, Math.max(0, line.quantity - 1))}>−</button>
              <span>{line.quantity}</span>
              <button aria-label={`Increase ${line.name}`} onClick={() => onQuantityChange?.(line.sku, line.quantity + 1)}>+</button>
            </div></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export function DashboardKpi({ label, value, trendLabel, state = "default" }: {
  label: string; value: string; trendLabel?: string; state?: CommerceFixture;
}) {
  if (state === "loading") return <div className="agency-card" role="status">Loading metric…</div>;
  if (state === "failure") return <div className="agency-card" role="alert">Metric unavailable</div>;
  return <article className="agency-card" aria-label={`${label} ${value}`}>
    <div className="agency-muted">{label}</div>
    <div className="agency-metric">{value}</div>
    {trendLabel ? <div className="agency-muted">{trendLabel}</div> : null}
  </article>;
}

export type ExceptionItem = { id: string; summary: string; status: string };

export function ExceptionTable({ items, state = "default", onOpen }: {
  items: ExceptionItem[]; state?: CommerceFixture; onOpen?: (id: string) => void;
}) {
  if (state === "loading") return <div role="status">Loading exceptions…</div>;
  if (state === "failure") return <div role="alert">Exceptions unavailable</div>;
  if (state === "empty" || items.length === 0) return <div className="agency-card">No exceptions</div>;
  return <div className="agency-table-wrap"><table className="agency-table">
    <caption>Operational exceptions</caption>
    <thead><tr><th>ID</th><th>Exception</th><th>Status</th><th>Action</th></tr></thead>
    <tbody>{items.map((item) => <tr key={item.id}>
      <td>{item.id}</td><td>{item.summary}</td><td>{item.status}</td>
      <td><button onClick={() => onOpen?.(item.id)}>Open</button></td>
    </tr>)}</tbody>
  </table></div>;
}

export function Surface({ children }: { children: ReactNode }) {
  return <section className="agency-surface">{children}</section>;
}
