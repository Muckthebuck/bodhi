# Tool Plugin System Design

**Last Updated:** 2026-02-21  
**Status:** Design Complete  
**Target Platform:** Raspberry Pi 5 (8GB RAM, ARM64) + Client Devices

---

## 1. Overview & Philosophy

The Tool Plugin System enables the AI companion to interact with external tools, services, and resources (emails, files, calendars, APIs, physical devices) in a **secure, permission-controlled, and auditable** manner.

### Design Principles

1. **Principle of Least Privilege:** Tools get minimum permissions needed for their function
2. **Defense in Depth:** Multiple security layers (sandboxing + permissions + monitoring + audit)
3. **User Sovereignty:** User has ultimate control over all tool access
4. **Transparency:** All tool actions are logged and explainable
5. **Fail-Safe:** If uncertain, ask user rather than assume permission
6. **Context-Aware:** Host vs. Client device boundaries are respected

### Key Features

- **Pre-approved tools:** Common tools (read calendar, check email) run autonomously
- **Permission learning:** User can grant permissions and save for future
- **Risk-based approval:** High-risk actions (delete files, send money) always require approval
- **Host/Client separation:** Agent has full autonomy on host (RPi5), asks for client device actions
- **Sandbox isolation:** Critical tools in dedicated containers, others share sandboxed environment
- **AI-synthesized plugins:** Companion can create new tool integrations autonomously (with approval)

---

## 2. Tool Plugin Architecture

### 2.1 System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Tool Plugin System                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   Central Agent                                 │ │
│  │  "I need to read user's email to summarize"                    │ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Tool Plugin Manager                                │ │
│  │                                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐│ │
│  │  │  Tool        │  │ Permission   │  │  Execution           ││ │
│  │  │  Registry    │  │ Manager      │  │  Coordinator         ││ │
│  │  │              │  │              │  │                      ││ │
│  │  │ - Discover   │  │ - Check perms│  │ - Route to sandbox   ││ │
│  │  │ - Validate   │  │ - Risk assess│  │ - Monitor execution  ││ │
│  │  │ - Version    │  │ - Ask user   │  │ - Return results     ││ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘│ │
│  └───────────────────────┬────────────────────────────────────────┘ │
│                          │                                            │
│           ┌──────────────┴──────────────┐                            │
│           │                             │                            │
│           ▼                             ▼                            │
│  ┌────────────────────┐       ┌────────────────────────┐            │
│  │ Shared Sandbox     │       │ Dedicated Sandbox      │            │
│  │ (Docker Container) │       │ (Per-Critical-Tool)    │            │
│  │                    │       │                        │            │
│  │ • File ops         │       │ • Email (Gmail API)    │            │
│  │ • Calendar read    │       │ • Payment systems      │            │
│  │ • Web scraping     │       │ • SSH/system admin     │            │
│  │ • Light APIs       │       │                        │            │
│  │                    │       │ Isolation: seccomp     │            │
│  │ cgroups: 512MB RAM │       │ AppArmor profiles      │            │
│  │ No network by def  │       │ Dedicated network ns   │            │
│  └────────────────────┘       └────────────────────────┘            │
│           │                             │                            │
│           └──────────────┬──────────────┘                            │
│                          │                                            │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Audit Logger                                 │ │
│  │  Logs ALL tool invocations to PostgreSQL                       │ │
│  │  - What tool was called                                         │ │
│  │  - What parameters were passed                                  │ │
│  │  - What permission level was used                               │ │
│  │  - What result was returned                                     │ │
│  │  - User approval (if required)                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.2 Tool Plugin Types

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Tool Plugin Types                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  TYPE 1: Built-in Tools (Curated, Pre-installed)                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Email (IMAP/SMTP, Gmail API, Outlook API)                    │ │
│  │ • Calendar (CalDAV, Google Calendar, iCal)                     │ │
│  │ • File System (read, write, search, organize)                  │ │
│  │ • Web Browser (scrape, interact, automation)                   │ │
│  │ • Notifications (send, manage)                                 │ │
│  │ • System Info (CPU, memory, disk, processes)                   │ │
│  │ • Database (SQLite, PostgreSQL read-only)                      │ │
│  │ • Time & Date (schedule, reminders, timers)                    │ │
│  │                                                                 │ │
│  │ Security: Vetted, sandboxed, tested                            │ │
│  │ Maintenance: Updated with system releases                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  TYPE 2: Custom Plugins (User-Installed, Community)                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Slack/Discord bots                                            │ │
│  │ • Jira/Trello integration                                       │ │
│  │ • Smart home devices (Home Assistant, MQTT)                    │ │
│  │ • Version control (Git, GitHub API)                             │ │
│  │ • Music players (Spotify API, MPD)                              │ │
│  │ • Custom business APIs                                          │ │
│  │                                                                 │ │
│  │ Installation:                                                   │ │
│  │  1. User downloads plugin manifest (.yaml + .wasm/.py)         │ │
│  │  2. System validates signature + scans for malware             │ │
│  │  3. User reviews requested permissions                          │ │
│  │  4. Plugin installed to plugins/ directory                      │ │
│  │  5. Loaded into shared sandbox on first use                     │ │
│  │                                                                 │ │
│  │ Security: Signature verification, permission review, sandbox   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  TYPE 3: AI-Synthesized Tools (Companion-Created)                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Companion can create new tools based on:                       │ │
│  │ • User request: "I need to check my stock portfolio"           │ │
│  │ • API discovery: Companion finds Yahoo Finance API docs        │ │
│  │ • Tool synthesis: Generates Python wrapper automatically       │ │
│  │                                                                 │ │
│  │ Process:                                                        │ │
│  │  1. Companion identifies need for new capability               │ │
│  │  2. Searches for relevant APIs (web scraping, API directories) │ │
│  │  3. Generates tool plugin code (Python + manifest)             │ │
│  │  4. Tests in isolated sandbox (dry-run with mock data)         │ │
│  │  5. Presents to user:                                           │ │
│  │     "I created a 'Stock Portfolio Checker' tool.               │ │
│  │      It uses Yahoo Finance API (read-only).                     │ │
│  │      Permissions needed: network access, read config file.     │ │
│  │      [Review Code] [Approve] [Reject]"                          │ │
│  │  6. If approved, install and use                                │ │
│  │                                                                 │ │
│  │ Security:                                                       │ │
│  │ • User ALWAYS reviews generated code before approval           │ │
│  │ • Dry-run testing with mock data first                          │ │
│  │ • Sandboxed execution                                           │ │
│  │ • Limited to read-only operations initially                     │ │
│  │ • Can be upgraded to read-write with explicit permission       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Permission Management

### 3.1 Dynamic Risk-Based Permission Model

