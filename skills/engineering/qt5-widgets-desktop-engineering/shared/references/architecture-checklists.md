# Architecture checklists for Qt 5.12 Widgets desktop tools

## New Qt5 Widgets application
- Confirm Qt version baseline is 5.12.x.
- Confirm C++ standard supported by toolchain, usually C++14 or C++17.
- Decide whether the canonical build entry is CMake, qmake, or both.
- Create at minimum `src/app`, `src/ui`, `src/core`, `src/models`, `resources`, `tests`.
- Decide ownership model for `MainWindow`, dialogs, services, worker objects, and models.
- Decide which workflows can block and design worker-thread boundaries before implementing screens.
- Decide which screens require model/view instead of `QTableWidget` or `QTreeWidget`.
- Define `QSettings` keys for geometry, state, recent files, and user preferences.
- Decide logging and user-visible error-reporting strategy.
- Plan deployment early, especially `platforms/`, image formats, styles, translations, and `windeployqt` behavior.

## Existing Qt5 Widgets repository audit
- Detect Qt version and whether the repo is truly 5.12-safe.
- Detect build-system reality: qmake only, CMake only, or dual-maintained.
- Inspect whether top-level code is split into app, UI, models, and services or collapsed into windows/dialogs.
- Check whether tables/trees use model/view or item widgets.
- Look for synchronous I/O, process execution, or parsing inside UI slots.
- Inspect object ownership around dialogs, worker objects, and long-lived services.
- Inspect settings persistence, translation resources, icons, and `.qrc` organization.
- Inspect packaging or deployment scripts, especially on Windows.
- Produce a staged migration plan rather than a rewrite fantasy.

## Model/view screen design
- Define the authoritative data source.
- Choose `QAbstractTableModel` or `QAbstractItemModel`.
- Define roles, headers, editability, and sort/filter needs.
- Decide whether a `QSortFilterProxyModel` is required.
- Decide whether a `QStyledItemDelegate` is needed.
- Decide update granularity: reset, insert/remove rows, `dataChanged`, layout change.
- Decide how selection state maps back to domain objects.
- Ensure formatting logic does not leak all over the view layer.

## Threading and responsiveness
- List all potentially blocking operations.
- Keep widgets in GUI thread only.
- Move heavy work to worker object or background execution path.
- Define progress, cancellation, timeout, and retry behavior where relevant.
- Use signal/slot delivery back to GUI thread.
- Guard destroyed widgets or dialogs with `QPointer` when async callbacks may arrive late.
- Avoid direct shared mutable state between threads.

## Packaging and deployment
- Make runtime plugin dependencies explicit.
- Verify `windeployqt` or Linux deployment flow in a clean environment.
- Include icons, translations, styles, and desktop metadata.
- Keep file paths configurable and avoid developer-machine assumptions.
- Document deployment prerequisites such as VC runtime and plugin directories.
- Test startup on a machine without Qt installed.

## Legacy dialog-heavy refactor
- Preserve current user-visible behavior first.
- Extract service logic before redesigning UI.
- Move repeated table/tree logic into model classes.
- Introduce actions and command handlers to shrink signal/slot sprawl.
- Centralize settings and error-reporting conventions.
- Only then consider larger structural cleanup.
