export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Memory {
  id: string;
  owner_id: string;
  title: string;
  content: string;
  tags?: string[] | null;
  captured_at?: string | null;
  source_device?: string | null;
  source_location?: string | null;
  context?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  filename: string;
  content_type?: string | null;
  size_bytes?: number | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AssistantResponse {
  reply: string;
  used_memory_ids: string[];
}
