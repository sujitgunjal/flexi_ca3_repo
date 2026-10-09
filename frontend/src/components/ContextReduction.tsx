import { ArrowDownRight, ScanText } from "lucide-react";
import type { ContextMetrics } from "../types";

interface ContextReductionProps {
	context: ContextMetrics | null;
	isLoading: boolean;
}

const integer = new Intl.NumberFormat("en-US");

export function ContextReduction({ context, isLoading }: ContextReductionProps) {
	const hasMeasurements = context !== null && context.requests_with_metrics > 0;
	const before = context?.total_original_tokens ?? 0;
	const after = context?.total_optimized_tokens ?? 0;
	const reduction = context?.overall_reduction_percent;
	const afterWidth = before > 0 ? Math.min((after / before) * 100, 100) : 0;

	return (
		<article className="context-chart" aria-labelledby="context-chart-title">
			<div className="context-chart__heading">
				<div>
					<div className="eyebrow"><span className="eyebrow__line" />CONTEXT OPTIMIZATION</div>
					<h2 id="context-chart-title">Context reduction</h2>
				</div>
				{hasMeasurements && reduction !== null && reduction !== undefined && (
					<div className="context-chart__reduction">
						<ArrowDownRight size={17} aria-hidden="true" />
						<strong>{reduction.toFixed(1)}%</strong>
						<span>reduced</span>
					</div>
				)}
			</div>

			{hasMeasurements ? (
				<div className="context-chart__content">
					<div className="context-chart__bars" role="img" aria-label={`Context reduced from ${integer.format(before)} tokens before optimization to ${integer.format(after)} tokens after optimization`}>
						<div className="context-chart__row">
							<span className="context-chart__label">Before</span>
							<div className="context-chart__track">
								<span className="context-chart__bar context-chart__bar--before" style={{ width: "100%" }} />
							</div>
							<strong className="context-chart__value">{integer.format(before)} <span>tokens</span></strong>
						</div>
						<div className="context-chart__row">
							<span className="context-chart__label">After</span>
							<div className="context-chart__track">
								<span className="context-chart__bar context-chart__bar--after" style={{ width: `${afterWidth}%` }} />
							</div>
							<strong className="context-chart__value">{integer.format(after)} <span>tokens</span></strong>
						</div>
					</div>
					<div className="context-chart__saved">
						<ScanText size={15} aria-hidden="true" />
						<span>{integer.format(context.total_tokens_saved)} tokens removed across {integer.format(context.requests_with_metrics)} {context.requests_with_metrics === 1 ? "request" : "requests"}</span>
					</div>
				</div>
			) : (
				<div className="context-chart__empty">
					<ScanText size={19} aria-hidden="true" />
					<p>{isLoading ? "Loading context measurements…" : "Context token measurements will appear here when available."}</p>
				</div>
			)}
		</article>
	);
}