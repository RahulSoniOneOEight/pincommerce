const screens = ["dashboard","products","orders","inventory","promotions","returns","customers","settings","search","product-detail","checkout","rfq","quote-detail","support","home","category","product-list","cart","exceptions","exception-detail","account","approval-status"];
const states = ["default","loading","empty","failure","no-results","coupon-valid","coupon-invalid","approval-pending","approved","rejected","refunded","in-stock","low-stock","out-of-stock","available","limit-exceeded","draft","submitted","open","retrying","resolved","failed"];

export default function CommerceAdminPage() {
  return <main className="agency-page">
    <p>Reference Retail · Functional Prototype</p>
    <h1>Commerce Admin</h1>
    <p>Deterministic demo orders, inventory, promotions, returns and B2B approval states.</p>
    <section><h2>Screens</h2><div>{screens.map(x=><a key={x} href={"#"+x} style={{marginRight:12}}>{x}</a>)}</div></section>
    <section>{screens.map(x=><article id={x} key={x} className="agency-card"><h3>{x}</h3><p>Reference data loaded for {x}.</p><small>{states.join(" · ")}</small></article>)}</section>
  </main>;
}
