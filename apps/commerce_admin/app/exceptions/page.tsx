import { ExceptionTable, Surface } from "@pincommerce/agency-web-ui";
import { exceptions } from "../../lib/demo-data";

export default function ExceptionsPage() {
  return (
    <Surface>
      <header className="page-header">
        <p className="eyebrow">Operations</p>
        <h1>Exceptions</h1>
        <p className="agency-muted">Dead-letter, reconciliation and provider-health alerts.</p>
      </header>
      <ExceptionTable items={exceptions} />
    </Surface>
  );
}
