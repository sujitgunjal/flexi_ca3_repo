import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
	label: string;
	value: string;
	note: string;
	icon: LucideIcon;
	accent: "green" | "blue" | "amber" | "rose" | "teal";
}

export function MetricCard({ label, value, note, icon: Icon, accent }: MetricCardProps) {
	return (
		<article className={`metric-card metric-card--${accent}`}>
			<div className="metric-card__top">
				<span className="metric-card__label">{label}</span>
				<span className="metric-card__icon"><Icon size={17} strokeWidth={1.8} /></span>
			</div>
			<strong className="metric-card__value">{value}</strong>
			<span className="metric-card__note">{note}</span>
		</article>
	);
}
