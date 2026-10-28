# My Clone — portable memory framework

A local-first framework for keeping one source-linked memory record per conversation, reviewing proposed insights, and maintaining a portable summary. This public directory contains reusable instructions, templates and tools. It contains no personal chat archive, financial records, biography or family messages.

## Use locally

1. Copy this directory to your private working location.
2. Run `python tools/init_memory.py`. Existing personal files are never overwritten.
3. Read `START-HERE.md` and give `UPDATE-PROMPT.md` to the assistant in the conversation you want to record.
4. Write that conversation's record under `chats/records/` using `templates/CHAT-RECORD.md`. Keep a stable filename per provider/chat ID.
5. Run `python tools/build_chat_archive.py` to build the private source index and combined archive. Run `python tools/build_portable.py` after reviewed memory edits.

The scripts use Python's standard library. They do not connect accounts, send data, train models, or start background jobs. The source compiler groups files; a human or assistant must review any proposed personal interpretation before adding it to memory.

## One coordinator, nine specialists

See `agents/ROUTING.md`. Generic project-scoped role definitions live in `.codex/agents/`. Supported runtimes may load them when this directory is opened as a project. Other assistants can follow the same instructions sequentially. Creating these files does not deploy a persistent bot.

## Privacy boundary

Personal memory, conversation records, generated indexes/summaries, imported sources, reviews and archives are ignored by Git. Only the framework should be committed here. Do not force-add those ignored files. A family-approved export must be made separately from private working memory; mentioning family does not approve sharing.

An assistant without local filesystem access can return a named Markdown record for the owner to save. An unavailable history must stay marked as partial or unknown.
