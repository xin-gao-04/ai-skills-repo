# Cross-repository patterns for Qt5 Widgets desktop tools

This file distills patterns from the repository corpus with an explicit bias toward desktop Qt Widgets work and Qt5-era engineering constraints.

## What mature Qt Widgets repositories tend to do

### 1. They treat desktop UX as a first-class concern
Common signals:
- command-centric UI via `QAction`
- menu/toolbar/status organization
- geometry/state persistence
- keyboard shortcuts
- import/export or recent-file workflows

### 2. They separate UI shell from operational logic
Even when not academically pure, healthier projects keep file I/O, parsing, network, and data transforms outside `MainWindow` and dialogs.

### 3. They use model/view once data stops being trivial
Mature repositories move tables and trees to model/view when sorting, filtering, or scale matters. They do not treat item widgets as the universal solution.

### 4. They make packaging part of the repo
Strong repositories document or script deployment instead of assuming the developer machine is the runtime environment.

### 5. They accept platform boundaries as real
OS-specific behavior is isolated instead of smeared across the UI layer.

## What weak Qt Widgets repositories often do

### 1. Everything lives in window classes
Symptoms:
- giant slot functions
- direct filesystem and process logic in button handlers
- no service boundary
- no easy way to test behavior without the GUI

### 2. `QTableWidget` becomes the data model
Symptoms:
- sorting/filtering grows painful
- hidden business state is stored in widget items
- data refreshes become full rebuilds
- custom editors become brittle

### 3. Async is bolted on late and unsafely
Symptoms:
- worker objects with unclear ownership
- GUI access from background thread
- callback crashes after dialog close
- no cancellation or progress path

### 4. Build and deployment are treated as afterthoughts
Symptoms:
- only works on developer machine
- plugins missing in deployment
- translations or icons missing outside build tree
- inconsistent qmake vs CMake support

## Practical rules to carry into generated solutions

- Prefer `QAction` driven command wiring over random button-to-slot sprawl.
- Prefer model/view over item widgets once a screen is operationally important.
- Prefer service classes over deep business logic in windows and dialogs.
- Prefer Qt5-compatible code paths unless the user explicitly wants a migration plan.
- Prefer incremental refactor plans over idealized rewrites.
