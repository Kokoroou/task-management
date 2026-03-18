# 🧠 Work State Engine (WSE)

> A **CLI-first personal workflow system** giúp bạn luôn biết:  
> ✅ *“Việc tiếp theo cần làm là gì”*  
> ✅ *“Khi nào cần quay lại việc bị quên”*  
> ✅ *“Làm sao resume mà không mất context”*

---

# 🎯 **Mục tiêu dự án**

WSE không phải là một todo app.

Nó giải quyết 3 vấn đề thực tế:

- ❌ Quên follow-up khi phụ thuộc người khác  
- ❌ Bị interrupt và mất luôn task đang làm  
- ❌ Quay lại task nhưng không biết bắt đầu từ đâu  

👉 Thay vì quản lý “danh sách việc”, WSE quản lý **trạng thái công việc (state)**.

---

# 🧠 **Core Concept**

## 🔥 **State-based workflow (quan trọng nhất)**

Mỗi task không chỉ là text, mà có **trạng thái rõ ràng**:

- `TODO` → chưa bắt đầu  
- `ACTIVE` → đang làm (chỉ có 1)  
- `INTERRUPTED` → bị chen ngang  
- `BLOCKED` → chờ external dependency  
- `DONE` → hoàn thành  

---

## ✅ **Nguyên tắc cốt lõi**

### 1. **Chỉ có 1 ACTIVE task**
→ giảm decision fatigue

---

### 2. **Interrupt phải lưu context**
→ khi bị chen ngang:
- task cũ → `INTERRUPTED`
- bắt buộc lưu `next_step`

---

### 3. **Resume không cần suy nghĩ lại**
→ mỗi task có:
```
next_step = "việc cụ thể tiếp theo"
```

---

### 4. **Side task không được giết main task**
- Task phụ → có `parent_id`
- Task chính → `BLOCKED` (chờ task phụ)

---

### 5. **Auto-resume parent**
→ Khi task con DONE:
- system tự đề xuất quay lại task cha

---

### 6. **Follow-up không bị quên**
→ Task `BLOCKED` có:
```
follow_up_at
```

→ system sẽ nhắc lại đúng lúc

---

# ⚙️ **Workflow tổng thể**

```
[Input CLI]
   ↓
[SQLite DB]
   ↓
[State Engine]
   ↓
[Next Task Selector]
   ↓
[CLI Output / Notification]
```

---

# 🧩 **Các thành phần chính**

## ⚡ **1. CLI Interface**
- `task add` → tạo task  
- `task start` → bắt đầu task  
- `task done` → hoàn thành  
- `task block` → đánh dấu blocked  
- `task next` → lấy task cần làm tiếp  

---

## 🗄️ **2. Storage (Single Source of Truth)**

- SQLite (local file)
- Không phụ thuộc dịch vụ bên ngoài
- Zero setup, zero latency

---

## 🧠 **3. State Engine**

Xử lý logic:

- Transition giữa các state
- Enforce rule (1 ACTIVE, next_step bắt buộc khi interrupt)
- Quản lý parent-child

---

## 🎯 **4. Next Task Selector**

Ưu tiên:

1. `ACTIVE`  
2. `INTERRUPTED` (mới nhất)  
3. `BLOCKED` (đến hạn follow-up)  
4. `TODO`  

👉 Output luôn là **1 task duy nhất**

---

## 🔔 **5. Follow-up Alert System**

- Chạy theo batch (30 phút)
- Chỉ alert task `BLOCKED` đến hạn
- Gom nhiều task thành 1 notification

👉 Tránh spam, không phá flow

---

# 🧱 **Data Model (simplified)**

Task gồm:

- `id`
- `title`
- `state`
- `parent_id`
- `next_step`
- `block_reason`
- `follow_up_at`
- `last_alerted_at`
- `created_at`
- `updated_at`

---

# 🔄 **Các flow quan trọng**

## ✅ **Interrupt flow**

```
Task A (ACTIVE)
   ↓ (task B xuất hiện)
Task A → INTERRUPTED + next_step
Task B → ACTIVE
```

---

## ✅ **Side task flow**

```
Task A (main)
   ↓ cần env setup
Task A → BLOCKED

Task B (side) → ACTIVE

Task B DONE
   → gợi ý resume Task A
```

---

## ✅ **Resume flow**

```
task next
→ trả về task INTERRUPTED gần nhất

+ next_step
```

---

## ✅ **Follow-up flow**

```
Task BLOCKED + follow_up_at

→ đến thời gian
→ system alert
→ đưa lại vào candidate list
```

---

# ⚖️ **Design Decisions**

## ✅ **CLI-first**
- Nhanh, ít friction
- Cross-platform (Linux / Windows / WSL)

---

## ✅ **Local-first**
- Không API
- Không sync
- Không latency

---

## ✅ **No AI (v1)**
- Không auto planning
- Không estimation

👉 Giữ system deterministic và trustable

---

## ✅ **Minimalism**
- Không dashboard
- Không kanban
- Không UI phức tạp

---

# ⚠️ **Non-goals (cố ý KHÔNG làm)**

- ❌ Không thay thế Jira / Todoist  
- ❌ Không scheduling phức tạp  
- ❌ Không time tracking  
- ❌ Không collaboration  

👉 Đây là tool cá nhân, tập trung vào **execution**, không phải management.

---

