---
name: qt5-widgets-desktop-engineering
description: Build, review, refactor, and debug Qt 5.12 C++ desktop tools built primarily with Qt Widgets. Use when the task involves MainWindow/dialog workflows, QAction/menu/toolbar UX, model-view tables and trees, item delegates, forms, settings persistence, file/process/network operations in desktop apps, repository audits, packaging on Windows/Linux, or migration of ad hoc UI code into maintainable Qt5.12 structure. This skill is intentionally biased toward Qt Widgets and away from Qt Quick/QML unless the repository already mixes them.
---

# Qt 5.12 Widgets Desktop Engineering Skill

Use this skill when the target codebase is a desktop-first Qt Widgets application and the practical baseline is **Qt 5.12**.

The goal is not to produce generic Qt examples. The goal is to produce code and architecture that fit a medium or large internal desktop tool maintained by a C++ team.

## Primary assumptions

- Default framework target: **Qt 5.12.x**
- Default UI stack: **Qt Widgets**
- Default language baseline: **C++14 or C++17**, depending on repository constraints
- Default deployment target: Windows desktop first, Linux second, unless the task says otherwise
- Default build reality: **CMake or qmake may both exist** in legacy codebases

When a request conflicts with these assumptions, state the conflict explicitly and adapt.

## What this skill optimizes for

1. Desktop utility software, not mobile-first UI.
2. Stable maintainability over flashy presentation.
3. Clear ownership and lifecycle rules for `QObject` and widgets.
4. Responsive UI under file I/O, process, network, parsing, or data-heavy workloads.
5. Model/view correctness for tables, trees, filters, and delegates.
6. Practical Qt5.12-compatible recommendations, not Qt6-only modernizations.

## Core operating rules

### 1. Classify the work before coding

Treat incoming work as one of these types:

- **Small utility window/dialog**: keep structure simple, but do not let logic collapse into slot spaghetti.
- **MainWindow-based desktop tool**: use `QAction`, menus, toolbars, status bar, dock widgets, settings persistence, recent files, shortcuts.
- **Data-heavy admin or inspection tool**: push data into `QAbstractItemModel` and proxy models early.
- **Legacy refactor**: preserve behavior first, then separate UI, service, and model layers in stages.
- **Packaging/deployment problem**: focus on runtime dependencies, plugins, translations, styles, paths, and deploy tooling.

Always say which class the task belongs to.

### 2. Prefer a Qt Widgets project layout that scales

Default repository shape:

- `src/app/` for startup, `main.cpp`, app wiring, and top-level window bootstrap
- `src/ui/` for `MainWindow`, dialogs, widgets, delegates, and generated `ui_*.h` integration points
- `src/core/` for services, persistence, domain logic, file/process/network wrappers
- `src/models/` for `QAbstractItemModel`, proxy models, item roles, and selection-related helpers
- `src/common/` for narrow shared utilities only
- `resources/` for icons, translations, and bundled static assets
- `tests/` for unit tests and targeted UI integration tests
- `packaging/` for deployment scripts, installer metadata, and runtime notes

For smaller projects, `src/ui`, `src/core`, `src/models` is sufficient. Do not introduce deep folder trees without need.

### 3. Respect Qt 5.12 realities

- Do not default to Qt6 APIs.
- Do not assume all modern helper APIs exist.
- Mention compatibility risk when suggesting features introduced or normalized later in Qt.
- When proposing CMake, use patterns compatible with Qt5 rather than Qt6 convenience APIs.
- When touching regex, networking, model/view, and deployment APIs, keep examples valid for Qt 5.12.

### 4. Treat ownership explicitly

In Qt Widgets apps, object lifetime bugs are among the most common sources of crashes and leaks.

Use these rules:

- For child widgets and dialogs attached to widget hierarchies, prefer Qt parent-child ownership.
- For long-lived non-`QObject` service objects, prefer `std::unique_ptr` or value members.
- For `QObject` services that are not widget children, choose one ownership model and state it explicitly.
- Avoid mixing raw ownership, parent ownership, and smart pointers without a written rule.
- Be careful with `deleteLater()`, queued connections, and lambdas capturing `this`.
- Use `QPointer` where a GUI object may disappear before an async callback completes.

### 5. Keep UI classes thin

`MainWindow`, dialogs, and custom widgets should coordinate presentation and user interaction. They should not become the primary home of parsing logic, business rules, filesystem orchestration, or process management.

Good split:

- UI class collects input, updates controls, triggers actions, renders results
- Service class does the actual file/process/network/business work
- Model class owns tabular or tree data presented by views

If a slot exceeds roughly one screen and mixes validation, I/O, transformation, and widget updates, push back and split it.

### 6. Default to model/view for real data

Use `QTableView`, `QTreeView`, `QListView`, `QAbstractItemModel`, and proxy models when any of these are true:

- Data size is non-trivial
- Sorting or filtering is required
- Multiple views consume the same dataset
- Incremental updates matter
- Custom painting or editing behavior is needed

Do not use `QTableWidget` or `QTreeWidget` as the default for serious tool UIs unless the data is truly small and static.

### 7. Avoid GUI-thread blocking

Qt Widgets desktop tools often start simple and then degrade because file parsing, external process execution, database reads, or network calls get added directly into slots.

Rules:

- GUI thread owns widgets only.
- Heavy work moves to worker objects, `QThread`, thread pools, or async process/network APIs.
- Progress and cancellation paths must be explicit when work is user-visible.
- Results are marshaled back to GUI through signals/slots or safe invocation patterns.

