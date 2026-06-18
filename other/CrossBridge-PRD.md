# CrossBridge — Product & Technical Requirements Document

**Version:** 1.0  
**Audience:** AI coding assistants (Cursor, GitHub Copilot, Codex), developers  
**Platforms:** macOS 13+, Android 12+ (phone + tablet)  
**Tools:** Cursor free tier, GitHub Copilot (Student Pack), Antigravity, Google Codex  

---

## PART 1 — PRODUCT REQUIREMENTS (PRD)

### 1.1 Product Goal

Build a free, open-source, local-first cross-platform continuity app that replicates Apple's Continuity ecosystem features between macOS and Android devices (phones and tablets). No mandatory cloud backend. No user accounts required. Database-free by design.

---

### 1.2 User Personas

**Persona A — The Mixed-Device Professional**

- Uses MacBook for work, Android phone (personal preference or budget)
- Pain: Cannot use AirDrop, Handoff, Universal Clipboard, or Continuity Camera with Android
- Wants: Seamless workflow continuity without switching ecosystems

**Persona B — The Student Developer**

- Budget-constrained, uses free-tier tools only
- Wants: Self-hostable, zero subscription, open source

---

### 1.3 Non-Goals

- No iOS support in v1 (Apple locks cross-platform Continuity APIs)
- No paid cloud relay (Cloudflare free tier only)
- No biometric data stored remotely (ProximityUnlock auth stays on-device)
- No user account system (QR pairing only)

---

### 1.4 Feature Requirements

#### F-01: NearShare (AirDrop)

**Priority:** P0  
**Description:** Transfer files, photos, videos, links between any two paired CrossBridge devices on the same LAN or BLE range.  
**Acceptance Criteria:**

- Transfer speed minimum 10 MB/s on LAN
- File size limit: 2 GB
- Works with no internet connection
- Progress indicator shown on both sender and receiver
- Receiver gets accept/decline prompt

---

#### F-02: SyncBoard (Universal Clipboard)

**Priority:** P0  
**Description:** Copy on one device, paste on any other paired device.  
**Acceptance Criteria:**

- Sync latency under 500 ms on LAN
- Supports text, images (PNG/JPEG up to 5 MB), URLs
- E2E encrypted (libsodium)
- Auto-expires clipboard content after 60 seconds

---

#### F-03: TaskBridge (Handoff)

**Priority:** P1  
**Description:** Resume active task (browser tab, document, email draft) from one device on another.  
**Acceptance Criteria:**

- Receiving device shows notification within 2 seconds of sender opening supported app
- Supported apps: browser, email client, note apps with URI scheme support
- Deep link opens correct app state on receiver

---

#### F-04: MirrorLink (Phone Mirroring)

**Priority:** P1  
**Description:** Full Android phone screen visible and controllable from Mac desktop.  
**Acceptance Criteria:**

- Wireless via ADB over TCP/IP (no USB required after initial setup)
- Touch input forwarded from Mac to Android
- Latency under 100 ms on local WiFi
- Resolution minimum 1080p at 30 fps

---

#### F-05: ExtendDroid (Sidecar)

**Priority:** P2  
**Description:** Android tablet acts as second display for Mac (extend or mirror).  
**Acceptance Criteria:**

- Extend mode: Mac cursor moves to tablet screen at screen edge
- Mirror mode: Mac display duplicated on tablet
- Minimum 720p at 30 fps wirelessly
- Touch on tablet maps to mouse events on Mac

---

#### F-06: FlowControl (Universal Control)

**Priority:** P2  
**Description:** One Mac keyboard and trackpad/mouse seamlessly controls Mac and Android tablet.  
**Acceptance Criteria:**

- Cursor slides from Mac to tablet by crossing screen edge
- Keyboard input follows cursor position
- Clipboard shared between Mac and controlled tablet
- Works on LAN without USB

---

#### F-07: QuickTether (Instant Hotspot)

**Priority:** P1  
**Description:** Activate Android hotspot remotely from Mac/tablet, auto-connect without password entry.  
**Acceptance Criteria:**

- Phone hotspot starts within 3 seconds of trigger from Mac
- Mac/tablet auto-joins hotspot using pre-shared credentials
- Requires Android TetheringManager API (Android 12+)

---

