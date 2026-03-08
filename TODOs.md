# hyprvisual – TODOs

_Última actualización: Sesión de refactorización y features (2026-03-07)_

---

## Arquitectura

### Refactorización completada

El proyecto fue reorganizado desde un archivo monolítico a una estructura modular bajo `hyprvisual/src/`:

```
hyprvisual/
├── main.py                      # Entrypoint (añade src/ al PYTHONPATH)
├── pyproject.toml
├── install.sh
├── README.md
└── src/
    ├── app.py                   # Clase principal DisplayTUIApp
    ├── app.tcss                 # CSS/estilos de la TUI (Textual CSS)
    ├── core/
    │   ├── display_manager.py   # Lógica de hyprctl (leer/aplicar estados)
    │   └── profile_manager.py   # Guardar/cargar perfiles en ~/.config/hypr/hyprvisual.json
    └── ui/
        ├── utils.py             # Helpers (ej: mnemonic labels)
        ├── components/
        │   └── display_card.py  # Widget de tarjeta por monitor
        └── screens/
            ├── mirror.py        # Modal selección de fuente espejo
            ├── hz.py            # Modal selección resolución/frecuencia
            ├── position.py      # Modal ajuste de posición X/Y
            ├── confirm.py       # Modal de confirmación con countdown 15s
            ├── scale.py         # Modal selección de escala (0.5x–3.0x)
            ├── profile.py       # Modal de perfiles (guardar/cargar/borrar)
            └── workspace.py     # Modal asignación de Workspace predeterminado
```

---

## Completado

### Features originales
- [x] Detección dinámica de monitores vía `hyprctl monitors all -j`
- [x] Toggle On/Off con confirmación/revert modal de 15 segundos
- [x] Modo Mirror con selección de fuente
- [x] Badge de Workspace activo por monitor
- [x] Navegación por teclado: Tab entre tarjetas, `m` para mirror, Space/Enter para toggle
- [x] Detección automática del mejor modo (mayor Hz) al re-habilitar monitores
- [x] Temas dinámicos: Glass, Hacker, Nordic (tecla `t`)
- [x] Selector frecuencia/resolución (`h`) por monitor

### Nuevas features implementadas en esta sesión
- [x] **1. Gestor de Posiciones Físicas** — tecla `p`
  - Soporte para coordenadas X/Y en `display_manager.py`
  - Modal para mover monitor izquierda/derecha/arriba/abajo relativo al primario
- [x] **2. Perfiles de Layout** — tecla `P` (global)
  - Guardar/cargar/borrar configuraciones completas
  - Persiste en `~/.config/hypr/hyprvisual.json`
- [x] **3. Escalado** — tecla `s`
  - Selección de escala por monitor: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 1.75x, 2.0x, 2.5x, 3.0x
  - Muestra la escala actual en la descripción de la tarjeta
- [x] **4. Identificador Visual Físico (Blink)** — tecla `i`
  - Parpadea el monitor seleccionado via `hyprctl dispatch dpms off/on`
  - Asíncrono para no congelar la TUI
- [x] **5. Workspaces Predeterminados** — tecla `w`
  - Asignar un Workspace ID fijo a un monitor mediante `hyprctl keyword workspace`

---

## Pendiente

- [ ] **6. Auto-Generar `hyprland.conf`** — tecla `c`
  - Botón para escribir/reemplazar las reglas `monitor=` en el archivo principal de Hyprland
  - Leer estado actual y generarlo como texto tipo `monitor=DP-1,1920x1080@144,0x0,1`

- [ ] **7. Mini Mapa ASCII**
  - Dibujar una representación visual arriba de las tarjetas basadas en las posiciones relativas (X/Y)
  - Cada monitor representado como un bloque con su nombre

- [ ] **8. Rotación / Transform**
  - Permitir cambiar la rotación de un monitor: 0°, 90°, 180°, 270°
  - Usar `hyprctl keyword monitor NAME,res@hz,pos,scale,transform N`

- [ ] **9. VRR / Adaptive Sync**
  - Toggle de VRR (Variable Refresh Rate) por monitor
  - Usar `hyprctl keyword monitor NAME,vrr,1` o `0`

- [ ] **10. Brightness / Gamma control**
  - Integrar `ddcutil` o `brightnessctl` para ajustar brillo directamente desde la TUI

---

## Atajos de teclado (resumen actual)

| Tecla     | Acción                              | Ámbito       |
|-----------|-------------------------------------|--------------|
| `Space`   | Toggle On/Off del monitor           | Tarjeta      |
| `m`       | Abrir selector de Mirror            | Tarjeta      |
| `h`       | Seleccionar resolución/frecuencia   | Tarjeta      |
| `p`       | Ajustar posición X/Y                | Tarjeta      |
| `s`       | Ajustar escala                      | Tarjeta      |
| `i`       | Parpadear monitor (identificar)     | Tarjeta      |
| `w`       | Asignar Workspace predeterminado    | Tarjeta      |
| `P`       | Abrir gestor de Perfiles            | Global       |
| `t`       | Cambiar tema visual                 | Global       |
| `r`       | Refrescar lista de monitores        | Global       |
| `q`       | Salir                               | Global       |
