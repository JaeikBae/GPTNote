import type { AssistantResponse, Memory, User } from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || response.statusText);
  }

  return (await response.json()) as T;
}

export const api = {
  listUsers: () => request<User[]>("/users/"),
  listMemories: (ownerId: string) =>
    request<Memory[]>(`/memories/?owner_id=${encodeURIComponent(ownerId)}`),
  getMemory: (memoryId: string) =>
    request<Memory>(`/memories/${memoryId}`),
  chat: (payload: {
    message: string;
    memory_ids?: string[];
    history?: { role: string; content: string }[];
  }) =>
    request<AssistantResponse>("/assistant/chat", {
      method: "POST",
      body: JSON.stringify(payload)
    })
};