**Concept:** Instead of fixed permission tiers, assess risk dynamically based on action + context + user patterns.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Risk-Based Permission System                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Risk Score Formula:                                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ risk_score = base_risk × context_multiplier × history_factor   │ │
│  │                                                                 │ │
│  │ Where:                                                          │ │
│  │ • base_risk: Inherent risk of the action (0-1)                 │ │
│  │ • context_multiplier: Current situation (0.5-2.0)              │ │
│  │ • history_factor: User's past approvals (0.5-1.5)              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  BASE RISK LEVELS (Action-Dependent):                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │ MINIMAL RISK (0.0 - 0.2): Auto-approve                         │ │
│  │ • Read public information (weather, news)                      │ │
│  │ • Read user's calendar (view-only)                             │ │
│  │ • Check system status (CPU, disk)                              │ │
│  │ • Read email subjects (not body)                               │ │
│  │                                                                 │ │
│  │ LOW RISK (0.2 - 0.4): Auto-approve if pre-approved             │ │
│  │ • Read full email content                                      │ │
│  │ • Search files (read-only)                                     │ │
│  │ • Read browser history                                         │ │
│  │ • Create calendar events                                       │ │
│  │                                                                 │ │
│  │ MEDIUM RISK (0.4 - 0.6): Ask once, remember choice            │ │
│  │ • Send email on user's behalf                                  │ │
│  │ • Modify files (non-critical directories)                      │ │
│  │ • Post to social media                                         │ │
│  │ • Access camera/microphone                                     │ │
│  │                                                                 │ │
│  │ HIGH RISK (0.6 - 0.8): Always ask, show preview               │ │
│  │ • Delete files                                                 │ │
│  │ • Modify system settings                                       │ │
│  │ • Execute arbitrary commands                                    │ │
│  │ • Access financial accounts                                    │ │
│  │                                                                 │ │
│  │ CRITICAL RISK (0.8 - 1.0): Always ask, require confirmation   │ │
│  │ • Transfer money                                               │ │
│  │ • Delete account data                                          │ │
│  │ • Grant new permissions to tools                               │ │
│  │ • Modify security settings                                      │ │
│  │ • SSH into remote systems                                       │ │
│  │                                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  CONTEXT MULTIPLIERS:                                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • Device: Host (RPi5) = 0.5x, Client (laptop) = 1.5x          │ │
│  │           → Agent has more autonomy on host device             │ │
│  │                                                                 │ │
│  │ • User presence: Active = 0.8x, Away = 1.2x, Offline = 2.0x   │ │
│  │           → More cautious when user is away                    │ │
│  │                                                                 │ │
│  │ • Time: Work hours = 1.0x, Off-hours = 1.3x                    │ │
│  │           → More scrutiny during unusual times                 │ │
│  │                                                                 │ │
│  │ • Data sensitivity: Public = 0.8x, Personal = 1.2x, Secret =  │ │
│  │   2.0x                                                          │ │
│  │           → Higher caution with sensitive data                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  HISTORY FACTOR (Pattern Learning):                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ • If user has approved this action 10+ times: 0.5x            │ │
│  │   → "User always lets me check email in morning"              │ │
│  │                                                                 │ │
│  │ • If user rejected this action before: 1.5x                    │ │
│  │   → "User doesn't like me modifying files in ~/Documents"     │ │
│  │                                                                 │ │
│  │ • First time action: 1.0x (neutral)                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 Permission Decision Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Permission Decision Process                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Example: Companion wants to "Send email to John about meeting"      │
│                                                                       │
│  STEP 1: Calculate Risk Score                                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ base_risk = 0.5 (send email = MEDIUM RISK)                     │ │
│  │                                                                 │ │
│  │ Context:                                                        │ │
│  │ • Device: Client laptop (multiplier = 1.5x)                    │ │
│  │ • User presence: Active (multiplier = 0.8x)                    │ │
│  │ • Time: 10am work hours (multiplier = 1.0x)                    │ │
│  │ context_multiplier = 1.5 × 0.8 × 1.0 = 1.2                     │ │
│  │                                                                 │ │
│  │ History:                                                        │ │
│  │ • User has approved "send email" 15 times before               │ │
│  │ history_factor = 0.5 (established pattern)                     │ │
│  │                                                                 │ │
│  │ risk_score = 0.5 × 1.2 × 0.5 = 0.30                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 2: Decision Logic                                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │ risk_score = 0.30 (LOW RISK range)                             │ │
│  │                                                                 │ │
│  │ Decision tree:                                                  │ │
│  │ IF risk_score < 0.2:                                            │ │
│  │   → AUTO-APPROVE (no user interaction)                          │ │
│  │                                                                 │ │
│  │ ELIF risk_score < 0.4:                                          │ │
│  │   → Check if pre-approved:                                      │ │
│  │       IF tool has "send_email" permission saved:                │ │
│  │         → AUTO-APPROVE ✓                                        │ │
│  │       ELSE:                                                      │ │
│  │         → ASK USER (with "Remember this choice" option)         │ │
│  │                                                                 │ │
│  │ ELIF risk_score < 0.6:                                          │ │
│  │   → ASK USER with preview                                       │ │
│  │                                                                 │ │
│  │ ELIF risk_score < 0.8:                                          │ │
│  │   → ASK USER with detailed preview + consequences               │ │
│  │                                                                 │ │
│  │ ELSE: # risk_score >= 0.8                                       │ │
│  │   → ASK USER with confirmation + 2FA if enabled                 │ │
│  │                                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          │ risk_score=0.30 → Check pre-approval      │
│                          ▼                                            │
│  STEP 3: Check Saved Permissions                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Query PostgreSQL:                                               │ │
│  │   SELECT * FROM tool_permissions                                │ │
│  │   WHERE user_id = $1                                            │ │
│  │     AND tool_id = 'email_plugin'                                │ │
│  │     AND capability = 'send_email'                               │ │
│  │     AND scope = 'work_contacts'  -- Optional scope filter      │ │
│  │                                                                 │ │
│  │ Result: Permission found, granted 2 weeks ago                   │ │
│  │ → AUTO-APPROVE ✓                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│                          ▼                                            │
│  STEP 4: Execute (If Approved)                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Execution:                                                      │ │
│  │   tool_executor.execute(                                        │ │
│  │     tool='email_plugin',                                        │ │
│  │     action='send',                                              │ │
│  │     params={                                                    │ │
│  │       'to': 'john@example.com',                                 │ │
│  │       'subject': 'Meeting Reminder',                            │ │
│  │       'body': 'Hi John, ...'                                    │ │
│  │     }                                                            │ │
│  │   )                                                              │ │
│  │                                                                 │ │
│  │ Audit Log:                                                      │ │
│  │   {                                                              │ │
│  │     'timestamp': '2026-02-21T10:30:00Z',                        │ │
│  │     'tool': 'email_plugin',                                     │ │
│  │     'action': 'send_email',                                     │ │
│  │     'risk_score': 0.30,                                         │ │
│  │     'approval': 'auto_approved',                                │ │
│  │     'params': {...},                                            │ │
│  │     'result': 'success'                                         │ │
│  │   }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ALTERNATIVE: If Not Pre-Approved                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Show user prompt:                                               │ │
│  │ ┌────────────────────────────────────────────────────────────┐│ │
│  │ │ 📧 Permission Request                                       ││ │
│  │ │                                                             ││ │
│  │ │ Your companion wants to:                                    ││ │
│  │ │ Send email to john@example.com                              ││ │
│  │ │                                                             ││ │
│  │ │ Subject: "Meeting Reminder"                                 ││ │
│  │ │ Preview: "Hi John, just a reminder about our meeting..."    ││ │
│  │ │                                                             ││ │
│  │ │ Risk Level: LOW (0.30)                                      ││ │
│  │ │                                                             ││ │
│  │ │ ☐ Remember this choice                                      ││ │
│  │ │   (Allow sending emails to work contacts)                   ││ │
│  │ │                                                             ││ │
│  │ │ [Approve] [Deny] [View Full Email]                         ││ │
│  │ └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │ If user clicks "Approve" + "Remember":                          │ │
│  │   → Execute action                                              │ │
│  │   → Save permission to database                                 │ │
│  │   → Future similar requests auto-approved                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.3 Host vs. Client Device Permissions

