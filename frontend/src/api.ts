import type { AssistantResponse, Attachment, Memory, User } from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData;
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(options?.headers ?? {})
    }
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
  createMemory: (payload: {
    owner_id: string;
    title: string;
    content: string;
    tags?: string[];
    captured_at?: string | null;
    source_device?: string | null;
    source_location?: string | null;
    context?: Record<string, unknown> | null;
  }) =>
    request<Memory>("/memories/", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  createMemoryFromAudio: (formData: FormData) =>
    request<Memory>("/memories/transcribe", {
      method: "POST",
      body: formData
    }),
  uploadAttachment: (memoryId: string, formData: FormData) =>
    request<Attachment>(`/memories/${memoryId}/attachments`, {
      method: "POST",
      body: formData
    }),
  chat: (payload: {
    message: string;
    owner_id?: string | null;
    memory_ids?: string[];
    history?: { role: string; content: string }[];
    top_k?: number;
    use_rag?: boolean;
  }) =>
    request<AssistantResponse>("/assistant/chat", {
      method: "POST",
      body: JSON.stringify(payload)
    })
};