#### F-08: DroidCam Bridge (Continuity Camera)

**Priority:** P1  
**Description:** Android rear camera used as high-quality webcam on Mac.  
**Acceptance Criteria:**

- Appears as virtual camera device in Mac (selectable in Zoom, Meet, OBS)
- Minimum 1080p 30 fps
- Wireless via WiFi, RTSP stream
- One-click connect from Mac menu bar

---

#### F-09: SketchRelay (Continuity Sketch)

**Priority:** P2  
**Description:** Draw or annotate on Android tablet/phone, result appears in real-time on Mac app.  
**Acceptance Criteria:**

- Stroke coordinates, pressure, tool type synced in real-time
- Latency under 80 ms
- Output embeddable in PDF, image files on Mac
- Supports stylus pressure sensitivity

---

#### F-10: RingBridge (Calls & SMS Forwarding)

**Priority:** P1  
**Description:** Answer/reject phone calls and send/receive SMS on Mac or tablet from Android phone.  
**Acceptance Criteria:**

- Incoming call notification appears on Mac/tablet within 2 seconds
- Answer from Mac plays audio over Mac speakers + mic
- SMS threads visible and writable from Mac
- Works on LAN; phone is source of truth for cellular

---

#### F-11: SyncVault (File & Data Sync)

**Priority:** P0  
**Description:** Sync files, notes, clipboard history across all paired devices.  
**Acceptance Criteria:**

- CRDT-based conflict resolution (Automerge)
- E2E encrypted before any transfer
- LAN sync without internet
- Optional Cloudflare R2 upload for WAN sync (user opt-in)

---

#### F-12: StreamCast (AirPlay)

**Priority:** P2  
**Description:** Cast audio, video, or mirror screen from Android to Mac or Mac to Android.  
**Acceptance Criteria:**

- Video: H.264 at minimum 720p 30 fps
- Audio: AAC stereo
- Latency under 200 ms
- Receiver renders fullscreen with playback controls

---

#### F-13: PinPoint (Find My)

**Priority:** P2  
**Description:** Real-time GPS location of all paired devices visible from any other paired device.  
**Acceptance Criteria:**

- Location updates every 5 seconds when app is active
- Live map view using Mapbox free tier
- No location history stored — live only
- Works over WAN via Cloudflare relay

---

#### F-14: ZenSync (Focus Mode Sync)

**Priority:** P1  
**Description:** Activating DND or custom focus on one device silences all other paired devices.  
**Acceptance Criteria:**

- State change propagated to all paired devices within 1 second
- Supports: DND, Work, Sleep, Personal modes
- Per-device override allowed

---

#### F-15: PassBeam (Wi-Fi Password Sharing)

**Priority:** P2  
**Description:** Share Wi-Fi credentials securely to a nearby paired device via BLE.  
**Acceptance Criteria:**

- BLE GATT handshake verifies device trust before sharing
- Credentials encrypted with libsodium
- Receiving device auto-joins the network
- No credentials stored in app after transfer

---

#### F-16: ProximityUnlock (Auto Unlock + Auth Relay)

**Priority:** P2  
**Description:** Mac unlocks when paired Android phone is nearby. Android biometric relays authorization to Mac for payments.  
**Acceptance Criteria:**

- RSSI threshold configurable by user (default: 1 meter)
- Mac locks again when phone moves away (configurable)
- BiometricPrompt result sent as signed token to Mac agent
- Token valid for 30 seconds only

---

### 1.5 UX Requirements

- **Onboarding:** QR scan pairing in under 30 seconds
- **Tray app:** Mac agent lives in menu bar, zero dock presence
- **Android app:** Persistent foreground service with minimal notification
- **Color system:** Dark mode first, Deep Navy + Electric Teal accent
- **Typography:** Inter (UI), JetBrains Mono (status/technical readouts)
- **Animations:** Functional only — no decorative motion that adds latency
- **Accessibility:** WCAG AA minimum contrast, screen reader labels on all interactive elements

---

## PART 2 — TECHNICAL REQUIREMENTS (TRD)

### 2.1 Platform Targets

| Platform | Min Version | Reason |

|---|---|---|
| Android | 12 (API 31) | TetheringManager, BLE enhanced features |
| macOS | 13 Ventura | Bluetooth updates, Metal rendering |
| Electron | 30+ | Node.js 20 LTS, ESM modules |

