"""Subcommand handlers for the peekdocs CLI.

Each module here owns one subcommand ("--check", "--diff", "--runs",
etc.) and exposes a ``handle_*(args) -> int`` function that
:func:`peekdocs.cli._main_inner` dispatches to. Extracting one
subcommand per module keeps ``cli.py``'s dispatcher small and readable,
and it means each subcommand's error handling / arg validation lives
in one focused place instead of blending into a mega-branch inside
``_main_inner``.

This is the same architectural move the GUI ``_mixin_tools.py`` got in
v1.2.76 — one file per feature domain, dispatched through a slim
top-level. Standard search + ``--suite`` + ``--regex-collection``
remain in ``_main_inner`` for now; they share the flag-parsing
plumbing that spans the report-writing pipeline, and factoring that
shared surface out cleanly is its own multi-day refactor.

**Adding a new subcommand:**

1. Add ``peekdocs/commands/foo.py`` with a ``handle_foo(args: list[str]) -> int``
   function. Take only what you need; return ``0`` on success, non-zero
   on error (with a message printed to stderr).
2. Wire it in ``peekdocs/cli.py``'s ``_main_inner``: ``if args and
   args[0] == "--foo": return handle_foo(args)``.
3. Add tests in ``tests/test_commands_foo.py`` or extend the
   subcommand's coverage in ``tests/test_cli.py``.
"""
