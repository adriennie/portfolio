# CrossBridge

> Apple Continuity for Everyone — Cross-platform ecosystem app bridging macOS and Android (phones + tablets)

---

## What Is CrossBridge

CrossBridge replicates 16 Apple Continuity features across macOS and Android devices using local-first, peer-to-peer architecture with zero mandatory cloud dependency.

**Target Devices:** macOS (13+), Android phones (12+), Android tablets (12+)

**Core Philosophy:** LAN-first. No database required. QR-based pairing. E2E encrypted.

---

## Features

| # | Feature | Method |

|---|---------|--------|
| 01 | NearShare (AirDrop) | P2P file transfer via WebRTC + BLE discovery |
| 02 | SyncBoard (Universal Clipboard) | Encrypted clipboard relay via LAN WebSocket |
| 03 | TaskBridge (Handoff) | App state + URL handoff via deep links |
| 04 | MirrorLink (Phone Mirroring) | Android screen to Mac via scrcpy over WiFi |
| 05 | ExtendDroid (Sidecar) | Android tablet as second Mac display |
| 06 | FlowControl (Universal Control) | Single keyboard/mouse across Mac + tablet |
| 07 | QuickTether (Instant Hotspot) | Remote hotspot activation via LAN broadcast |
| 08 | DroidCam Bridge (Continuity Camera) | Android rear camera as Mac webcam via RTSP |
| 09 | SketchRelay (Continuity Sketch) | Real-time canvas stroke sync to Mac |
| 10 | RingBridge (Calls & SMS) | Phone call + SMS relay to tablet/Mac |
| 11 | SyncVault (iCloud Drive) | CRDT-based E2EE file sync, no cloud required |
| 12 | StreamCast (AirPlay) | Screen/audio cast via WebRTC between devices |
| 13 | PinPoint (Find My) | Live GPS via WebSocket, no history stored |
| 14 | ZenSync (Focus Modes) | DND state broadcast across all linked devices |
| 15 | PassBeam (Wi-Fi Sharing) | BLE GATT encrypted credential handshake |
| 16 | ProximityUnlock (Auto Unlock) | BLE RSSI proximity unlock + biometric auth relay |

---

## Architecture

```bash
[Android Phone] ──BLE/WiFi──> [CrossBridge LAN Relay] <──BLE/WiFi── [Mac Desktop Agent]
                                        |
                               [Android Tablet]
```

- **No database.** Device pairing stored locally via QR-generated shared secret.
- **Relay:** Cloudflare Worker (WebSocket) for WAN fallback only. LAN-first always.
- **Encryption:** libsodium NaCl for all clipboard, file, and credential transfers.

---

## Tech Stack

| Layer | Technology |

|---|---|
| Android app | Kotlin, Jetpack Compose, CameraX, BLE API, camera2 |
| Mac desktop agent | Electron (Node.js) + Rust (HID input layer) |
| P2P transport | WebRTC via PeerJS, mDNS discovery |
| Relay (WAN fallback) | Cloudflare Workers + Durable Objects (free tier) |
| Auth + pairing | QR code, libsodium key exchange, local Keystore |
| File sync | Automerge (CRDT), Cloudflare R2 (optional) |
| Camera streaming | RTSP via GStreamer, virtual cam driver (Mac) |
| Screen mirroring | scrcpy over ADB TCP/IP |
| Notifications | Firebase FCM (free tier) |
| Maps (Find My) | Mapbox free tier |

---

## Project Structure

```bash
crossbridge/
├── android/
│   └── app/src/main/
│       ├── ble/              # BLE advertising + GATT server
│       ├── clipboard/        # ClipboardManager listener
│       ├── camera/           # CameraX + RTSP streaming
│       ├── mirror/           # scrcpy ADB bridge
│       ├── calls/            # TelecomManager + SMS relay
│       ├── sync/             # Automerge CRDT sync
│       └── ui/               # Jetpack Compose screens
├── mac-agent/
│   └── src/
│       ├── ble/              # CoreBluetooth via noble
│       ├── clipboard/        # macOS clipboard watcher
│       ├── hid/              # Rust HID layer (FlowControl)
│       ├── virtual-cam/      # Virtual camera driver
│       └── ui/               # Electron tray + settings
├── relay/
│   └── src/
│       ├── ws-relay.ts       # WebSocket room-based relay
│       └── signaling.ts      # WebRTC signaling server
├── shared/
│   ├── crypto/               # libsodium wrappers
│   ├── protocol/             # Message schema (TypeScript)
│   └── pairing/              # QR pairing handshake logic
└── docs/
    ├── PRD.md
    ├── TRD.md
    └── AI_RULES.md
```

---

## Getting Started

### Prerequisites

- macOS 13+ with Xcode CLI tools
- Android Studio Hedgehog or newer
- Node.js 20+
- Rust stable toolchain
- Wrangler CLI: `npm i -g wrangler`

### Setup

```bash
git clone https://github.com/your-org/crossbridge.git
cd crossbridge

# Shared deps
cd shared && npm install

# Mac agent
cd ../mac-agent && npm install && cargo build --release

# Relay
cd ../relay && npm install && wrangler dev

# Android: open /android folder in Android Studio, run on device
```

### Pairing Devices

1. Open CrossBridge on Mac → click "Add Device"
2. Scan the QR code shown in the Android CrossBridge app
3. Devices exchange libsodium public keys and store pairing locally

---

## Free Tier Usage

| Service | Free Limit | Usage |

|---|---|---|
| Cloudflare Workers | 100k req/day | WebSocket relay fallback |
| Cloudflare R2 | 10 GB | Optional file sync |
| Firebase FCM | Unlimited | Focus sync, call alerts |
| Mapbox | 50k loads/month | PinPoint GPS map |

---

## License

MIT License. See [LICENSE](LICENSE) for details.