---

### 2.2 Android Technical Specifications

#### Core Services (always running)

```kotlin
// Foreground service — required for all background continuity features
class CrossBridgeService : Service() {
    // Manages: BLE, clipboard listener, call observer, location, WebSocket
}
```

#### BLE Stack

- Advertise as GATT peripheral with CrossBridge UUID
- UUID format: `CB000000-0000-0000-0000-[6-byte device ID]`
- GATT characteristics per feature (clipboard, unlock, Wi-Fi share)
- Use `BluetoothLeAdvertiser` for advertising, `BluetoothGattServer` for server

#### Clipboard Sync

```kotlin
// Poll ClipboardManager every 500ms (Android 10+ blocks listener)
// On change: encrypt with libsodium box, push to LAN relay socket
val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
```

#### Camera Streaming (DroidCam Bridge)

```bash
camera2 API -> ImageReader (YUV_420_888) -> MediaCodec (H.264) -> RTP/RTSP
```

- Use `Camera2` not `CameraX` for raw frame access
- MediaCodec hardware encoder mandatory (software too slow)
- RTSP server: embed `net.majorkernelpanic:streaming` library

#### Screen Mirroring (MirrorLink)

- ADB over TCP/IP: `adb tcpip 5555` then `adb connect [device-ip]`
- Use scrcpy server JAR pushed to device via ADB
- Control channel: separate TCP socket for input events

#### Calls & SMS (RingBridge)

```kotlin
// Call monitoring
class CallReceiver : BroadcastReceiver() {
    // ACTION_PHONE_STATE_CHANGED -> relay via WebSocket
}

// SMS monitoring  
contentResolver.registerContentObserver(
    Uri.parse("content://sms"), true, SmsObserver()
)
```

#### Permissions Required (Android)

```xml
BLUETOOTH_ADVERTISE, BLUETOOTH_CONNECT, BLUETOOTH_SCAN
ACCESS_FINE_LOCATION (BLE scanning)
CAMERA, RECORD_AUDIO (DroidCam Bridge)
READ_PHONE_STATE, READ_CALL_LOG (RingBridge)
RECEIVE_SMS, READ_SMS, SEND_SMS (RingBridge)
FOREGROUND_SERVICE, FOREGROUND_SERVICE_CONNECTED_DEVICE
CHANGE_NETWORK_STATE (QuickTether)
ACCESS_WIFI_STATE, CHANGE_WIFI_STATE
```

---

### 2.3 Mac Agent Technical Specifications

#### Electron Architecture

```bash
main process: BLE (noble), mDNS, WebSocket client, clipboard watcher, ADB manager
renderer process: Tray UI, settings panel, device list
preload: IPC bridge between main and renderer
```

#### BLE on Mac

- Use `@abandonware/noble` (CoreBluetooth wrapper for Node.js)
- Scan for CrossBridge UUID on app start
- RSSI polling for ProximityUnlock every 500 ms

#### Clipboard Watcher (Mac)

```javascript
// Poll macOS clipboard via native module
const { clipboard } = require('electron')
setInterval(() => {
  const text = clipboard.readText()
  if (text !== lastClipboard) syncClipboard(text)
}, 500)
```

#### Virtual Camera (DroidCam Bridge)

- Mac: Install OBS Virtual Camera or use `v4l2loopback` equivalent
- Pipe RTSP stream from Android into virtual camera device
- GStreamer pipeline: `rtspsrc -> decodebin -> videoconvert -> v4l2sink`

#### HID Input Layer (FlowControl)

- Written in Rust: `crossbridge-hid` crate
- Uses `CGEventPost` (macOS) to inject mouse/keyboard events
- Communicates with Electron main via stdio pipe
- Android side: `AccessibilityService` for input injection

#### Rust Crate Interface

```rust
// crossbridge-hid/src/lib.rs
pub fn inject_mouse_move(x: f64, y: f64) -> Result<()>
pub fn inject_key_event(keycode: u32, down: bool) -> Result<()>
pub fn get_display_bounds() -> (f64, f64)
```

---

### 2.4 Relay Server (Cloudflare Worker)

#### WebSocket Room Design

