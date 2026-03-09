# Model/view checklist for Qt 5.12 Widgets tools

Before implementing a table or tree screen, answer these questions:

1. What is the authoritative data source?
2. Is a flat table enough, or is hierarchy required?
3. Which columns or roles are editable?
4. Is sorting required?
5. Is filtering required?
6. Will multiple views share the same data?
7. Do updates happen incrementally or by full reload?
8. Is a custom delegate needed for display or editing?
9. How is selection mapped back to domain objects?
10. What should persist across sessions, such as column widths or sort order?
