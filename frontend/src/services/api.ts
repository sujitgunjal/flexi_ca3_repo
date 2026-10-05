import type { GatewayMetrics, ModelInfo, RequestRecord } from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000")
	.replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
	let response: Response;

	try {
		response = await fetch(`${API_BASE_URL}${path}`);
	} catch {
		throw new Error(`Can't reach the gateway at ${API_BASE_URL}.`);
	}

	if (!response.ok) {
		throw new Error(`${path} returned ${response.status} ${response.statusText}.`);
	}

	return response.json() as Promise<T>;
}

export function getMetrics(): Promise<GatewayMetrics> {
	return getJson<GatewayMetrics>("/metrics");
}

export function getModels(): Promise<ModelInfo[]> {
	return getJson<ModelInfo[]>("/models");
}

export async function getRequests(): Promise<RequestRecord[]> {
	const payload: unknown = await getJson<unknown>("/requests");

	if (Array.isArray(payload)) {
		return payload as RequestRecord[];
	}

	if (payload && typeof payload === "object") {
		const records = (payload as { items?: unknown; requests?: unknown }).items
			?? (payload as { requests?: unknown }).requests;
		if (Array.isArray(records)) {
			return records as RequestRecord[];
		}
	}

	throw new Error("/requests returned an unsupported response format.");
}