```
┌──────────────────────────────────────────────────────────────────────┐
│               Host (RPi5) vs. Client Device Separation                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  HOST DEVICE (Raspberry Pi 5):                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Companion has broad autonomy                                    │ │
│  │                                                                 │ │
│  │ Pre-approved actions (no user prompt):                          │ │
│  │ • Read/write to /home/companion/ directory                      │ │
│  │ • Manage system resources (CPU, memory)                         │ │
│  │ • Install/update own dependencies                               │ │
│  │ • Access databases (PostgreSQL, Redis, Neo4j, Qdrant)          │ │
│  │ • Network access for API calls                                  │ │
│  │ • Schedule tasks (cron-like)                                    │ │
│  │ • Manage logs                                                   │ │
│  │                                                                 │ │
│  │ Still requires approval:                                        │ │
│  │ • Modify system config files outside /home/companion/           │ │
│  │ • Open new ports (firewall changes)                             │ │
│  │ • SSH into external systems                                     │ │
│  │                                                                 │ │
│  │ Permission setting: User can grant "full host autonomy" mode   │ │
│  │   → Companion can self-maintain without interrupting user      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  CLIENT DEVICES (Laptop, Phone, Desktop):                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Companion has limited autonomy (user's personal device)         │ │
│  │                                                                 │ │
│  │ Requires explicit permission:                                   │ │
│  │ • Read files from user's file system                            │ │
│  │ • Capture screenshots                                           │ │
│  │ • Access camera/microphone                                      │ │
│  │ • Modify files                                                  │ │
│  │ • Send emails/messages on user's behalf                         │ │
│  │ • Control applications (automation)                             │ │
│  │                                                                 │ │
│  │ Only pre-approved:                                              │ │
│  │ • Display notifications                                         │ │
│  │ • Show on-screen character (if opted in)                        │ │
│  │ • Read system time/date                                         │ │
│  │                                                                 │ │
│  │ Client agent architecture:                                      │ │
│  │ ┌────────────────────────────────────────────────────────────┐│ │
│  │ │ Thin client installed on user's device:                    ││ │
│  │ │                                                             ││ │
│  │ │ - Communicates with host (RPi5) over mTLS                  ││ │
│  │ │ - Executes ONLY actions user has approved                  ││ │
│  │ │ - Shows permission prompts in UI                            ││ │
│  │ │ - Cannot act without explicit user confirmation             ││ │
│  │ │ - Logs all actions locally for user review                  ││ │
│  │ └────────────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  CROSS-DEVICE ACTION FLOW:                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │ Scenario: Companion (on RPi5) wants to screenshot user's       │ │
│  │           laptop to answer "What's on my screen?"               │ │
│  │                                                                 │ │
│  │ Step 1: Host agent (RPi5) sends request to client agent        │ │
│  │   {                                                             │ │
│  │     'action': 'capture_screenshot',                             │ │
│  │     'reason': 'User asked what is on screen',                   │ │
│  │     'risk_score': 0.45                                          │ │
│  │   }                                                              │ │
│  │                                                                 │ │
│  │ Step 2: Client agent (laptop) checks permissions               │ │
│  │   - No saved permission for screenshot                          │ │
│  │   - risk_score = 0.45 (MEDIUM) → Show prompt                   │ │
│  │                                                                 │ │
│  │ Step 3: User sees notification on laptop                        │ │
│  │   ┌───────────────────────────────────────────────────────┐   │ │
│  │   │ 🤖 Companion Request                                   │   │ │
│  │   │                                                         │   │ │
│  │   │ Wants to: Capture screenshot                           │   │ │
│  │   │ Reason: You asked "What's on my screen?"               │   │ │
│  │   │                                                         │   │ │
│  │   │ ☐ Allow this once                                      │   │ │
│  │   │ ☐ Always allow screenshots (when I ask)                │   │ │
│  │   │                                                         │   │ │
│  │   │ [Approve] [Deny]                                        │   │ │
│  │   └───────────────────────────────────────────────────────┘   │ │
│  │                                                                 │ │
│  │ Step 4: User clicks "Approve" + "Always allow when I ask"      │ │
│  │   - Client captures screenshot                                  │ │
│  │   - Sends to host agent over mTLS                               │ │
│  │   - Saves permission for future                                 │ │
│  │                                                                 │ │
│  │ Step 5: Host agent processes screenshot and responds to user   │ │
│  │   "I see you have an email client open with 3 unread emails."  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 4. Sandbox Isolation

### 4.1 Hybrid Sandboxing Strategy

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Sandbox Architecture                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  SHARED SANDBOX (Docker Container)                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Name: companion-tools-shared                                    │ │
│  │                                                                 │ │
│  │ Resource Limits:                                                │ │
│  │ • Memory: 512 MB (cgroups)                                      │ │
│  │ • CPU: 1 core (25% of RPi5 total)                              │ │
│  │ • Disk: 1 GB tmpfs (ephemeral)                                 │ │
│  │ • Network: Disabled by default                                  │ │
│  │   (enable per-tool if needed via --network flag)                │ │
│  │                                                                 │ │
│  │ Security:                                                       │ │
│  │ • seccomp profile: Blocks dangerous syscalls                   │ │
│  │   (e.g., mount, reboot, kernel module loading)                 │ │
│  │ • AppArmor profile: Restricts file access                      │ │
│  │   Read-only: /usr, /lib, /etc                                  │ │
│  │   Read-write: /tmp, /var/run/tools                             │ │
│  │   No access: /home (host), /root                                │ │
│  │ • No privileged mode                                            │ │
│  │ • Drop all capabilities except CAP_NET_BIND_SERVICE            │ │
│  │                                                                 │ │
│  │ Tools in shared sandbox:                                        │ │
│  │ • File operations (read, write, search)                         │ │
│  │ • Calendar read/write                                           │ │
│  │ • Web scraping (BeautifulSoup, requests)                        │ │
│  │ • Light APIs (REST clients)                                     │ │
│  │ • Database queries (read-only)                                  │ │
│  │ • Text processing utilities                                     │ │
│  │                                                                 │ │
│  │ Execution:                                                      │ │
│  │   docker run --rm \                                             │ │
│  │     --name companion-tools-shared \                             │ │
│  │     --memory=512m \                                             │ │
│  │     --cpus=1.0 \                                                │ │
│  │     --tmpfs /tmp:rw,size=1g \                                   │ │
│  │     --security-opt seccomp=seccomp-profile.json \               │ │
│  │     --security-opt apparmor=companion-tools \                   │ │
│  │     --cap-drop=ALL \                                            │ │
│  │     --network=none \                                            │ │
│  │     -v /path/to/tools:/tools:ro \                               │ │
│  │     companion/tools-shared:latest \                             │ │
│  │     python3 /tools/executor.py $TOOL_NAME $PARAMS               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  DEDICATED SANDBOXES (Per Critical Tool)                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Critical tools get isolated containers                          │ │
│  │                                                                 │ │
│  │ Example 1: Email Plugin (Gmail API)                             │ │
│  │ ┌────────────────────────────────────────────────────────────┐│ │
│  │ │ Name: companion-tool-email                                  ││ │
│  │ │                                                             ││ │
│  │ │ Why dedicated:                                              ││ │
│  │ │ • Handles sensitive data (email content, credentials)      ││ │
│  │ │ • Needs network access (Gmail API)                         ││ │
│  │ │ • High risk if compromised                                  ││ │
│  │ │                                                             ││ │
│  │ │ Security:                                                   ││ │
│  │ │ • Dedicated network namespace                               ││ │
│  │ │ • Outbound only to gmail.com (iptables whitelist)          ││ │
│  │ │ • Encrypted credential storage (libsecret)                  ││ │
│  │ │ • OAuth tokens stored in encrypted volume                   ││ │
│  │ │ • Stricter seccomp profile                                  ││ │
│  │ │                                                             ││ │
│  │ │ Resource limits:                                            ││ │
│  │ │ • Memory: 256 MB                                            ││ │
│  │ │ • CPU: 0.5 core                                             ││ │
│  │ └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │ Example 2: Payment Plugin (Stripe API)                          │ │
│  │ ┌────────────────────────────────────────────────────────────┐│ │
│  │ │ Name: companion-tool-payment                                ││ │
│  │ │                                                             ││ │
│  │ │ Why dedicated:                                              ││ │
│  │ │ • CRITICAL: Handles financial transactions                 ││ │
│  │ │ • Requires maximum isolation                                ││ │
│  │ │                                                             ││ │
│  │ │ Security:                                                   ││ │
│  │ │ • All of above, plus:                                       ││ │
│  │ │ • Audit logging to separate immutable log                   ││ │
│  │ │ • 2FA required for all transactions                         ││ │
│  │ │ • Transaction preview always shown to user                  ││ │
│  │ │ • Rate limiting (max 5 transactions/hour)                   ││ │
│  │ └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │ Example 3: SSH/System Admin Plugin                              │ │
│  │ ┌────────────────────────────────────────────────────────────┐│ │
│  │ │ Name: companion-tool-ssh                                    ││ │
│  │ │                                                             ││ │
│  │ │ Why dedicated:                                              ││ │
│  │ │ • Can execute arbitrary commands on remote systems         ││ │
│  │ │ • Needs SSH key access                                      ││ │
│  │ │                                                             ││ │
│  │ │ Security:                                                   ││ │
│  │ │ • SSH keys stored in encrypted volume                       ││ │
│  │ │ • Command whitelist (only allow approved commands)          ││ │
│  │ │ • User approves EVERY command before execution              ││ │
│  │ │ • Full transcript logged                                    ││ │
│  │ └────────────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  DECISION LOGIC: Shared vs. Dedicated                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │ Use DEDICATED sandbox if ANY of:                                │ │
│  │ • base_risk > 0.6 (HIGH or CRITICAL risk actions)             │ │
│  │ • Handles credentials or tokens                                 │ │
│  │ • Requires network access                                       │ │
│  │ • Can modify sensitive data (files, emails, financial)         │ │
│  │ • User marks as "critical" in settings                          │ │
│  │                                                                 │ │
│  │ Use SHARED sandbox otherwise (most tools)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 4.2 Seccomp Profile (Syscall Filtering)

```yaml
# seccomp-profile.json - Blocks dangerous system calls
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close", "stat", "fstat",
        "lstat", "poll", "lseek", "mmap", "mprotect", "munmap",
        "brk", "ioctl", "access", "socket", "connect", "accept",
        "sendto", "recvfrom", "bind", "listen", "getsockopt",
        "setsockopt", "clone", "fork", "execve", "exit",
        "wait4", "kill", "uname", "getcwd", "getuid", "getgid"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": [
        "mount", "umount", "reboot", "swapon", "swapoff",
        "init_module", "delete_module", "kexec_load",
        "ptrace", "acct", "chroot", "pivot_root"
      ],
      "action": "SCMP_ACT_ERRNO",
      "comment": "Block privileged operations"
    }
  ]
}
```

### 4.3 AppArmor Profile (File Access Control)

```
# /etc/apparmor.d/companion-tools
#include <tunables/global>

