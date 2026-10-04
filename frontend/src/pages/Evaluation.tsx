import { FlaskConical } from "lucide-react";

export default function Evaluation() {
  return (
    <div className="page-content">
      <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line" />QUALITY WORKSPACE</div><h1>Evaluation</h1><p className="page-subtitle">Evaluation results from the gateway test set.</p></div></div>
      <div className="empty-state empty-state--large"><div className="empty-state__icon"><FlaskConical size={21} /></div><div><strong>No evaluation results yet</strong><p>Results will appear here after an evaluation run is available from the backend.</p></div></div>
    </div>
  );
}