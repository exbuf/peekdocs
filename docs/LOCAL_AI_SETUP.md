# Private, Local AI Assistant — A Beginner's Guide

**Goal:** ask your documents questions in plain English — *"which contract mentions the roof
warranty?"* — with an AI assistant that runs **entirely on your own computer**, so nothing you
search or find is ever uploaded anywhere.

This guide assumes **no prior experience** with AI models, "runtimes," or the Model Context
Protocol (MCP). If you've never done any of this, you're in the right place. Budget about
**20–30 minutes**, most of which is a download finishing.

> Just want the quick version, or don't mind using a cloud assistant? The
> [Quickstart: Claude Code](USER_GUIDE.md#quickstart-claude-code-the-fastest-way-to-try-it) in
> the User Guide gets you talking to peekdocs in a couple of minutes — but with a cloud assistant,
> the snippets it reads leave your machine. This guide is the **fully-local, fully-private**
> route.

---

## The idea, in plain English

- **peekdocs** finds exact text in your files — fast, and across 100+ formats.
- An **AI assistant** lets you *ask* in everyday language instead of building a search yourself.
- Normally that assistant runs in the **cloud**, which means the snippets it reads get sent over
  the internet. To keep everything private, you run the assistant **on your own computer**
  instead. That's what this guide sets up.

You'll connect three things:

1. a program that runs an AI model on your computer (the **runtime**),
2. the AI model itself (a big file you download once), and
3. **peekdocs**, connected to that program so the assistant can search your files.

When it's done, the model, peekdocs, and your documents all live on your machine. Nothing leaves
it.

## A few words you'll run into

You don't need to *understand* these deeply — just recognize them:

| Word | What it means, plainly |
|---|---|
| **Model** / **LLM** (short for *Large Language Model*) | The "AI brain" — a large file you download and run. It's what turns your plain-language question into a tool call and writes the reply. |
| **Runtime** / **model runner** | The app that runs an AI model **on your own computer**. We use **LM Studio**; other local options include **Ollama**, **Jan**, and **GPT4All**. With a **cloud** assistant instead (e.g. **Claude Desktop** or **Claude Code**), the model runs on the provider's servers, so there's no local runner to install. |
| **MCP** (short for *Model Context Protocol*) | The open standard that lets an AI assistant plug into an outside tool (here, peekdocs). |
| **MCP host** | The app the assistant runs in that can connect to MCP tools. LM Studio is both the runner *and* the host. |
| **Tool calling** | The model's ability to actually *use* a tool. **Essential** — some models can't, and then this won't work (see Troubleshooting). |
| **`--root`** | The folder(s) you allow the assistant to search. Your safety fence. |
| **stdio** | The behind-the-scenes plumbing peekdocs and the app use to talk. You never touch it. |

## What you'll need

- A **Mac, Windows, or Linux** computer with about **8 GB of free memory (RAM)** — 16 GB is
  comfortable — and roughly **5 GB of free disk space** for the model.
- **peekdocs** installed (see the [Installation](INSTALLATION.md) guide if you haven't).
- An internet connection **for the downloads only**. Once everything's installed, it all works
  offline.

---

## Step 1 — Install a runtime (LM Studio)

The runtime is the app that downloads and runs AI models. We use **LM Studio** because it does
*two* jobs in one app: it runs the model **and** it can connect to peekdocs. That's the simplest
setup for a beginner.

- Download it from **[lmstudio.ai](https://lmstudio.ai)** and install it like any other app.
  *(On a Mac with [Homebrew](https://brew.sh): `brew install --cask lm-studio`.)*
- Launch it. If it offers to download a starter model on first run, you can **Skip** — we'll pick
  a specific one in the next step.

## Step 2 — Download an AI model

The model is the "brain." **Which model you pick matters a lot** — most beginner problems come
from choosing the wrong one.

1. In LM Studio, open the **Discover / Search** tab (magnifying-glass icon).
2. Search for **`Qwen2.5-7B-Instruct`**.
3. Choose a build and download it. Aim for the **`Q4_K_M`** version if asked (that's a good
   balance of quality and size — about **4–5 GB**).

⚠️ **The most important rule:** you need a model that can do **tool calling**, and it must be an
**instruct** model. Specifically:

- ✅ **Pick:** `Qwen2.5-7B-Instruct` (or another instruct model known for tool use, like
  Llama 3.1 8B Instruct).
- ❌ **Avoid `VL` / "Vision"** builds (e.g. `Qwen2.5-VL-7B`). These are for *images* and usually
  **can't call tools** — the assistant will just make up an answer instead of searching. This is
  the single most common way this setup fails.
- ❌ **Avoid "base"** (non-instruct) builds and **very small** models (1–3B) — unreliable at tools.

**Memory guide** (rough, for the `Q4_K_M` size):

| Model size | Disk | Works with | Notes |
|---|---|---|---|
| 3B | ~2 GB | 8 GB RAM | too small — unreliable at tools |
| **7–8B** (recommended) | ~4–5 GB | **16 GB RAM** (8 GB tight) | the sweet spot |
| 14B | ~9 GB | 24 GB RAM | more reliable, if you have the memory |

Once downloaded, the model lives under **My Models** (folder icon) and in the chat's model
selector — **not** in the Discover tab. (Searching Discover for a model you've *already*
downloaded shows nothing — that's expected, not a bug.)

## Step 3 — Add the peekdocs connector

peekdocs can talk to AI assistants, but that ability ships as an optional add-on called the
**`[mcp]` extra**, and it comes **only with the pip/pipx install** — *not* with the standalone
binary download. You don't need the GUI either: `peekdocs-mcp` is a headless server. Install it
once, in a terminal:

```bash
pipx install "peekdocs[mcp] @ git+https://github.com/exbuf/peekdocs.git"
```

**Already have peekdocs installed?** A plain `pipx install` does nothing when it's already there,
so add `--force` to actually pull the add-on:

```bash
pipx install --force "peekdocs[mcp] @ git+https://github.com/exbuf/peekdocs.git"
```

This gives you a new command, **`peekdocs-mcp`**. You won't run it yourself — LM Studio will start
it for you — but you can confirm it exists:

```bash
which peekdocs-mcp      # macOS / Linux  → prints a path like /Users/you/.local/bin/peekdocs-mcp
where peekdocs-mcp      # Windows
```

Note that path — you'll need it in the next step.

## Step 4 — Connect peekdocs to LM Studio

LM Studio reads a small settings file named **`mcp.json`** that lists the connectors — MCP
**servers** — it should connect to. You'll add **peekdocs** (one server) to it; LM Studio then
discovers peekdocs' individual tools (`search_documents`, `inventory_folder`, and the rest)
**automatically** — you never list tools yourself.

**Where the file is** (it's in a *hidden* folder, so it won't show in normal file browsers):

- **macOS / Linux:** `~/.lmstudio/mcp.json`
- **Windows:** `%USERPROFILE%\.lmstudio\mcp.json`

**How to open a hidden file:**

- **macOS (easiest):** in Terminal, run `open -e ~/.lmstudio/mcp.json` (opens in TextEdit). *(In
  Finder instead: press **⌘⇧G** and paste the path, or **⌘⇧.** to reveal hidden files.)*
- **Windows:** paste `%USERPROFILE%\.lmstudio\mcp.json` into File Explorer's address bar, or into
  Notepad's **File → Open** box — typing the path reaches the hidden folder even though it's not shown.
- **Linux:** `xdg-open ~/.lmstudio/mcp.json`, or press **Ctrl+H** in your file manager to show
  hidden files.

**What to put in it.** Replace the contents with this, using **the full path from Step 3** and the
folder you want the assistant to be able to search:

```json
{
  "mcpServers": {
    "peekdocs": {
      "command": "/Users/you/.local/bin/peekdocs-mcp",
      "args": ["--root", "/Users/you/Documents"]
    }
  }
}
```

Two things here matter, and both are common beginner traps:

- **Use the *full path* to `peekdocs-mcp` in `"command"`** (the one from `which`/`where`), not just
  `peekdocs-mcp`. LM Studio is a desktop app, and desktop apps often can't find commands the way
  your terminal can — the full path avoids a "failed to start" error. Use forward slashes even on
  Windows (`C:/Users/you/...`).
- **`--root` is your safety fence.** It names the folder the assistant is allowed to search — and
  it can search **only** inside that folder and its subfolders, never anywhere else on your disk.
  It's **required** (peekdocs won't start without it), you can list **several** (`"--root", "A",
  "--root", "B"`), and it blocks sneaky paths (`..` tricks and shortcuts that point outside). Point
  it at a broad folder like your Documents, and you can then ask about any subfolder in plain
  language without editing this file again.

Save the file.

## Step 5 — Turn it on

**1. Reload LM Studio so it sees peekdocs.** LM Studio reads `mcp.json` only at startup, so after
editing the file, **quit LM Studio completely and reopen it** (or toggle peekdocs off then on in
the integrations panel). The first time, it may ask you to **allow** the peekdocs server — say yes.

**2. Confirm peekdocs is connected (this is "pointing to peekdocs").** Open the
**integrations / plugins / "Program"** panel — look for a **puzzle-piece, plug, or tools icon** in
LM Studio's sidebar. You should now see **peekdocs** listed, with its tools under it
(`search_documents`, `inventory_folder`, and more). If there's an on/off switch next to peekdocs,
make sure it's **on**. Seeing those tools means peekdocs is connected — you never add tools
yourself; they appear automatically.

**3. Select the AI model.** Open the **Chat** (speech-bubble icon). At the **top of the chat**
there's a **model selector** — click it and choose your **Qwen2.5-7B-Instruct** from the list of
downloaded models. *(Downloaded models appear here and under **My Models** — **not** in the
Discover tab; Discover only searches for new models to download.)* Give it a few seconds to load
into memory.

**4. Make sure tools are on for the chat.** Near the message box there's usually a **tools / wrench
icon** — make sure tool use is enabled and **peekdocs** is switched on for this conversation.
That's what lets the model actually call peekdocs.

## Step 6 — Ask your first question

In the chat, type something like:

> *Use peekdocs to search my Documents for the word invoice and tell me which files it's in.*

**What success looks like:** before answering, the assistant shows a **tool call** (peekdocs
running a search), then replies with real file names and line numbers. That tool call is the whole
point — it means the assistant actually searched your files instead of guessing.

Two good things to try next:

- **Ask where it looked:** *"What folder did you search?"* — it should name your `--root` folder.
- **Test the fence:** *"Search my whole home folder for passwords."* — if that's outside your
  `--root`, peekdocs **refuses**. That refusal is the safety fence working as intended.

And the payoff: because the model is running on your computer, **your question, the file snippets,
and the answer never leave your machine.**

## Changing which folders it can search

The searchable folders are set by `--root` in `mcp.json` (Step 4), *not* in the chat. You rarely
need to change it, though: point `--root` at a broad parent folder once (like your Documents), and
then just **name the subfolder in your question** — *"search my Documents/Contracts folder for…"*.
The assistant searches wherever you point, as long as it's inside `--root`.

To allow a genuinely new area, edit `--root` in `mcp.json`, save, and **reload LM Studio** (it only
reads the file at startup).

## If something goes wrong

- **The assistant makes something up instead of searching** (invents commands, doesn't show a tool
  call). Almost always the **wrong model** — a vision (`VL`), base, or tiny model that can't call
  tools. **Fix:** load a proper `-Instruct` build (Step 2). *(Advanced check: LM Studio's logs
  under `~/.lmstudio/server-logs` will show many `ListToolsRequest` and zero `CallToolRequest` —
  that pattern means the model never called a tool.)*
- **"command not found" / "failed to start server."** LM Studio can't find `peekdocs-mcp`. **Fix:**
  put the **full path** in `mcp.json` (Step 4), and confirm the `[mcp]` extra installed (Step 3).
- **You ran `peekdocs-mcp` in a terminal and it just sits there doing nothing.** That's normal —
  it's a server waiting to be contacted, not a frozen program. Press **Ctrl-C** to stop it; you're
  not meant to run it by hand (LM Studio does).
- **You can't find or open `mcp.json`.** It's in a hidden folder — see the "How to open a hidden
  file" tips in Step 4.
- **The first answer is slow.** The model is loading into memory. Later answers are faster.

## Prefer a cloud assistant instead?

If privacy of the file snippets isn't a concern for a given folder, a cloud assistant is easier to
set up — no model to download. See the
[Quickstart: Claude Code](USER_GUIDE.md#quickstart-claude-code-the-fastest-way-to-try-it). The
peekdocs side is identical; only the model's location (and whether snippets leave your machine)
differs. Full background is in the User Guide's
[MCP server](USER_GUIDE.md#mcp-server-search-from-an-ai-assistant) section.
