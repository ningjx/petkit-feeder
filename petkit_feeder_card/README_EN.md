# PetKit Feeder Lovelace Card

English | [简体中文](README.md)

A Home Assistant Lovelace card designed for PetKit smart feeders.

## Preview

![Card Preview](../docs/card.png)

## Features

- **Feeding Schedule Management** - Visually manage weekly feeding schedules with support for adding, editing, and deleting
- **Feeding History** - Track feeding details, showing planned vs actual amounts
- **Manual Feeding** - One-click food dispensing
- **Status Monitoring** - Real-time device status, WiFi signal, desiccant status
- **Weekly View** - Quick navigation between different days

## Interaction

| Action           | Effect                |
|------------------|-----------------------|
| Click time       | Edit time             |
| Click name       | Edit name             |
| Click amount     | Edit portion size     |
| Click toggle     | Enable/disable plan   |
| Click delete     | Delete plan           |
| Focus out        | Auto save             |
| ESC              | Cancel edit           |
| Click dashed box | Add new plan          |

## Prerequisites

1. Home Assistant (2024.1.0 or higher)
2. [PetKit Feeder Integration](../README_EN.md) installed
3. PetKit feeder device configured

## Installation

The card ships with the [PetKit Feeder Integration](../README_EN.md#installation). Install the integration and restart Home Assistant, then add the card configuration below. See the [integration README](../README_EN.md#lovelace-card) for standalone card migration and YAML resource setup.

## Configuration

```yaml
type: custom:petkit-feeder-card
device_id: "YOUR_DEVICE_ID"
```

> 💡 **Tip**: The `device_id` can be found in the "Device ID" sensor of your PetKit device in Home Assistant.

### Configuration Options

| Parameter        | Type    | Required | Default       | Description                |
|------------------|---------|----------|---------------|----------------------------|
| `device_id`      | string  | Yes*     | -             | Device ID                  |
| `entity`         | string  | No       | Auto-inferred | Feeding plan sensor        |
| `history_entity` | string  | No       | Auto-inferred | History record sensor      |
| `name`           | string  | No       | Device name   | Card title                 |
| `show_timeline`  | bool    | No       | true          | Show timeline              |
| `show_summary`   | bool    | No       | true          | Show statistics            |
| `show_actions`   | bool    | No       | true          | Show action buttons        |

*Either `device_id` or `entity` is required

## Supported Devices

| Device             | Model | Status            |
|--------------------|-------|-------------------|
| Fresh Element Solo | D4    | ✅ Supported      |
| Fresh Element      | D3    | 🚧 Not Supported  |
| Fresh Element Duo  | D4s   | 🚧 Not Supported  |
| Feeder Mini        | Mini  | 🚧 Not Supported  |

## Development

From the repository root, enter the card directory and build with Node.js 24.

```bash
cd petkit_feeder_card
npm ci --ignore-scripts
npm run build
```

The build writes `dist/petkit-feeder-card.js`. Use `npm start` to rebuild when source files change.

## Disclaimer

- This is not an official PetKit product
- API may change without notice

## License

MIT
