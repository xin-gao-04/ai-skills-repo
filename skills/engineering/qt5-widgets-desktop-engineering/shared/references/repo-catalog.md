# Repository catalog for Qt/C++ skill research

This catalog is curated for building a **Qt 5.12 Widgets desktop-tool engineering** skill. The repositories are not all Qt5.12-only, but each teaches something useful for desktop Qt architecture, packaging, UX, or maintainability.

## Desktop utilities and end-user applications

### 1. Flameshot
Teaches cross-platform desktop utility structure, action-oriented UX, packaging awareness, and practical desktop-tool scope control.

### 2. QtScrcpy
Teaches Qt-based device tooling, responsive UI around I/O-heavy workflows, and pragmatic desktop application structure.

### 3. moonlight-qt
Teaches larger Qt desktop client organization, platform separation, and non-trivial runtime packaging concerns.

### 4. MuseScore
Teaches large-scale Qt application architecture, layered code organization, and how UI complexity must be separated from deep domain logic.

### 5. NotepadNext
Teaches editor-style desktop application structure and operational UX patterns familiar to Windows users.

### 6. Zeal
Teaches documentation-browser style desktop UX, search-heavy tooling, and practical Qt desktop maintainability.

### 7. Tiled
Teaches mature editor-style architecture, document workflows, dockable interfaces, and stateful desktop behavior.

### 8. PrismLauncher
Teaches launcher-style desktop tool UX, settings persistence, and packaging/deployment pragmatism.

### 9. LibreCAD
Teaches complex Widgets application structure and how large desktop tools evolve over long maintenance cycles.

### 10. QOwnNotes
Teaches everyday productivity desktop-tool patterns, settings, storage, and plugin-adjacent concerns.

## Framework and tooling references

### 11. qtbase
Teaches Qt core and Widgets-adjacent patterns, API shape, and platform abstraction discipline.

### 12. qttools
Teaches Qt tooling and utility-side project organization relevant to desktop developer tools.

### 13. qt-creator
Teaches large desktop IDE architecture, plugin boundaries, and command-driven desktop UI.

### 14. awesome-qt
Teaches ecosystem map and recurring architectural choices across Qt projects.

## Additional practice corpus

### 15. FileCentipede
Useful for studying desktop tool integration across network/process/filesystem concerns.

### 16. nomacs
Useful for studying media-heavy Qt desktop application patterns.

### 17. calibre
Useful as a large desktop-application reference, especially for workflow-rich tool UX and deployment reality.

### 18. Scribus
Useful for understanding long-lived desktop publishing style architecture and document workflows.

### 19. Wireshark
Not a pure Qt codebase in the same sense, but useful for desktop tool UX, model-heavy data presentation, and platform packaging discipline.

### 20. GoldenCheetah
Useful for complex desktop data visualization and long-lived Qt application maintenance patterns.

## How to use this catalog

Do not copy any single repository blindly.

Use the corpus to answer these questions:
- how should a Qt Widgets desktop tool lay out modules?
- when should a table/tree switch to model/view?
- what belongs in `MainWindow` and what does not?
- how should packaging and deployment appear in the repository?
- how should a Qt5-era codebase balance qmake compatibility with gradual modernization?
