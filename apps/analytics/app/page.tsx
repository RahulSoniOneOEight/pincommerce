const screens = ["dashboard","sales","orders","inventory","fulfilment","customers","operations-overview","exceptions","search","return-status","approval-status","exception-detail"];
const exceptions = [
  ["ORD-1002","Payment failed"],["ORD-1007","Inventory shortage"],["ORD-1008","Reconciliation mismatch"],["INV-1009","Overdue receivable"]
];
export default function AnalyticsPage() {
  return <main className="agency-page">
    <p>Reference Retail · Functional Prototype</p>
    <h1>Analytics & Exceptions</h1>
    <section><h2>Operational states</h2>{exceptions.map(([id,label])=><article key={id} className="agency-card"><strong>{id}</strong><p>{label}</p></article>)}</section>
    <section><h2>Available views</h2><p>{screens.join(" · ")}</p></section>
  </main>;
}
