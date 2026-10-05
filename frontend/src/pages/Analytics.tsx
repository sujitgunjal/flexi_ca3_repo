import { ChartNoAxesColumn } from "lucide-react";

export default function Analytics() {
  return (
    <div className="page-content">
      <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line" />TRAFFIC INSIGHTS</div><h1>Analytics</h1><p className="page-subtitle">Gateway activity summarized over time.</p></div></div>
      <div className="empty-state empty-state--large"><div className="empty-state__icon"><ChartNoAxesColumn size={21} /></div><div><strong>Analytics are waiting for request history</strong><p>Trend data will appear when the gateway exposes request records.</p></div></div>
    </div>
  );
}