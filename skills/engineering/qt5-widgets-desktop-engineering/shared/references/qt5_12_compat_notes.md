# Qt 5.12 compatibility notes for generated solutions

This skill defaults to Qt 5.12. That means generated solutions should avoid quietly relying on Qt6-first assumptions.

## General guidance
- State explicitly when a recommendation is Qt6-oriented and provide a Qt5.12-safe alternative.
- Keep examples valid for common Qt 5.12 toolchains on Windows.
- Do not assume recent convenience APIs exist just because they are common in newer examples online.

## Build system
- New projects may use CMake, but many real Qt 5.12 repositories still use qmake.
- Do not propose a build-system rewrite unless it solves a concrete problem.
- Keep CMake examples target-based and Qt5-compatible.

## Widgets and desktop UX
- Prefer standard Widgets and delegates over custom rendering unless there is a real UX need.
- `QAction`, `QMenu`, `QToolBar`, `QStatusBar`, `QDockWidget`, and `QSettings` remain core patterns.

## Model/view
- Prefer `QAbstractItemModel` and proxy models for non-trivial screens.
- Avoid item-widget-heavy solutions for serious operational tables and trees.

## Async and ownership
- Use worker-object patterns and signal/slot marshaling carefully.
- Guard against use-after-free when windows or dialogs close before async completion.
- State ownership clearly when combining parent ownership with standard smart pointers.

## Deployment
- On Windows, include deployment notes for Qt platform plugins, image format plugins, styles, translations, and runtime DLLs.
- `windeployqt` is often part of the practical answer and should be considered early.
