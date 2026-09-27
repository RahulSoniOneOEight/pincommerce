import { DashboardKpi, ExceptionTable, Surface } from "@pincommerce/agency-web-ui";
import { exceptions, kpis } from "../lib/demo-data";

export default function DashboardPage() {
  return (
    <Surface>
      <header className="page-header">
        <p className="eyebrow">Consolidated admin</p>
        <h1>Commerce + ERP</h1>
        <p className="agency-muted">
          A unified back-office across Medusa (commerce) and Tryton (ERP), with
          operational exceptions surfaced in one place.
        </p>
      </header>

      <section className="kpi-grid">
        {kpis.map((kpi) => (
          <DashboardKpi key={kpi.label} label={kpi.label} value={kpi.value} trendLabel={kpi.trendLabel} />
        ))}
      </section>

      <section className="section">
        <h2>Operational exceptions</h2>
        <ExceptionTable items={exceptions} />
      </section>
    </Surface>
  );
}
