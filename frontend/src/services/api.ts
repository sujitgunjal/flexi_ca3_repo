import type { GatewayMetrics, ModelInfo, RequestRecord } from "../types";

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000")
	.replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
	let response: Response;
	try {
		response = await fetch(`${API_BASE_URL}${path}`);
	} catch (error) {
		throw new Error(`Can't reach the gateway at ${API_BASE_URL}.`, { cause: error });
	}

	if (!response.ok) {
		throw new Error(`${path} returned ${response.status} ${response.statusText}.`);
	}

	try {
		return await response.json() as T;
	} catch (error) {
		throw new Error(`${path} returned invalid JSON.`, { cause: error });
	}
}

const metricFields: (keyof GatewayMetrics)[] = [
	"total_requests",
	"cache_hits",
	"cache_misses",
	"llm_calls",
	"tokens_input",
	"tokens_output",
	"estimated_cost",
	"average_latency_ms",
	"context_reduction_percent",
	"escalations",
	"fallbacks",
];

function isGatewayMetrics(value: unknown): value is GatewayMetrics {
	return typeof value === "object"
		&& value !== null
		&& metricFields.every((field) => typeof (value as Record<string, unknown>)[field] === "number");
}

function isRequestRecord(value: unknown): value is RequestRecord {
	return typeof value === "object"
		&& value !== null
		&& ("id" in value)
		&& (typeof value.id === "number" || typeof value.id === "string");
}

export async function getMetrics(): Promise<GatewayMetrics> {
	const payload: unknown = await getJson<unknown>("/metrics");
	if (!isGatewayMetrics(payload)) {
		throw new Error("/metrics returned an unsupported response format.");
	}
	return payload;
}

export function getModels(): Promise<ModelInfo[]> {
	return getJson<ModelInfo[]>("/models");
}

export async function getRequests(): Promise<RequestRecord[]> {
	const payload: unknown = await getJson<unknown>("/requests");

	if (Array.isArray(payload)) {
		if (payload.every(isRequestRecord)) {
			return payload;
		}
	}

	if (payload && typeof payload === "object") {
		const response = payload as { items?: unknown; requests?: unknown };
		const records = response.items ?? response.requests;
		if (Array.isArray(records) && records.every(isRequestRecord)) {
			return records;
		}
	}

	throw new Error("/requests returned an unsupported response format.");
}
