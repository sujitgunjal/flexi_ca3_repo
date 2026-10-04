import { CircleHelp, Search } from "lucide-react";
import { formatTimestamp } from "./Dashboard";
import type { RequestRecord } from "../types";

interface RequestsProps {
	requests: RequestRecord[];
	isLoading: boolean;
	error: string | null;
}

const integer = new Intl.NumberFormat("en-US");
const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 4 });

export default function Requests({ requests, isLoading, error }: RequestsProps) {
	return (
		<div className="page-content">
			<div className="page-heading">
				<div><div className="eyebrow"><span className="eyebrow__line" />GATEWAY ACTIVITY</div><h1>Requests</h1><p className="page-subtitle">Request records returned by the gateway.</p></div>
				<span className="count-badge">{requests.length} records</span>
			</div>
			{error ? (
				<div className="empty-state empty-state--warning"><div className="empty-state__icon"><CircleHelp size={20} /></div><div><strong>Request endpoint unavailable</strong><p>{error}</p></div></div>
			) : requests.length ? (
				<div className="table-wrap table-wrap--full">
					<table className="data-table">
						<thead><tr><th>Request</th><th>Complexity</th><th>Model</th><th>Cache</th><th>Tokens</th><th>Latency</th><th>Cost</th></tr></thead>
						<tbody>{requests.map((request) => (
							<tr key={request.id}>
								<td><span className="request-query">{request.query || `Request #${request.id}`}</span><span className="request-time">{formatTimestamp(request.timestamp)}</span></td>
								<td>{request.complexity || "—"}</td>
								<td>{request.final_model || request.selected_model || "—"}</td>
								<td><span className={`cache-state${request.cache_hit ? " cache-state--hit" : ""}`}>{request.cache_hit == null ? "—" : request.cache_hit ? "Hit" : "Miss"}</span></td>
								<td>{integer.format(request.total_tokens ?? ((request.input_tokens ?? 0) + (request.output_tokens ?? 0)))}</td>
								<td>{request.latency_ms == null ? "—" : `${Math.round(request.latency_ms)} ms`}</td>
								<td>{request.estimated_cost == null ? "—" : currency.format(request.estimated_cost)}</td>
							</tr>
						))}</tbody>
					</table>
				</div>
			) : (
				<div className="empty-state"><div className="empty-state__icon"><Search size={19} /></div><div><strong>{isLoading ? "Loading requests" : "No request records"}</strong><p>{isLoading ? "Waiting for gateway data." : "No request records were returned by the gateway."}</p></div></div>
			)}
		</div>
	);
}