profile companion-tools flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/python>

  # Allow reading tools
  /tools/** r,

  # Allow writing to temp
  /tmp/** rw,
  /var/run/tools/** rw,

  # Deny everything else
  deny /home/** rwx,
  deny /root/** rwx,
  deny /etc/shadow r,
  deny /etc/passwd w,

  # Network (if enabled)
  network inet stream,
  network inet6 stream,

  # No capability escalation
  deny capability setuid,
  deny capability setgid,
  deny capability sys_admin,
  deny capability sys_boot,
  deny capability sys_module,
}
```

---

## 5. Tool Plugin Interface

### 5.1 Plugin Manifest Format

Every tool plugin must include a manifest file describing its capabilities, permissions, and metadata.

```yaml
# plugin-manifest.yaml - Example for Email Plugin

plugin:
  id: email_plugin_gmail
  name: "Gmail Email Integration"
  version: "1.2.0"
  author: "Bodhi Team"
  description: "Read and send emails via Gmail API"
  
  # Plugin type
  type: built-in  # Options: built-in, custom, ai-synthesized
  
  # Signature (for custom plugins)
  signature: "SHA256:a3f2c8e7..."  # Digital signature
  
  # Runtime environment
  runtime:
    type: python  # Options: python, wasm, docker, binary
    version: "3.11"
    entrypoint: "email_plugin.py"
    sandbox: dedicated  # Options: shared, dedicated
  
  # Required permissions
  permissions:
    - id: read_email
      description: "Read email content"
      risk_level: 0.3  # LOW
      default: allow  # Options: allow, ask, deny
      
    - id: send_email
      description: "Send email on user's behalf"
      risk_level: 0.5  # MEDIUM
      default: ask
      scope:  # Optional: limit scope
        - type: recipient
          whitelist: ["work_contacts", "family"]
      
    - id: delete_email
      description: "Delete emails"
      risk_level: 0.7  # HIGH
      default: deny
      requires_confirmation: true
    
    - id: network_access
      description: "Access Gmail API"
      destinations: ["gmail.com", "googleapis.com"]
      risk_level: 0.4
      default: allow
  
  # Capabilities exposed to companion
  capabilities:
    - name: list_emails
      description: "List emails in inbox"
      parameters:
        - name: folder
          type: string
          default: "INBOX"
          required: false
        - name: limit
          type: integer
          default: 50
          max: 200
      returns: array<email_object>
      
    - name: send_email
      description: "Send an email"
      parameters:
        - name: to
          type: email_address
          required: true
        - name: subject
          type: string
          required: true
        - name: body
          type: string
          required: true
        - name: attachments
          type: array<file_path>
          required: false
      returns: email_id
      
    - name: search_emails
      description: "Search emails by query"
      parameters:
        - name: query
          type: string
          required: true
        - name: limit
          type: integer
          default: 20
      returns: array<email_object>
  
  # Resource limits (for shared sandbox)
  resources:
    max_memory_mb: 128
    max_cpu_percent: 20
    max_execution_time_sec: 30
    max_network_kb_per_sec: 1024
  
  # Dependencies
  dependencies:
    python:
      - google-api-python-client==2.70.0
      - google-auth==2.16.0
    system:
      - libsecret  # For credential storage
  
  # Configuration (user-editable)
  config:
    - key: oauth_credentials_path
      description: "Path to OAuth credentials JSON"
      type: file_path
      default: "/home/companion/secrets/gmail_oauth.json"
      encrypted: true
    
    - key: max_emails_per_hour
      description: "Rate limit for sending emails"
      type: integer
      default: 50
      min: 1
      max: 200
  
  # Audit settings
  audit:
    log_all_calls: true
    sensitive_params: ["body", "attachments"]  # Redacted in logs
    retention_days: 90
```

### 5.2 Plugin Implementation (Python Example)

```python
# email_plugin.py - Gmail plugin implementation

import json
import sys
from typing import Dict, List, Any
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class EmailPlugin:
    """Gmail email integration plugin."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize plugin with config from manifest."""
        self.config = config
        self.creds = self._load_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
    
    def _load_credentials(self) -> Credentials:
        """Load OAuth credentials from encrypted storage."""
        creds_path = self.config['oauth_credentials_path']
        # In production, decrypt using libsecret or similar
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        return Credentials.from_authorized_user_info(creds_data)
    
    # ===== Capability: list_emails =====
    
    def list_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List emails in specified folder."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=[folder],
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                email_data = self._fetch_email_details(msg['id'])
                emails.append(email_data)
            
            return emails
        
        except Exception as e:
            return {'error': str(e)}
    
    def _fetch_email_details(self, msg_id: str) -> Dict[str, Any]:
        """Fetch details for a single email."""
        msg = self.service.users().messages().get(
            userId='me',
            id=msg_id,
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()
        
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        
        return {
            'id': msg_id,
            'from': headers.get('From'),
            'to': headers.get('To'),
            'subject': headers.get('Subject'),
            'date': headers.get('Date'),
            'snippet': msg.get('snippet'),
            'labels': msg.get('labelIds', [])
        }
    
    # ===== Capability: send_email =====
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: List[str] = None
    ) -> str:
        """Send an email."""
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import base64
            
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            message.attach(MIMEText(body, 'plain'))
            
            # Handle attachments
            if attachments:
                for filepath in attachments:
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={filepath.split("/")[-1]}'
                    )
                    message.attach(part)
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return result['id']
        
        except Exception as e:
            return {'error': str(e)}
    
    # ===== Capability: search_emails =====
    
    def search_emails(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search emails by query string."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                email_data = self._fetch_email_details(msg['id'])
                emails.append(email_data)
            
            return emails
        
        except Exception as e:
            return {'error': str(e)}


# ===== Plugin Executor (Entry Point) =====

def main():
    """Entry point for plugin execution."""
    # Parse command-line arguments
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Usage: python email_plugin.py <capability> <params_json>'}))
        sys.exit(1)
    
    capability = sys.argv[1]
    params_json = sys.argv[2]
    params = json.loads(params_json)
    
    # Load config (passed via environment or file)
    import os
    config_path = os.environ.get('PLUGIN_CONFIG', '/tmp/plugin_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Initialize plugin
    plugin = EmailPlugin(config)
    
    # Execute capability
    if hasattr(plugin, capability):
        result = getattr(plugin, capability)(**params)
        print(json.dumps(result))
    else:
        print(json.dumps({'error': f'Unknown capability: {capability}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### 5.3 Tool Executor (Companion Side)

```python
# tool_executor.py - Executes tools in sandbox

import asyncio
import json
import subprocess
from typing import Dict, Any, Optional

class ToolExecutor:
    """Executes tool plugins in sandboxed environments."""
    
    def __init__(self, registry: 'ToolRegistry', permission_mgr: 'PermissionManager'):
        self.registry = registry
        self.permission_mgr = permission_mgr
    
    async def execute(
        self,
        tool_id: str,
        capability: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a tool capability."""
        # Step 1: Validate tool exists
        tool = await self.registry.get_tool(tool_id)
        if not tool:
            return {'error': f'Tool not found: {tool_id}'}
        
        # Step 2: Validate capability exists
        cap_def = tool.get_capability(capability)
        if not cap_def:
            return {'error': f'Capability not found: {capability}'}
        
        # Step 3: Check permissions
        permission_result = await self.permission_mgr.check_permission(
            tool_id=tool_id,
            capability=capability,
            params=params,
            context=context or {}
        )
        
        if permission_result['status'] == 'denied':
            return {'error': 'Permission denied', 'reason': permission_result['reason']}
        
        if permission_result['status'] == 'approval_required':
            # Show user prompt
            user_decision = await self._request_user_approval(
                tool_id, capability, params, permission_result
            )
            
            if not user_decision['approved']:
                return {'error': 'User denied permission'}
            
            # Save permission if requested
            if user_decision.get('remember'):
                await self.permission_mgr.save_permission(
                    tool_id, capability, user_decision['scope']
                )
        
        # Step 4: Execute in sandbox
        result = await self._execute_in_sandbox(tool, capability, params)
        
        # Step 5: Audit log
        await self._log_execution(tool_id, capability, params, result, permission_result)
        
        return result
    
    async def _execute_in_sandbox(
        self,
        tool: 'Tool',
        capability: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool in appropriate sandbox."""
        # Prepare sandbox based on tool manifest
        if tool.manifest['runtime']['sandbox'] == 'dedicated':
            sandbox_name = f"companion-tool-{tool.id}"
        else:
            sandbox_name = "companion-tools-shared"
        
        # Prepare config file
        config_path = f"/tmp/plugin_config_{tool.id}.json"
        with open(config_path, 'w') as f:
            json.dump(tool.config, f)
        
        # Build Docker command
        docker_cmd = [
            'docker', 'run', '--rm',
            '--name', sandbox_name,
            '--memory', f"{tool.manifest['resources']['max_memory_mb']}m",
            '--cpus', str(tool.manifest['resources']['max_cpu_percent'] / 100),
            '--security-opt', 'seccomp=seccomp-profile.json',
            '--security-opt', 'apparmor=companion-tools',
            '--cap-drop', 'ALL',
            '--network', 'none' if not tool.needs_network() else 'bridge',
            '-v', f'{config_path}:/tmp/plugin_config.json:ro',
            '-v', f'/path/to/tools/{tool.id}:/tools:ro',
            '-e', 'PLUGIN_CONFIG=/tmp/plugin_config.json',
            f'companion/tool-{tool.id}:latest',
            'python3', f'/tools/{tool.manifest["runtime"]["entrypoint"]}',
            capability,
            json.dumps(params)
        ]
        
        # Execute with timeout
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=tool.manifest['resources']['max_execution_time_sec']
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {'error': f'Execution failed: {result.stderr}'}
        
        except subprocess.TimeoutExpired:
            return {'error': 'Execution timeout'}
        except json.JSONDecodeError:
            return {'error': 'Invalid JSON response from tool'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}
    
    async def _request_user_approval(
        self,
        tool_id: str,
        capability: str,
        params: Dict[str, Any],
        permission_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request user approval via UI."""
        # Send approval request to client UI
        approval_request = {
            'type': 'permission_request',
            'tool_id': tool_id,
            'capability': capability,
            'params': params,
            'risk_score': permission_result['risk_score'],
            'risk_level': permission_result['risk_level'],
            'preview': self._generate_preview(tool_id, capability, params)
        }
        
        # Wait for user response (via Redis Pub/Sub or WebSocket)
        response = await self._wait_for_user_response(approval_request)
        
        return response
    
    def _generate_preview(
        self,
        tool_id: str,
        capability: str,
        params: Dict[str, Any]
    ) -> str:
        """Generate human-readable preview of action."""
        if tool_id == 'email_plugin_gmail' and capability == 'send_email':
            return (
                f"Send email to {params['to']}\n"
                f"Subject: {params['subject']}\n"
                f"Preview: {params['body'][:100]}..."
            )
        elif tool_id == 'file_tool' and capability == 'delete_file':
            return f"Delete file: {params['path']}"
        else:
            return f"Execute {tool_id}.{capability} with params: {json.dumps(params)}"
    
    async def _log_execution(
        self,
        tool_id: str,
        capability: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        permission_result: Dict[str, Any]
    ):
        """Log tool execution to audit log."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tool_id': tool_id,
            'capability': capability,
            'params': self._redact_sensitive(tool_id, params),
            'result_status': 'success' if 'error' not in result else 'error',
            'risk_score': permission_result['risk_score'],
            'approval_status': permission_result['status'],
        }
        
        await self.db.execute("""
            INSERT INTO tool_execution_log
            (timestamp, tool_id, capability, params, result_status, risk_score, approval_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, *log_entry.values())
    
    def _redact_sensitive(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive parameters before logging."""
        tool = self.registry.get_tool_sync(tool_id)
        sensitive = tool.manifest['audit'].get('sensitive_params', [])
        
        redacted = params.copy()
        for key in sensitive:
            if key in redacted:
                redacted[key] = '[REDACTED]'
        
        return redacted
```

---

## 6. AI-Synthesized Tool Creation

### 6.1 Autonomous Tool Synthesis Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│             AI-Synthesized Tool Creation Process                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Trigger: User asks "Check my stock portfolio value"                 │
│           Companion has no "stock_portfolio" tool                     │
│                                                                       │
│  STEP 1: Identify Need                                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Central Agent: "I need capability to check stock prices"        │ │
│  │                                                                 │ │
│  │ Query Tool Registry: search("stock", "portfolio", "finance")    │ │
│  │ Result: No matching tools found                                 │ │
│  │                                                                 │ │
│  │ Decision: Attempt to synthesize new tool                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 2: API Discovery                                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Search for relevant APIs:                                       │ │
│  │ 1. Check curated API directory (RapidAPI, ProgrammableWeb)     │ │
│  │ 2. Web search: "stock price API free"                           │ │
│  │ 3. Check API documentation databases                            │ │
│  │                                                                 │ │
│  │ Found APIs:                                                     │ │
│  │ • Yahoo Finance API (free, no auth required)                    │ │
│  │ • Alpha Vantage API (free tier, API key needed)                 │ │
│  │ • IEX Cloud API (paid)                                          │ │
│  │                                                                 │ │
│  │ Select: Yahoo Finance API (simplest, no auth, free)             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 3: API Analysis                                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Scrape API documentation:                                       │ │
│  │ URL: https://www.yahoofinanceapi.com/docs                       │ │
│  │                                                                 │ │
│  │ Extract:                                                        │ │
│  │ • Endpoint: GET https://api.yahoofinance.com/v1/quote          │ │
│  │ • Parameters: symbol (required), range, interval                │ │
│  │ • Response format: JSON with price, change, volume              │ │
│  │ • Rate limits: 100 requests/hour                                │ │
│  │ • Authentication: None (public API)                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 4: Code Generation                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ LLM Prompt:                                                     │ │
│  │ "Generate a Python plugin for the Bodhi tool system     │ │
│  │  that fetches stock prices using Yahoo Finance API.            │ │
│  │  Endpoint: GET https://api.yahoofinance.com/v1/quote           │ │
│  │  Parameters: symbol (stock ticker), range, interval            │ │
│  │  Follow plugin template in email_plugin.py                      │ │
│  │  Include manifest YAML and Python implementation."              │ │
│  │                                                                 │ │
│  │ Generated files:                                                │ │
│  │ • plugin-manifest.yaml (with capabilities, permissions)         │ │
│  │ • stock_plugin.py (Python implementation)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 5: Dry-Run Testing                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Test in isolated sandbox with mock data:                       │ │
│  │                                                                 │ │
│  │ Test 1: get_stock_price('AAPL')                                 │ │
│  │   → Expected: {'symbol': 'AAPL', 'price': 150.25, ...}        │ │
│  │   → Result: ✓ Success                                           │ │
│  │                                                                 │ │
│  │ Test 2: get_stock_price('INVALID_SYMBOL')                       │ │
│  │   → Expected: Error handling                                    │ │
│  │   → Result: ✓ Returns {'error': 'Invalid symbol'}              │ │
│  │                                                                 │ │
│  │ Test 3: Rate limit handling                                     │ │
│  │   → Expected: Graceful failure after 100 requests               │ │
│  │   → Result: ✓ Returns rate limit error                          │ │
│  │                                                                 │ │
│  │ All tests passed ✓                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 6: Present to User                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ UI Notification:                                                │ │
│  │ ┌────────────────────────────────────────────────────────────┐│ │
│  │ │ 🤖 New Tool Created                                         ││ │
│  │ │                                                             ││ │
│  │ │ I created a "Stock Price Checker" tool to answer your      ││ │
│  │ │ question about your portfolio.                              ││ │
│  │ │                                                             ││ │
│  │ │ Details:                                                    ││ │
│  │ │ • Uses: Yahoo Finance API (free, public)                   ││ │
│  │ │ • Capabilities: Get stock price, get portfolio value       ││ │
│  │ │ • Permissions needed:                                       ││ │
│  │ │   - Network access (api.yahoofinance.com)                  ││ │
│  │ │   - Read config file (your stock tickers)                  ││ │
│  │ │ • Risk level: LOW (read-only, no auth required)            ││ │
│  │ │                                                             ││ │
│  │ │ [Review Code] [Approve & Install] [Reject]                 ││ │
│  │ └────────────────────────────────────────────────────────────┘│ │
│  │                                                                 │ │
│  │ User clicks "Review Code":                                      │ │
│  │ • Shows generated plugin-manifest.yaml                          │ │
│  │ • Shows stock_plugin.py with syntax highlighting               │ │
│  │ • Shows test results                                            │ │
│  │ • Highlights permissions and network endpoints                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 7: User Approval & Installation                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ User clicks "Approve & Install"                                 │ │
│  │                                                                 │ │
│  │ 1. Copy files to plugins/stock_plugin/                          │ │
│  │ 2. Register in Tool Registry                                    │ │
│  │ 3. Build Docker image (if dedicated sandbox needed)             │ │
│  │ 4. Grant approved permissions                                   │ │
│  │ 5. Mark as "ai-synthesized" for extra monitoring                │ │
│  │                                                                 │ │
│  │ Confirmation: "Stock Price Checker installed successfully!"     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          │                                            │
│  STEP 8: Execute Original Request                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Now companion can answer original question:                     │ │
│  │                                                                 │ │
│  │ User: "Check my stock portfolio value"                          │ │
│  │                                                                 │ │
│  │ Companion:                                                      │ │
│  │ • Reads portfolio config (e.g., AAPL: 10 shares, TSLA: 5)      │ │
│  │ • Calls stock_plugin.get_stock_price('AAPL')                    │ │
│  │ • Calls stock_plugin.get_stock_price('TSLA')                    │ │
│  │ • Calculates total value                                        │ │
│  │                                                                 │ │
│  │ Response: "Your portfolio is worth $4,237.50:                   │ │
│  │            • AAPL: 10 shares @ $150.25 = $1,502.50             │ │
│  │            • TSLA: 5 shares @ $547.00 = $2,735.00"             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ONGOING MONITORING:                                                 │
│  • AI-synthesized tools are marked for extra scrutiny               │
│  • All calls logged with detailed parameters                        │
│  • User can review audit log any time                               │
│  • If tool behaves unexpectedly, user is notified                   │
│  • User can revoke permissions or uninstall at any time             │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 7. Database Schema

### PostgreSQL Tables

```sql
-- Tool registry
CREATE TABLE tools (
    tool_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    version VARCHAR(16) NOT NULL,
    type VARCHAR(16) NOT NULL,  -- 'built-in', 'custom', 'ai-synthesized'
    author VARCHAR(128),
    description TEXT,
    manifest JSONB NOT NULL,
    installed_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    usage_count INT DEFAULT 0,
    sandbox_type VARCHAR(16) NOT NULL,  -- 'shared', 'dedicated'
    status VARCHAR(16) DEFAULT 'active'  -- 'active', 'disabled', 'uninstalled'
);

-- Tool permissions (user grants)
CREATE TABLE tool_permissions (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    tool_id VARCHAR(64) REFERENCES tools(tool_id),
    capability VARCHAR(64) NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- NULL = never expires
    scope JSONB,  -- Optional constraints (e.g., {"recipients": ["work_contacts"]})
    auto_approved BOOLEAN DEFAULT FALSE,
    granted_by VARCHAR(16) DEFAULT 'user'  -- 'user', 'pattern_learned'
);

CREATE INDEX idx_permissions_user_tool ON tool_permissions(user_id, tool_id);

-- Tool execution log (audit trail)
CREATE TABLE tool_execution_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    tool_id VARCHAR(64) REFERENCES tools(tool_id),
    capability VARCHAR(64) NOT NULL,
    params JSONB NOT NULL,  -- Sensitive params redacted
    result_status VARCHAR(16) NOT NULL,  -- 'success', 'error', 'permission_denied'
    risk_score FLOAT NOT NULL,
    approval_status VARCHAR(16) NOT NULL,  -- 'auto_approved', 'user_approved', 'denied'
    execution_time_ms INT,
    device VARCHAR(16),  -- 'host', 'client'
    
    INDEX idx_log_timestamp (timestamp),
    INDEX idx_log_tool (tool_id, timestamp)
);

-- Tool synthesis queue (AI-generated tools pending approval)
CREATE TABLE tool_synthesis_queue (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    request_context TEXT NOT NULL,  -- What user asked for
    api_discovered VARCHAR(256),
    generated_manifest JSONB NOT NULL,
    generated_code TEXT NOT NULL,
    test_results JSONB,
    status VARCHAR(16) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    reviewed_at TIMESTAMP,
    user_feedback TEXT
);
```

---

## 8. Security Monitoring & Audit

### 8.1 Real-Time Monitoring

```python
class ToolSecurityMonitor:
    """Monitors tool execution for suspicious behavior."""
    
    def __init__(self, db: PostgreSQL, alerter: Alerter):
        self.db = db
        self.alerter = alerter
        self.anomaly_detector = AnomalyDetector()
    
    async def monitor_execution(self, log_entry: Dict[str, Any]):
        """Monitor a tool execution for anomalies."""
        # Check 1: Rate limiting
        recent_calls = await self._get_recent_calls(
            log_entry['tool_id'],
            window_seconds=3600
        )
        
        if len(recent_calls) > 100:  # Configurable per tool
            await self.alerter.alert(
                level='warning',
                message=f"Tool {log_entry['tool_id']} exceeded rate limit"
            )
        
        # Check 2: Unusual parameters
        if await self._detect_unusual_params(log_entry):
            await self.alerter.alert(
                level='info',
                message=f"Unusual parameters detected for {log_entry['tool_id']}"
            )
        
        # Check 3: High-risk actions at unusual times
        if log_entry['risk_score'] > 0.6:
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 23:  # Off-hours
                await self.alerter.alert(
                    level='warning',
                    message=f"High-risk action at unusual time: {log_entry}"
                )
        
        # Check 4: AI-synthesized tool behavior
        tool = await self.db.fetchrow(
            "SELECT type FROM tools WHERE tool_id = $1",
            log_entry['tool_id']
        )
        
        if tool['type'] == 'ai-synthesized':
            # Extra scrutiny for AI-generated tools
            if log_entry['result_status'] == 'error':
                await self.alerter.alert(
                    level='info',
                    message=f"AI-synthesized tool error: {log_entry}"
                )
    
    async def _detect_unusual_params(self, log_entry: Dict[str, Any]) -> bool:
        """Use ML to detect unusual parameter patterns."""
        # Train model on historical params for this tool+capability
        historical = await self.anomaly_detector.get_historical_params(
            log_entry['tool_id'],
            log_entry['capability']
        )
        
        # Compare current params
        is_anomaly = self.anomaly_detector.is_anomaly(
            log_entry['params'],
            historical
        )
        
        return is_anomaly
```

### 8.2 Audit Dashboard (User-Facing)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Tool Activity Dashboard                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  📊 Activity Summary (Last 24 Hours)                                 │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Total tool calls: 147                                           │ │
│  │ Auto-approved: 132 (90%)                                        │ │
│  │ User-approved: 12 (8%)                                          │ │
│  │ Denied: 3 (2%)                                                  │ │
│  │                                                                 │ │
│  │ Most used tools:                                                │ │
│  │ 1. Email Plugin: 45 calls                                       │ │
│  │ 2. Calendar Plugin: 32 calls                                    │ │
│  │ 3. File Tool: 28 calls                                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  📋 Recent Activity                                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 10:32 AM │ Email Plugin │ send_email      │ ✓ Auto-approved   │ │
│  │          │ To: john@work.com                                   │ │
│  │          │ Subject: "Meeting reminder"                         │ │
│  │                                                                 │ │
│  │ 10:15 AM │ Calendar     │ create_event    │ ✓ User-approved   │ │
│  │          │ Event: "Dentist appointment"                        │ │
│  │                                                                 │ │
│  │  9:47 AM │ File Tool    │ delete_file     │ ✗ Denied          │ │
│  │          │ Path: ~/Documents/important.pdf                     │ │
│  │          │ Reason: User rejected                               │ │
│  │                                                                 │ │
│  │  9:22 AM │ Email Plugin │ read_email      │ ✓ Auto-approved   │ │
│  │          │ Folder: INBOX (15 emails)                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ⚙️ Permissions Management                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Email Plugin                                      [Manage]      │ │
│  │ ✓ Read emails (auto-approved)                                  │ │
│  │ ✓ Send emails to work contacts (auto-approved)                 │ │
│  │ ✗ Delete emails (always ask)                                   │ │
│  │                                                                 │ │
│  │ File Tool                                         [Manage]      │ │
│  │ ✓ Read files in ~/Documents (auto-approved)                    │ │
│  │ ✗ Write files (always ask)                                     │ │
│  │ ✗ Delete files (always ask)                                    │ │
│  │                                                                 │ │
│  │ Stock Plugin (AI-synthesized)                     [Manage]      │ │
│  │ ✓ Get stock prices (auto-approved)                             │ │
│  │   [View Code] [Uninstall]                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  🔔 Alerts                                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ ⚠️ Email Plugin: 45 calls in last hour (rate limit warning)    │ │
│  │ ℹ️ New tool available: GitHub Integration (review)             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  [Export Audit Log] [Tool Settings] [Security Report]               │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 9. Resource Estimates

### Memory Footprint

**Shared Sandbox:**
- Container overhead: 50 MB
- Python runtime: 80 MB
- Loaded tools (average 5): 150 MB
- **Total: ~280 MB**

**Dedicated Sandboxes (per tool):**
- Email Plugin: 256 MB
- Payment Plugin: 256 MB
- SSH Plugin: 128 MB
- **Total (3 critical tools): ~640 MB**

**Tool Plugin Manager:**
- Registry + Permission Manager: 50 MB
- Execution Coordinator: 30 MB
- **Total: ~80 MB**

**Grand Total: ~1000 MB (1 GB)**

### Storage

**Tool binaries & dependencies:**
- Built-in tools: 300 MB
- Custom plugins (average 10): 200 MB
- AI-synthesized tools (average 5): 50 MB
- **Total: ~550 MB**

**Audit logs:**
- ~1 KB per execution
- 10,000 executions/month = 10 MB/month
- Retention: 3 months = 30 MB

**Total Storage: ~600 MB**

### CPU Usage

**Shared sandbox (idle): <1% CPU**
**Active tool execution: 10-25% CPU (depends on tool)**
**Permission checks: <1% CPU**

---

## 10. Summary & Next Steps

### Design Complete ✅

**Tool Plugin System includes:**
1. ✅ Dynamic risk-based permissions (context-aware)
2. ✅ Host vs. Client device separation
3. ✅ Hybrid sandboxing (shared + dedicated containers)
4. ✅ Three plugin types (built-in, custom, AI-synthesized)
5. ✅ Comprehensive audit logging
6. ✅ Security monitoring & anomaly detection
7. ✅ User-facing permission management
8. ✅ AI-autonomous tool creation (with approval)

### Key Security Features

- **Defense in Depth:** Multiple security layers
- **Principle of Least Privilege:** Minimum permissions per tool
- **User Sovereignty:** User has final say on all permissions
- **Transparency:** Full audit trail, user can review everything
- **Fail-Safe:** When uncertain, ask user

### Integration Points

**With Central Agent:**
- Tool execution requests flow through intent system

**With Module Activation:**
- Tool Plugin System itself is a module (can be loaded/unloaded)

**With Memory Consolidation:**
- Tool execution results stored as memories

**With Skill Tree:**
- Skills can invoke tools as capabilities

---

**Design Status:** ✅ COMPLETE  
**Ready for:** Implementation Phase 1  
**Estimated Implementation Time:** 4-5 weeks
