# 🤖 AI Flows — Voice, Natural Language & Summaries

Three endpoints lean on external AI providers. This page documents the full
pipeline, configuration, and — most importantly — **which HTTP status each
failure produces**, so clients can branch correctly.

**Providers:** [Groq](https://console.groq.com) (chat completions) ·
[AssemblyAI](https://www.assemblyai.com) (speech-to-text)

---

## 1. Voice → task

`POST /api/tasks/create/voice` (`multipart/form-data`, field `file`)

```
audio bytes
  │  upload_audio()            app/utils/assemblyai_utils.py
  ▼
AssemblyAI /upload ──► hosted audio_url
  │  transcribe_audio()        poll ≤ 100 × 3s (bounded, never hangs a thread)
  ▼
transcript text
  │  generate_task_fields_from_llm()   app/utils/llm_utils.py
  ▼
{title, description, category, dueDate, createdFrom}
  │  TaskService.create_from_voice()
  ▼
201 + task document (createdFrom = "voice")
```

## 2. Natural language → task

`POST /api/tasks/create/natural-language` (JSON `{"prompt": "..."}`)

```
prompt ──► generate_task_fields_from_llm() ──► task fields ──► 201 + task
                    (Groq, JSON-object mode)      (createdFrom = "natural-language")
```

## 3. PDF → summary

`POST /api/summaries/create` (`multipart/form-data`, field `file`)

```
PDF bytes
  │  extract_pdf_text()        app/utils/pdf_to_text.py (PyPDF2, lazy import)
  ▼
extracted text
  │  generate_summary_from_llm()        app/utils/summary_utils.py
  ▼
4–9 summary bullets
  │  SummaryService.create()
  ▼
201 + {summary, task}   ← the `task` is a suggestion only (not persisted);
                          persist it via POST /api/summaries/<id>/convert-to-tasks
```

Subtask generation (`POST /api/subtasks/create`) also calls Groq:
task description → **3–8 ordered sub-task strings** (over-delivery is truncated
to 8; fewer than 3 is an error).

All Groq calls share one transport: `app/utils/groq_client.py`.

---

## ⚙️ Configuration

| Env var | Default | Meaning |
|---------|---------|---------|
| `KOVA_GROQ_API_KEY` | *(unset)* | Groq key — **required for all LLM flows** |
| `KOVA_ASSEMBLYAI_API_KEY` | *(unset)* | AssemblyAI key — required for voice |
| `KOVA_GROQ_LLM_URL` | Groq chat-completions URL | Override for proxies/tests |
| `KOVA_GROQ_MODEL` | `llama-3.3-70b-versatile` | Any current Groq production model |
| `KOVA_LLM_TIMEOUT_SECONDS` | `60` | Per-request Groq timeout |

---

## ❌ Failure semantics (per flow)

Every AI flow guards **before** any network I/O when a key is missing.

| Failure | Status | Body | Applies to |
|---------|--------|------|------------|
| Provider API key not configured | `503` | `{"message": "AI provider is not configured"}` | all flows |
| Groq transport/parse failure | `400` | `{"message": "API request failed: …"}` | natural-language *(legacy contract)* |
| Groq transport/parse failure | `500` | `{"message": "Internal server error"}` | voice, summary *(legacy contract)* |
| Groq transport/parse failure | `502` | `{"message": "Subtask generation failed"}` | subtasks *(fixed in Sprint D — was wrongly 404)* |
| Upload/polling failure (AssemblyAI) | `500` | `{"message": "Internal server error"}` | voice *(legacy contract)* |
| Missing `prompt` / `file` / `taskId` | `400` | endpoint-specific message | request validation |
| Task referenced by `taskId` not found | `404` | `{"message": "Task not found"}` | subtasks |

**Response validation** (all flows): malformed JSON, a non-array answer, an
out-of-range item count, or a non-string task field → the flow's failure status
above. Successful task-field responses must contain string values for `title`,
`description`, `category`, `dueDate`, and `createdFrom`.

**Rate limiting:** these routes use the standard per-IP limits
(`KOVA_RATELIMIT_*`) — see [README.md](README.md#️conventions--error-shapes).