When suggesting threading, also state the thread-affinity assumptions.

### 8. Build desktop-grade UX, not just working code

For Qt Widgets tools, always consider whether the task should include:

- `QAction` based command wiring
- menu bar, toolbar, and context menu consistency
- persistent settings via `QSettings`
- recent file/project lists
- drag and drop
- clipboard support
- status feedback and progress reporting
- error dialogs with actionable text
- keyboard shortcuts
- translations and resource packaging

## Qt 5.12 specific decision framework

### Build system choice

Prefer this order:

1. **Keep existing build system** if the repository is already stable and the task is not a migration task.
2. **Use CMake** for new work if the team can support it.
3. **Support qmake honestly** in legacy repositories, because Qt 5.12 codebases still use it heavily.

Push back on unnecessary build-system rewrites unless they solve a real maintenance problem.

### Widgets over QML

For this skill, default to Widgets when:

- The app is desktop-first
- The UI is forms, tables, trees, editors, inspectors, launchers, configuration panels, or operational consoles
- Native desktop affordances and mature controls matter more than animation
- The team is already on Qt 5.12 and does not need a QML-heavy architecture

If QML appears in the repo, treat it as an exception that must justify itself.

### Dialog strategy

- Use modal dialogs for focused confirmation or bounded data entry.
- Use modeless panels or dock widgets for repeated workflows.
- Avoid turning every workflow into a custom dialog when the main window can host it more clearly.
- Keep validation logic out of UI glue where possible.

### Table/tree strategy

Default stack:

- `QAbstractTableModel` or `QAbstractItemModel`
- `QSortFilterProxyModel`
- `QStyledItemDelegate` for custom edit/render behavior
- persistent selection behavior only when it is really needed

This is usually more maintainable than embedding state directly into widgets.

## Implementation patterns

### MainWindow pattern

A healthy `MainWindow` typically owns:

- command and action wiring
- view composition
- toolbar/menu/status setup
- restoring and saving geometry/state
- delegating commands to services or controllers
- receiving result signals and updating visible state

It should not own parsing engines, network protocol logic, or deep business rules.

### Service boundary pattern

Use services for:

- filesystem scanning and serialization
- external process invocation
- network requests and retries
- long-running transforms
- database or cache access
- import/export logic

Service APIs should be narrow and testable. Avoid a single giant `AppManager`.

### Model/view pattern

For each non-trivial table or tree, define:

- the source data owner
- model roles and headers
- update strategy, reset vs incremental insert/remove/dataChanged
- proxy model chain if filtering/sorting is involved
- delegate strategy for editors and custom display

### Settings pattern

Use `QSettings` for:

- window geometry and state
- recent files and last paths
- user preferences
- column widths or view state when appropriate

Do not scatter settings keys throughout UI code. Centralize key names.

### Error/reporting pattern

- Services produce structured failure information.
- UI translates that into user-facing messages.
- Logs contain technical detail.
- Users should know what failed, why it matters, and what they can do next.

## Review checklist

When reviewing or generating code, inspect in this order:

1. Is the task clearly classified as a Widgets desktop-tool problem?
2. Are Qt 5.12 assumptions stated and respected?
3. Is build-system advice valid for Qt5 and the repo's reality?
4. Is ownership unambiguous for widgets, dialogs, and services?
5. Is `MainWindow` or dialog logic too fat?
6. Is model/view used where tables or trees are important?
7. Are blocking operations off the GUI thread?
8. Are actions, settings, shortcuts, and UX conventions handled like a desktop app?
9. Is deployment considered, especially on Windows with plugins and runtime DLLs?
10. Does the proposal look maintainable in a real team six to twelve months later?

## Anti-patterns to push back on

Reject or refactor these unless constrained by legacy compatibility:

- Business logic implemented directly inside `MainWindow` slots
- `QTableWidget` or `QTreeWidget` used as the main data store for complex screens
- Synchronous file parsing, process execution, or network calls from button handlers
- Global singleton managers with unclear ownership and wide write access
- Utility headers included everywhere
- Blind conversion to Qt6-style CMake or APIs in a Qt 5.12 codebase
- Overuse of custom-painted widgets when delegates or standard widgets are sufficient
- Passing widget pointers deep into service layers
- Dialog classes that both execute business logic and store long-lived state
- Massive `connect` sections with no clear command or controller structure

## Output expectations

When using this skill for a non-trivial task, provide:

- chosen architecture
- Qt version assumptions, explicitly saying **Qt 5.12** unless overridden
- build-system assumptions, including qmake/CMake reality
- ownership model
- thread model
- project layout
- migration path if refactoring legacy code
- deployment notes if the tool is user-facing

## Bundled references

Use these when needed:

- `references/repo-catalog.md`: curated repositories and what they teach for Qt Widgets desktop tools
- `references/repo-patterns.md`: cross-repo patterns and anti-patterns with Qt5 bias
- `references/architecture-checklists.md`: practical checklists for Qt5 Widgets, model/view, threading, and packaging
- `references/qt5_12_compat_notes.md`: compatibility notes to keep recommendations aligned with Qt 5.12

## Bundled templates

- `templates/mainwindow_skeleton.md`: recommended MainWindow/module split for a Qt5 Widgets tool
- `templates/model_view_checklist.md`: what to define before building a serious table/tree screen

## Bundled script

Use `scripts/qt_repo_audit.py` to audit a local Qt repository. It now reports Qt5/qmake/CMake signals, Widgets-oriented structure hints, and deployment warnings relevant to desktop tools.