# 🧠 **Mental Model**

> Bạn không cần biết:
> - có bao nhiêu task

> Bạn chỉ cần biết:
> ✅ Task hiện tại  
> ✅ Bước tiếp theo  
> ✅ Khi nào quay lại việc khác  

---

# 🚀 **Roadmap (sau POC)**

## Phase 1 (hiện tại)
- CLI
- State machine
- Follow-up alert

---

## Phase 2 (UX)
- Global hotkey input
- Faster capture

---

## Phase 3 (Visibility)
- Overlay minimal / tmux status bar

---

## Phase 4 (Intelligence - optional)
- Suggest next task tốt hơn
- Pattern recognition (nhẹ, không AI nặng)

---

# ✅ **Success Criteria**

System thành công nếu:

- Bạn dùng liên tục **3–5 ngày**
- Không còn:
  - quên task
  - mất context khi resume
  - drift khỏi main task

---

# 💣 **Failure Modes**

- Input quá chậm → bỏ dùng  
- Không ghi `next_step` → không resume được  
- Alert spam → ignore toàn bộ  
- Over-engineer → abandon project  

---

# 📌 **Triết lý cốt lõi**

> ❗ Không tối ưu việc “lập kế hoạch”  
> ✅ Tối ưu việc “tiếp tục làm việc”  

---

# 👤 **Target User**

- Dev / DevOps / Knowledge worker
- Làm nhiều task song song
- Bị interrupt thường xuyên
- Không cần fancy UI, ưu tiên tốc độ &amp; hiệu quả

---

# 🏁 **Kết luận**

WSE không giúp bạn làm nhiều việc hơn.

Nó giúp bạn:
- **Không quên việc quan trọng**
- **Không mất thời gian reload context**
- **Luôn biết việc tiếp theo cần làm**

→ Từ đó, bạn làm việc **ít stress hơn, tập trung hơn, và ổn định hơn**.

---

# 🚀 **Cài đặt**

## Yêu cầu

- Python 3.9+
- pip

## Cài đặt

```bash
# Clone project
git clone <repo-url>
cd task-management

# Cài đặt (editable mode để phát triển)
pip install -e .

# Hoặc cài thẳng
pip install .
```

Windows — cài thêm toast notification (tuỳ chọn):

```bash
pip install "work-state-engine[windows]"
```

---

# ⚡ **Quick Start**

```bash
# Khởi tạo database (lần đầu)
task init

# Thêm task
task add "Code feature A"
task add "Fix urgent bug"

# Bắt đầu task 1
task start 1

# Bị chen ngang bởi bug → phải điền next_step
task start 2
# ▶ WSE hỏi: "Where did you leave off?"
# → nhập: "Đang viết function parse_config, dở dang ở line 42"

# Xong bug
task done 2
# ✔ Gợi ý resume task 1 (vì có parent/interrupted)

# Xem task tiếp theo
task next

# Xem danh sách
task list

# Block task đang chờ người khác
task block 1 --reason "Chờ review từ team" --follow-up "2025-03-20 09:00"
```

---

# 📋 **Tất cả commands**

| Command | Mô tả |
|---|---|
| `task init` | Khởi tạo database |
| `task add "title"` | Thêm task mới |
| `task add "title" --parent ID` | Thêm sub-task |
| `task start ID` | Bắt đầu task (auto interrupt task cũ) |
| `task start ID --next-step "..."` | Bắt đầu + ghi next_step luôn |
| `task done ID` | Hoàn thành task |
| `task block ID --reason "..."` | Đánh dấu blocked |
| `task block ID --reason "..." --follow-up "YYYY-MM-DD HH:MM"` | Blocked + đặt nhắc |
| `task next` | Xem task tiếp theo cần làm |
| `task list` | Danh sách task (bỏ DONE) |
| `task list --all` | Tất cả task kể cả DONE |
| `task show ID` | Chi tiết 1 task |
| `task check-followup` | Kiểm tra & gửi alert (dùng cho cron) |

---

# 🔔 **Cài đặt Cron / Scheduler (Follow-up Alert)**

## Linux / WSL

Thêm vào crontab (`crontab -e`):

```cron
*/30 * * * * /usr/local/bin/task check-followup
```

Nếu dùng virtual environment:

```cron
*/30 * * * * /path/to/venv/bin/task check-followup
```

Notification dùng `notify-send`. Trên WSL, cần cài thêm `wslu`:

```bash
sudo apt install libnotify-bin wslu
```

## Windows (Task Scheduler)

1. Mở **Task Scheduler** → Create Basic Task
2. Name: `WSE Follow-up Alert`
3. Trigger: Daily, repeat every **30 minutes**
4. Action: Start a program
   - Program: `task`
   - Arguments: `check-followup`
5. Finish

Notification dùng PowerShell toast (built-in) hoặc cài thêm:

```bash
pip install win10toast
```

---

# 🗂️ **Cấu trúc project**

```
task-management/
├── task_engine/
│   ├── __init__.py     # Package metadata
│   ├── models.py       # Data models (Task, TaskState)
│   ├── db.py           # SQLite layer
│   ├── service.py      # Business logic / state machine
│   ├── main.py         # Typer CLI commands
│   └── alerts.py       # Cross-platform notifications
├── pyproject.toml      # Package config & entry points
└── README.md
```

Database: `~/.task_engine.db` (SQLite, local file)