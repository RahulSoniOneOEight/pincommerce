import type { ReactNode } from "react";

export function DataTable({ caption, columns, rows }: {
  caption: string;
  columns: string[];
  rows: ReactNode[][];
}) {
  return (
    <div className="agency-table-wrap">
      <table className="agency-table">
        <caption>{caption}</caption>
        <thead>
          <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Status({ value }: { value: string }) {
  const tone =
    value === "in-stock" || value === "paid" || value === "fulfilled" || value === "invoiced" || value === "closed" || value === "resolved"
      ? "positive"
      : value === "out-of-stock" || value === "returned" || value === "open" || value === "retrying"
        ? "negative"
        : value === "low-stock" || value === "pending" || value === "confirmed"
          ? "warning"
          : "neutral";
  return <span className={`status status-${tone}`}>{value}</span>;
}
