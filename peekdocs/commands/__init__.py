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

1. Add ``peekdocs/commands/foo.py`` with a ``handle_foo(...) -> int``
   function. Take whatever argument shape fits the subcommand — some
   handlers need the full ``args: list[str]`` slice (``--diff``,
   ``--runs``); others need nothing at all (``--check``). Return
   ``0`` on success, non-zero on error (with a message printed to
   ``stderr``).
2. Wire it in ``peekdocs/cli.py``'s ``_main_inner``: ``if args and
   args[0] == "--foo": return handle_foo(args)``.
3. Add tests in ``tests/test_commands_foo.py`` or extend the
   subcommand's coverage in ``tests/test_cli.py``.
4. Add the file to ``[tool.mypy].files`` in ``pyproject.toml`` so the
   type-check gate covers the new module.

**Circular-import defense.** Handlers routinely need helpers that
live in ``peekdocs/cli.py`` (``run_system_check``, ``VERSION``,
etc.). Because ``cli.py`` imports *from* this package, a
top-level ``from peekdocs.cli import X`` in a handler creates a
circular import at module load. The pattern used throughout is a
**lazy import inside the handler function body**:

    def handle_check() -> int:
        from peekdocs.cli import run_system_check   # lazy, defers to call time
        info = run_system_check()
        ...

Follow the same pattern in new handlers. Runtime cost is negligible
(one dict lookup per invocation) and it keeps the import graph
one-way.
"""
