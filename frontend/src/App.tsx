import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
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
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [newMemoryTitle, setNewMemoryTitle] = useState("");
  const [newMemoryContent, setNewMemoryContent] = useState("");
  const [newMemoryTags, setNewMemoryTags] = useState("");
  const [creatingMemory, setCreatingMemory] = useState(false);

  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioTitle, setAudioTitle] = useState("");
  const [audioTags, setAudioTags] = useState("");
  const [transcribing, setTranscribing] = useState(false);

  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [uploadingAttachment, setUploadingAttachment] = useState(false);

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

  const loadMemory = useCallback(async (memoryId: string) => {
    try {
      const memory = await api.getMemory(memoryId);
      setSelectedMemory(memory);
    } catch (err) {
      console.error(err);
      setError("선택한 기억을 불러오지 못했습니다.");
    }
  }, []);

  const fetchMemories = useCallback(
    async (userId: string, focusId?: string) => {
      try {
        const data = await api.listMemories(userId);
        setMemories(data);

        if (data.length === 0) {
          setSelectedMemoryId(null);
          setSelectedMemory(null);
          return;
        }

        const stillExists = focusId ?? selectedMemoryId;
        const candidate = stillExists && data.some((item) => item.id === stillExists)
          ? stillExists
          : data[0].id;

        setSelectedMemoryId(candidate);
        await loadMemory(candidate);
      } catch (err) {
        console.error(err);
        setError("기억 데이터를 불러오지 못했습니다.");
      }
    },
    [loadMemory, selectedMemoryId]
  );

  useEffect(() => {
    if (!selectedUserId) {
      setMemories([]);
      setSelectedMemoryId(null);
      setSelectedMemory(null);
      return;
    }
    setMessages([]);
    setStatusMessage(null);
    setError(null);
    void fetchMemories(selectedUserId);
  }, [selectedUserId, fetchMemories]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    const history = [...messages, userMessage];
    setMessages(history);
    setInput("");
    setChatLoading(true);
    setError(null);
    setStatusMessage(null);
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
      setChatLoading(false);
    }
  };

  const handleCreateMemory = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedUserId) {
      setError("메모를 생성하려면 사용자를 선택하세요.");
      return;
    }
    if (!newMemoryTitle.trim() || !newMemoryContent.trim()) {
      setError("제목과 내용을 입력해주세요.");
      return;
    }

    setError(null);
    setStatusMessage(null);
    setCreatingMemory(true);
    const tags = newMemoryTags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    try {
      const created = await api.createMemory({
        owner_id: selectedUserId,
        title: newMemoryTitle.trim(),
        content: newMemoryContent.trim(),
        tags: tags.length > 0 ? tags : undefined
      });

      setStatusMessage("새 메모가 저장되었습니다.");
      setNewMemoryTitle("");
      setNewMemoryContent("");
      setNewMemoryTags("");
      await fetchMemories(selectedUserId, created.id);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "메모 생성에 실패했습니다.");
    } finally {
      setCreatingMemory(false);
    }
  };

  const handleTranscribeAudio = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedUserId) {
      setError("오디오를 전사하려면 사용자를 선택하세요.");
      return;
    }
    if (!audioFile) {
      setError("업로드할 오디오 파일을 선택해주세요.");
      return;
    }

    const form = event.currentTarget;
    setError(null);
    setStatusMessage(null);
    setTranscribing(true);

    const tags = audioTags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    const formData = new FormData();
    formData.append("owner_id", selectedUserId);
    formData.append("file", audioFile);
    if (audioTitle.trim()) {
      formData.append("title", audioTitle.trim());
    }
    if (tags.length > 0) {
      formData.append("tags", JSON.stringify(tags));
    }

    try {
      const created = await api.createMemoryFromAudio(formData);
      setStatusMessage("오디오가 전사되어 저장되었습니다.");
      setAudioFile(null);
      setAudioTitle("");
      setAudioTags("");
      form.reset();
      await fetchMemories(selectedUserId, created.id);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "오디오 전사에 실패했습니다.");
    } finally {
      setTranscribing(false);
    }
  };

  const handleUploadAttachment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedMemoryId) {
      setError("첨부할 메모를 먼저 선택해주세요.");
      return;
    }
    if (!attachmentFile) {
      setError("업로드할 파일을 선택해주세요.");
      return;
    }

    const form = event.currentTarget;
    setError(null);
    setStatusMessage(null);
    setUploadingAttachment(true);

    const formData = new FormData();
    formData.append("file", attachmentFile);

    try {
      await api.uploadAttachment(selectedMemoryId, formData);
      setStatusMessage("첨부파일이 업로드되었습니다.");
      setAttachmentFile(null);
      form.reset();
      await loadMemory(selectedMemoryId);
      if (selectedUserId) {
        await fetchMemories(selectedUserId, selectedMemoryId);
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "첨부파일 업로드에 실패했습니다.");
    } finally {
      setUploadingAttachment(false);
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
                setStatusMessage(null);
                setError(null);
                void loadMemory(memory.id);
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
          <div className="memory-actions">
            <div className="memory-action-card">
              <h3>텍스트 메모 추가</h3>
              <form className="memory-form" onSubmit={handleCreateMemory}>
                <label className="form-field">
                  제목
                  <input
                    type="text"
                    value={newMemoryTitle}
                    onChange={(event) => setNewMemoryTitle(event.target.value)}
                    placeholder="예: 주간 회의 요약"
                    required
                  />
                </label>
                <label className="form-field">
                  내용
                  <textarea
                    value={newMemoryContent}
                    onChange={(event) => setNewMemoryContent(event.target.value)}
                    placeholder="메모 내용을 입력하세요"
                    rows={4}
                    required
                  />
                </label>
                <label className="form-field">
                  태그 (쉼표 구분)
                  <input
                    type="text"
                    value={newMemoryTags}
                    onChange={(event) => setNewMemoryTags(event.target.value)}
                    placeholder="예: 회의,요약"
                  />
                </label>
                <button type="submit" disabled={creatingMemory || !selectedUserId}>
                  {creatingMemory ? "저장중..." : "텍스트 메모 저장"}
                </button>
              </form>
            </div>

            <div className="memory-action-card">
              <h3>오디오 전사 업로드</h3>
              <form className="memory-form" onSubmit={handleTranscribeAudio}>
                <label className="form-field">
                  오디오 파일
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={(event) => setAudioFile(event.target.files?.[0] ?? null)}
                    required
                  />
                </label>
                <label className="form-field">
                  제목 (선택)
                  <input
                    type="text"
                    value={audioTitle}
                    onChange={(event) => setAudioTitle(event.target.value)}
                    placeholder="오디오 메모 제목"
                  />
                </label>
                <label className="form-field">
                  태그 (쉼표 구분, 선택)
                  <input
                    type="text"
                    value={audioTags}
                    onChange={(event) => setAudioTags(event.target.value)}
                    placeholder="예: 음성,현장"
                  />
                </label>
                <button type="submit" disabled={transcribing || !selectedUserId || !audioFile}>
                  {transcribing ? "전사중..." : "오디오 전사"}
                </button>
              </form>
            </div>

            {selectedMemoryId && (
              <div className="memory-action-card">
                <h3>선택 메모에 첨부 추가</h3>
                <form className="memory-form" onSubmit={handleUploadAttachment}>
                  <label className="form-field">
                    파일
                    <input
                      type="file"
                      onChange={(event) => setAttachmentFile(event.target.files?.[0] ?? null)}
                      required
                    />
                  </label>
                  <button type="submit" disabled={uploadingAttachment || !attachmentFile}>
                    {uploadingAttachment ? "업로드중..." : "첨부 추가"}
                  </button>
                </form>
              </div>
            )}
          </div>

          {statusMessage && <p className="status-message">{statusMessage}</p>}

          {selectedMemory ? (
            <>
              <header>
                <h2>{selectedMemory.title}</h2>
                <p style={{ color: "#64748b" }}>
                  {selectedUser?.full_name || selectedUser?.email} · {" "}
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

          {error && (
            <p style={{ color: "#dc2626", marginTop: "0.75rem" }}>{error}</p>
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
              disabled={chatLoading}
            />
            <button onClick={handleSend} disabled={chatLoading}>
              {chatLoading ? "전송중..." : "전송"}
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

