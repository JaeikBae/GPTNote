import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { ChatMessage, Memory, User } from "./types";

export default function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedMemoryId, setSelectedMemoryId] = useState<string | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listUsers()
      .then((data) => {
        setUsers(data);
        if (data.length > 0) {
          setSelectedUserId(data[0].id);
        }
      })
      .catch((err) => {
        console.error(err);
        setError("사용자 목록을 불러오지 못했습니다.");
      });
  }, []);

  useEffect(() => {
    if (!selectedUserId) {
      setMemories([]);
      setSelectedMemoryId(null);
      setSelectedMemory(null);
      return;
    }
    setError(null);
    api
      .listMemories(selectedUserId)
      .then((data) => {
        setMemories(data);
        if (data.length > 0) {
          const first = data[0];
          setSelectedMemoryId(first.id);
          loadMemory(first.id);
        } else {
          setSelectedMemoryId(null);
          setSelectedMemory(null);
        }
      })
      .catch((err) => {
        console.error(err);
        setError("기억 데이터를 불러오지 못했습니다.");
      });
  }, [selectedUserId]);

  const loadMemory = (memoryId: string) => {
    api
      .getMemory(memoryId)
      .then(setSelectedMemory)
      .catch((err) => {
        console.error(err);
        setError("선택한 기억을 불러오지 못했습니다.");
      });
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    const history = [...messages, userMessage];
    setMessages(history);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const response = await api.chat({
        message: userMessage.content,
        owner_id: selectedUserId,
        memory_ids: selectedMemoryId ? [selectedMemoryId] : undefined,
        history: messages.map((msg) => ({ role: msg.role, content: msg.content }))
      });
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.reply,
        context: response.context
      };
      setMessages([...history, assistantMessage]);
    } catch (err) {
      console.error(err);
      setError("GPT 응답을 가져오지 못했습니다.");
      setMessages(history);
    } finally {
      setLoading(false);
    }
  };

  const formattedCreatedAt = (memory: Memory) =>
    new Date(memory.created_at).toLocaleString();

  const selectedUser = useMemo(
    () => users.find((user) => user.id === selectedUserId) ?? null,
    [users, selectedUserId]
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <header>
          <h1>MindDock</h1>
          <p style={{ color: "rgba(255,255,255,0.6)", marginTop: "0.5rem" }}>
            기억 흐름을 한 눈에 보고 GPT와 바로 정리하세요.
          </p>
        </header>

        <div className="user-select">
          <label htmlFor="userSelect">사용자 선택</label>
          <select
            id="userSelect"
            value={selectedUserId ?? ""}
            onChange={(event) => setSelectedUserId(event.target.value || null)}
          >
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.full_name || user.email}
              </option>
            ))}
          </select>
        </div>

        <div className="memory-list">
          {memories.map((memory) => (
            <article
              key={memory.id}
              className={`memory-card ${
                memory.id === selectedMemoryId ? "active" : ""
              }`}
              onClick={() => {
                setSelectedMemoryId(memory.id);
                loadMemory(memory.id);
              }}
            >
              <h3>{memory.title}</h3>
              <time>{formattedCreatedAt(memory)}</time>
            </article>
          ))}

          {memories.length === 0 && (
            <p className="empty-state">
              아직 저장된 기억이 없습니다. MindDock에 첫 메모를 남겨보세요.
            </p>
          )}
        </div>
      </aside>

      <main className="main-pane">
        <section className="memory-detail">
          {selectedMemory ? (
            <>
              <header>
                <h2>{selectedMemory.title}</h2>
                <p style={{ color: "#64748b" }}>
                  {selectedUser?.full_name || selectedUser?.email} ·
                  {" "}
                  {new Date(selectedMemory.updated_at).toLocaleString()}
                </p>
              </header>

              {selectedMemory.tags && selectedMemory.tags.length > 0 && (
                <div className="tags">
                  {selectedMemory.tags.map((tag) => (
                    <span key={tag} className="tag">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}

              <article style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                {selectedMemory.content}
              </article>

              {selectedMemory.attachments && selectedMemory.attachments.length > 0 && (
                <footer style={{ marginTop: "1.5rem" }}>
                  <strong>첨부파일</strong>
                  <ul>
                    {selectedMemory.attachments.map((file) => (
                      <li key={file.id}>{file.filename}</li>
                    ))}
                  </ul>
                </footer>
              )}
            </>
          ) : (
            <p className="empty-state">좌측에서 기억을 선택해 내용을 확인하세요.</p>
          )}
        </section>

        <section className="chat-pane">
          <header style={{ marginBottom: "0.75rem" }}>
            <strong>MindDock GPT 어시스턴트</strong>
            <p style={{ color: "#64748b", margin: "0.35rem 0 0" }}>
              선택된 기억을 바탕으로 질문하고 요약을 받아보세요.
            </p>
          </header>

          <div className="chat-messages">
            {messages.map((message, index) => (
              <div key={index} className={`chat-bubble ${message.role}`}>
                {message.content}
                {message.role === "assistant" &&
                  message.context &&
                  message.context.length > 0 && (
                    <div style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
                      <strong>참고한 기억</strong>
                      <ul style={{ marginTop: "0.35rem", paddingLeft: "1.25rem" }}>
                        {message.context.map((ctx) => (
                          <li key={ctx.memory_id}>
                            <span style={{ display: "block", fontWeight: 600 }}>
                              {ctx.title}
                              {typeof ctx.score === "number"
                                ? ` · 관련도 ${ctx.score.toFixed(2)}`
                                : ""}
                            </span>
                            <span style={{ display: "block", opacity: 0.8 }}>
                              {ctx.snippet}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            ))}

            {messages.length === 0 && (
              <p className="empty-state">
                오른쪽 입력창에서 MindDock GPT에게 질문을 시작해보세요.
              </p>
            )}
          </div>

          <div className="chat-input">
            <textarea
              placeholder="예: 이 기억들을 바탕으로 실행 계획을 만들어줘"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
            />
            <button onClick={handleSend} disabled={loading}>
              {loading ? "전송중..." : "전송"}
            </button>
          </div>

          {error && (
            <p style={{ color: "#dc2626", marginTop: "0.5rem" }}>{error}</p>
          )}
        </section>
      </main>
    </div>
  );
}

