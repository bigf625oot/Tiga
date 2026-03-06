# BaseIcon Component

A wrapper around `@iconify/vue` for dynamic icon loading with enhanced features.

## Features

- Dynamic icon loading from Iconify API
- Custom sizing (px, em, rem)
- Color theming via props or CSS
- Rotation and Flip
- Loading state (spin)
- Accessibility support
- Fallback icon support

## Usage

```vue
<script setup>
import BaseIcon from '@/shared/components/atoms/BaseIcon';
</script>

<template>
  <!-- Basic Usage -->
  <BaseIcon icon="mdi:home" />

  <!-- Custom Size and Color -->
  <BaseIcon icon="mdi:heart" size="32" color="red" />

  <!-- Rotation -->
  <BaseIcon icon="mdi:arrow-right" :rotate="90" />

  <!-- Spinning -->
  <BaseIcon icon="mdi:loading" spin />

  <!-- Fallback -->
  <BaseIcon icon="invalid:icon-name" fallback="mdi:alert" color="orange" />
</template>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `icon` | `string` | Required | Iconify icon name (e.g., 'mdi:home') |
| `size` | `string \| number` | `24` | Size in pixels (number) or CSS string |
| `color` | `string` | `undefined` | Icon color |
| `rotate` | `number \| string` | `undefined` | Rotation (0, 90, 180, 270) or string |
| `flip` | `string` | `undefined` | 'horizontal', 'vertical' |
| `spin` | `boolean` | `false` | Applies spin animation |
| `inline` | `boolean` | `false` | Aligns icon with text |
| `fallback` | `string` | `undefined` | Icon to show if primary fails |
| `ariaLabel` | `string` | `undefined` | Accessibility label |

## Common Icons

- Home: `mdi:home`
- Settings: `mdi:cog`
- User: `mdi:account`
- Delete: `mdi:trash`
- Edit: `mdi:pencil`
- Loading: `mdi:loading` (use with `spin` prop)
- Success: `mdi:check-circle`
- Error: `mdi:alert-circle`
- Warning: `mdi:alert`
- Info: `mdi:information`

## Performance Note

Icons are loaded on demand and cached by `@iconify/vue`. First load might have a slight delay depending on network.
