const screens = ["home","category","search","search-results","product-list","product-detail","cart","checkout","address","delivery","payment","order-confirmation","account","orders","order-detail","return-request","return-status","rfq","quote-detail","approval-status","support","inventory"];
const states = ["default","loading","empty","failure","out-of-stock","no-results","coupon-valid","coupon-invalid","payment-failed","order-success","approval-pending","approved","rejected","refunded","available","partially-used","limit-exceeded","draft","submitted","in-stock","low-stock"];

export default function HomePage() {
  return (
    <main className="agency-page">
      <p>Reference Retail · Direction A</p>
      <h1>Discovery-first Storefront</h1>
      <p>Demo customer: CUST-B2B-014 · Credit ₹1,85,000 · Warehouse BLR-01</p>
      <nav>{screens.map((x)=><a key={x} href={"#"+x} style={{marginRight:12}}>{x}</a>)}</nav>
      {screens.map((x)=><section id={x} key={x} className="agency-card">
        <h2>{x}</h2>
        <p>Reference transaction data is available for this screen.</p>
        <small>{states.join(" · ")}</small>
      </section>)}
    </main>
  );
}
