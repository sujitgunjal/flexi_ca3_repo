import { CircleHelp, Server } from "lucide-react";
import type { ModelInfo } from "../types";

interface ModelsProps {
	models: ModelInfo[];
	isLoading: boolean;
	error: string | null;
}

export default function Models({ models, isLoading, error }: ModelsProps) {
	return (
		<div className="page-content">
			<div className="page-heading">
				<div><div className="eyebrow"><span className="eyebrow__line" />GATEWAY INVENTORY</div><h1>Models</h1><p className="page-subtitle">Configured model tiers and provider availability.</p></div>
				<span className="count-badge">{models.length} configured</span>
			</div>
			{error ? <div className="notice notice--error" role="alert"><CircleHelp size={17} /><span>Models unavailable: {error}</span></div> : null}
			{models.length ? (
				<div className="model-list">
					{models.map((model) => (
						<article className="model-row" key={model.id}>
							<div className="model-row__icon"><Server size={19} /></div>
							<div className="model-row__identity"><strong>{model.id}</strong><span>{model.provider} provider</span></div>
							<span className={`tier-pill tier-pill--${model.tier.toLowerCase()}`}>{model.tier}</span>
							<span className={`availability${model.available ? " availability--ready" : ""}`}><span />{model.available ? "Available" : "Unavailable"}</span>
						</article>
					))}
				</div>
			) : (
				<div className="empty-state"><div className="empty-state__icon"><Server size={19} /></div><div><strong>{isLoading ? "Loading models" : "No models returned"}</strong><p>{error || "The gateway has not reported any configured models."}</p></div></div>
			)}
		</div>
	);
}