```typescript
// Each paired device group = one Durable Object room
// Room ID = SHA256(sorted device public keys)
export class RelayRoom {
  peers: Map<string, WebSocket>
  
  handleMessage(sender: string, data: ArrayBuffer) {
    // Broadcast to all peers except sender
    // Never decrypt — relay is transport only
  }
}
```

#### Signaling (WebRTC)

```typescript
// /signal endpoint for WebRTC offer/answer/ICE exchange
// Messages: { type: 'offer'|'answer'|'ice', from: string, to: string, payload: any }
```

#### Endpoints

| Method | Path | Purpose |

|---|---|---|
| WS | `/relay/:roomId` | Encrypted message relay |
| POST | `/signal` | WebRTC signaling |
| GET | `/ping` | Health check |

---

### 2.5 Pairing Protocol

```bash
1. Device A generates: keypair (libsodium box_keypair)
2. Device A displays QR: { pubkey_a, room_id, relay_url }
3. Device B scans QR, generates keypair_b
4. Device B sends: { pubkey_b } encrypted with pubkey_a to relay room
5. Device A decrypts, verifies, stores pubkey_b in local Keystore
6. Both devices now share: room_id, each other's pubkey
7. All future messages: libsodium box(message, their_pubkey, my_privkey)
```

No server stores keys. Relay only sees ciphertext.

---

### 2.6 CRDT Sync (SyncVault)

```typescript
// Using Automerge 2.x
import * as Automerge from '@automerge/automerge'

// Each device holds full document replica
// Changes encoded as binary patches, broadcast to peers
// Conflict resolution: last-write-wins per field (Automerge default)
```

---

### 2.7 Performance Budgets

| Feature | Max Latency | Max CPU (Android) | Max Battery/hr |

|---|---|---|---|
| SyncBoard | 500 ms | 2% | 15 mAh |
| MirrorLink | 100 ms | 35% | 180 mAh |
| DroidCam Bridge | 80 ms | 40% | 200 mAh |
| SketchRelay | 80 ms | 5% | 20 mAh |
| NearShare | N/A (throughput) | 20% | 100 mAh |
| PinPoint | 5 sec intervals | 1% | 10 mAh |

---

### 2.8 Security Requirements

- All LAN messages: libsodium `crypto_box` (Curve25519 + XSalsa20 + Poly1305)
- No plaintext over network — ever
- Pairing keys stored in Android Keystore + macOS Keychain
- Relay server: zero-knowledge (cannot decrypt any message)
- ProximityUnlock token: HMAC-SHA256, 30-second TTL
- PassBeam credentials: never persisted after handshake

---

### 2.9 Build & CI

```yaml
# GitHub Actions (free tier)
on: [push, pull_request]
jobs:
  android:
    runs-on: ubuntu-latest
    steps: [checkout, setup-java, gradle-build, android-lint]
  mac-agent:
    runs-on: macos-latest
    steps: [checkout, node-setup, cargo-build, electron-build]
  relay:
    runs-on: ubuntu-latest
    steps: [checkout, node-setup, wrangler-dry-run]
```

---

### 2.10 Tool-Specific Usage Guide

#### Cursor (Free Tier)

- Open each module folder as separate Cursor workspace to stay within context limits
- Use `Cmd+K` for: generating BLE GATT boilerplate, Android service skeletons, Rust HID functions
- Use `Cmd+L` (chat) for: architecture questions, debugging WebRTC signaling, reviewing protocol logic
- Tag `@codebase` when asking about cross-module integration

#### GitHub Copilot (Student Pack)

- Best for: inline autocomplete of repetitive Android API code (permissions, manifest entries, Kotlin coroutines)
- Use Copilot Chat (`Ctrl+I`) for: explaining unfamiliar APIs (TetheringManager, camera2, AccessibilityService)
- Write clear function signatures + JSDoc/KDoc comments before accepting suggestions

#### Antigravity

- Use for: full-feature scaffolding when starting a new module from scratch
- Input: paste the relevant PRD feature section + TRD spec section as prompt context
- Output: review generated code against TRD before committing

#### Google Codex

- Use for: generating test cases, debugging complex async code, protocol message schema validation
- Workflow: paste protocol spec section -> ask Codex to generate unit tests
- Pipe source files directly: `cat src/ws-relay.ts | codex "find race conditions in broadcast logic"`
