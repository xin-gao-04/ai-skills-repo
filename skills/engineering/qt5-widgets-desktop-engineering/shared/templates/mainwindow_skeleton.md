# Recommended MainWindow split for a Qt 5.12 Widgets desktop tool

## Files
- `src/app/main.cpp`
- `src/ui/mainwindow.h`
- `src/ui/mainwindow.cpp`
- `src/ui/mainwindow.ui`
- `src/core/appservices.h`
- `src/core/appservices.cpp`
- `src/models/...`
- `resources/app.qrc`

## Responsibilities

### `main.cpp`
- create `QApplication`
- initialize app metadata
- initialize logging/settings basics
- create service container or top-level services
- create `MainWindow`
- restore startup state if needed

### `MainWindow`
- own actions, menus, toolbar, status bar
- wire commands to services
- own visible views and dialogs
- receive service results and update controls
- save/restore geometry and state

### service layer
- implement filesystem, process, network, serialization, and domain logic
- expose narrow APIs and result signals/callback contracts
- avoid direct dependency on widget types

### models
- own table/tree presentation logic
- convert domain data into Qt roles and headers
- keep sort/filter logic separate via proxy models where appropriate
