import { ArrowRight, BrainCircuit, CircleHelp, Clock3, Coins, Database, Hash, Layers3, Network, Route, ShieldCheck } from "lucide-react";
import { MetricCard } from "../components/MetricCard";
import type { GatewayMetrics, RequestRecord } from "../types";

interface DashboardProps {
	metrics: GatewayMetrics | null;
	requests: RequestRecord[];
	isLoading: boolean;
	metricsError: string | null;
	requestsError: string | null;
	onOpenRequests: () => void;
}

const integer = new Intl.NumberFormat("en-US");
const currency = new Intl.NumberFormat("en-US", {
	style: "currency",
	currency: "USD",
	minimumFractionDigits: 2,
	maximumFractionDigits: 4,
});

const pipelineStages = [
	{ label: "Cache", detail: "Check for a match", icon: Database, tone: "green" },
	{ label: "Complexity", detail: "Assess the request", icon: BrainCircuit, tone: "blue" },
	{ label: "Context", detail: "Select relevant history", icon: Layers3, tone: "amber" },
	{ label: "Model router", detail: "Choose a model tier", icon: Route, tone: "rose" },
	{ label: "Quality", detail: "Review the response", icon: ShieldCheck, tone: "green" },
];

function tokenTotal(metrics: GatewayMetrics | null): number {
	return (metrics?.tokens_input ?? 0) + (metrics?.tokens_output ?? 0);
}

function metricNote(value: number, total: number): string {
	if (!total) return "No requests recorded";
	return `${((value / total) * 100).toFixed(1)}% of total requests`;
}

export default function Dashboard({
	metrics,
	requests,
	isLoading,
	metricsError,
	requestsError,
	onOpenRequests,
}: DashboardProps) {
	const total = metrics?.total_requests ?? 0;
	const cacheHits = metrics?.cache_hits ?? 0;

	return (
		<div className="page-content">
			<div className="page-heading">
				<div>
					<div className="eyebrow"><span className="eyebrow__line" />INTELLIGENT MODEL ROUTING</div>
					<h1>Gateway overview</h1>
					<p className="page-subtitle">One considered path from prompt to response.</p>
				</div>
				<div className={`live-badge${metricsError ? " live-badge--offline" : isLoading ? " live-badge--loading" : ""}`}>
					<span />{metricsError ? "API OFFLINE" : isLoading ? "CONNECTING" : "LIVE DATA"}
				</div>
			</div>

			{metricsError && (
				<div className="notice notice--error" role="alert">
					<CircleHelp size={17} />
					<span>Metrics unavailable: {metricsError}</span>
				</div>
			)}

			<section className="metrics-grid" aria-label="Gateway metrics" aria-busy={isLoading}>
				<MetricCard
					label="Total requests"
					value={metrics ? integer.format(total) : isLoading ? "—" : "Unavailable"}
					note={metrics ? `${integer.format(metrics.llm_calls)} sent to models` : "GET /metrics"}
					icon={Network}
					accent="green"
				/>
				<MetricCard
					label="Cache hits"
					value={metrics ? integer.format(cacheHits) : isLoading ? "—" : "Unavailable"}
					note={metrics ? metricNote(cacheHits, total) : "GET /metrics"}
					icon={Database}
					accent="blue"
				/>
				<MetricCard
					label="Tokens used"
					value={metrics ? integer.format(tokenTotal(metrics)) : isLoading ? "—" : "Unavailable"}
					note={metrics ? `${integer.format(metrics.tokens_input)} in · ${integer.format(metrics.tokens_output)} out` : "GET /metrics"}
					icon={Hash}
					accent="amber"
				/>
				<MetricCard
					label="Estimated cost"
					value={metrics ? currency.format(metrics.estimated_cost) : isLoading ? "—" : "Unavailable"}
					note="USD · reported by gateway"
					icon={Coins}
					accent="rose"
				/>
				<MetricCard
					label="Average latency"
					value={metrics ? `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(metrics.average_latency_ms)} ms` : isLoading ? "—" : "Unavailable"}
					note="average response time"
					icon={Clock3}
					accent="teal"
				/>
			</section>

			<section className="flow-section" aria-labelledby="flow-title">
				<div className="flow-heading">
					<div>
						<div className="eyebrow">MULTI-AGENT ORCHESTRATION</div>
						<h2 id="flow-title">How a request moves</h2>
					</div>
					<span className="flow-count">5 STAGES</span>
				</div>
				<div className="flow-track-viewport">
					<div className="flow-track">
						{pipelineStages.map(({ label, detail, icon: Icon, tone }, index) => (
							<div className="flow-unit" key={label}>
								<div className="flow-stage">
									<div className={`flow-stage__icon flow-stage__icon--${tone}`}><Icon size={18} strokeWidth={1.8} /></div>
									<div className="flow-stage__title"><span>0{index + 1}</span><strong>{label}</strong></div>
									<p>{detail}</p>
								</div>
								{index < pipelineStages.length - 1 && <ArrowRight className="flow-arrow" size={16} aria-hidden="true" />}
							</div>
						))}
					</div>
				</div>
			</section>

			<section className="section-block">
				<div className="section-heading">
					<div>
						<div className="eyebrow">ACTIVITY</div>
						<h2>Recent requests</h2>
					</div>
					<button className="text-button" onClick={onOpenRequests}>View all <span aria-hidden="true">↗</span></button>
				</div>
				{requestsError ? (
					<div className="empty-state empty-state--warning">
						<div className="empty-state__icon"><CircleHelp size={20} /></div>
						<div><strong>Request history is unavailable</strong><p>{requestsError}</p></div>
					</div>
				) : requests.length === 0 ? (
					<div className="empty-state">
						<div className="empty-state__icon"><ActivityIcon /></div>
						<div><strong>{isLoading ? "Loading request history" : "No requests to show"}</strong><p>{isLoading ? "Waiting for gateway data." : "Request records will appear here when available."}</p></div>
					</div>
				) : (
					<RequestRows requests={requests.slice(0, 5)} />
				)}
			</section>

			<div className="dashboard-footnote">
				<span className="footnote-dot" />
				<span>Metrics are reported by the gateway. No sample data is shown.</span>
			</div>
		</div>
	);
}

function ActivityIcon() {
	return <Network size={19} strokeWidth={1.7} />;
}

function RequestRows({ requests }: { requests: RequestRecord[] }) {
	return (
		<div className="table-wrap">
			<table className="data-table">
				<thead><tr><th>Request</th><th>Model</th><th>Tokens</th><th>Latency</th><th>Cost</th></tr></thead>
				<tbody>
					{requests.map((request) => (
						<tr key={request.id}>
							<td><span className="request-query">{request.query || `Request #${request.id}`}</span><span className="request-time">{formatTimestamp(request.timestamp)}</span></td>
							<td>{request.final_model || request.selected_model || "—"}</td>
							<td>{integer.format(request.total_tokens ?? ((request.input_tokens ?? 0) + (request.output_tokens ?? 0)))}</td>
							<td>{request.latency_ms == null ? "—" : `${Math.round(request.latency_ms)} ms`}</td>
							<td>{request.estimated_cost == null ? "—" : currency.format(request.estimated_cost)}</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
}

export function formatTimestamp(timestamp?: string | null): string {
	if (!timestamp) return "Time not recorded";
	const date = new Date(timestamp);
	return Number.isNaN(date.getTime())
		? timestamp
		: date.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
