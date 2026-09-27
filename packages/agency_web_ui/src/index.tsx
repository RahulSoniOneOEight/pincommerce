"use client";

import type { ReactNode } from "react";

export type AgencyIconConcept = "increment" | "decrement" | "search" | "warning" | "success" | "error";

export function AgencyIcon({ concept }: { concept: AgencyIconConcept }) {
  const path = concept === "increment" ? "M12 5v14M5 12h14"
    : concept === "decrement" ? "M5 12h14"
    : concept === "search" ? "M11 4a7 7 0 1 0 0 14a7 7 0 0 0 0-14Zm5 12l4 4"
    : concept === "warning" ? "M12 4l9 16H3L12 4Zm0 5v5m0 3h.01"
    : concept === "success" ? "M5 12l4 4L19 6"
    : "M6 6l12 12M18 6L6 18";
  return <svg className="agency-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" data-semantic-icon={concept}><path d={path} /></svg>;
}

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
              <button aria-label={`Decrease ${line.name}`} onClick={() => onQuantityChange?.(line.sku, Math.max(0, line.quantity - 1))}><AgencyIcon concept="decrement" /></button>
              <span>{line.quantity}</span>
              <button aria-label={`Increase ${line.name}`} onClick={() => onQuantityChange?.(line.sku, line.quantity + 1)}><AgencyIcon concept="increment" /></button>
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

export function FilterBar({ filters, selected = [], onSelect, onClear, state = "default" }: {
  filters: string[]; selected?: string[]; onSelect?: (filter: string) => void; onClear?: () => void; state?: CommerceFixture;
}) {
  const disabled = state === "disabled";
  return <section className="agency-filter-bar" aria-label="Product filters">
    {filters.map((filter) => <button key={filter} className="agency-chip" aria-pressed={selected.includes(filter)} disabled={disabled} onClick={() => onSelect?.(filter)}>{filter}</button>)}
    <button disabled={disabled} onClick={onClear}>Clear</button>
  </section>;
}

export function CheckoutSummary({ subtotal, shipping, total, onContinue, state = "default" }: {
  subtotal: string; shipping: string; total: string; onContinue?: () => void; state?: CommerceFixture;
}) {
  if (state === "loading") return <div role="status">Loading checkout summary…</div>;
  const disabled = state === "disabled";
  return <article className="agency-card" aria-label="Checkout summary">
    <dl className="agency-summary-list">
      <div><dt>Subtotal</dt><dd>{subtotal}</dd></div>
      <div><dt>Shipping</dt><dd>{shipping}</dd></div>
      <div><dt>Total</dt><dd>{total}</dd></div>
    </dl>
    <button disabled={disabled} onClick={onContinue}>Continue checkout</button>
  </article>;
}

export function NavigationMenu({ items, current, onNavigate, state = "default" }: {
  items: string[]; current: string; onNavigate?: (item: string) => void; state?: CommerceFixture;
}) {
  const disabled = state === "disabled";
  return <nav className="agency-nav" aria-label="Primary navigation">
    {items.map((item) => <button key={item} aria-current={item === current ? "page" : undefined} disabled={disabled} onClick={() => onNavigate?.(item)}>{item}</button>)}
  </nav>;
}

export function FormSection({ label, value, helper, error, onChange, state = "default" }: {
  label: string; value: string; helper?: string; error?: string; onChange?: (value: string) => void; state?: CommerceFixture;
}) {
  const disabled = state === "disabled";
  const effectiveError = state === "validation-error" ? (error || "Check this value") : error;
  const id = "agency-field-" + label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return <div className="agency-form-section">
    <label htmlFor={id}>{label}</label>
    <input id={id} value={value} disabled={disabled} aria-invalid={Boolean(effectiveError)} aria-describedby={helper || effectiveError ? id + "-help" : undefined} onChange={(event) => onChange?.(event.target.value)} />
    {(helper || effectiveError) ? <div id={id + "-help"} role={effectiveError ? "alert" : undefined}>{effectiveError || helper}</div> : null}
  </div>;
}

export function Surface({ children }: { children: ReactNode }) {
  return <section className="agency-surface">{children}</section>;
}
