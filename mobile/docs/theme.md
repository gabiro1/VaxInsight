# Theme system

VaxInsight's theme tokens live in `src/theme/tokens.js`. The exported `themes`
object contains the light and dark semantic palettes, including `background`,
`surface`, `surfaceSecondary`, `elevatedSurface`, text colors, borders,
accent colors, input colors, status colors, navigation colors, and overlays.
Legacy aliases remain available so existing components can migrate without
changing the brand vocabulary all at once.

`src/context/ThemeContext.js` owns the active preference and resolved mode:

- `light` always resolves to the light palette.
- `dark` always resolves to the dark palette.
- `system` resolves from React Native's `Appearance` API and updates when the
  operating system appearance changes.

The preference is stored locally with AsyncStorage under
`vaxinsight.themePreference`. A missing or invalid value defaults to `system`.
The provider waits for the stored value before rendering the app, which avoids
rendering the wrong palette during startup.

## Applying theme tokens

Use `useTheme()` in a screen or reusable component, then build any
color-dependent styles from the returned `colors` object:

```js
const { colors } = useTheme();
const styles = createStyles(colors);
```

Prefer semantic tokens such as `colors.surface`, `colors.primaryText`,
`colors.inputBorder`, and `colors.primaryAccent`. Add a new semantic token to
both palettes in `tokens.js` before using it. Do not add a one-off hex value to
a screen when an existing token describes the same role.

Use `getShadows(colors)` for theme-aware elevation and shadows. Keep brand
orange as the primary accent and select foreground colors from the palette so
buttons, cards, inputs, alerts, and navigation remain readable in both modes.
