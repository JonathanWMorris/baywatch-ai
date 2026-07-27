// Web Bluetooth API Integration for Physical Lifeguard Hand & Marine BLE Hardware

export const SERVICE_UUID = "0000fa10-0000-1000-8000-00805f9b34fb";
export const TELEMETRY_CHAR_UUID = "0000fa11-0000-1000-8000-00805f9b34fb";
export const HAPTIC_CHAR_UUID = "0000fa12-0000-1000-8000-00805f9b34fb";
export const GESTURE_CHAR_UUID = "0000fa13-0000-1000-8000-00805f9b34fb";

export interface BLEConnectionState {
  connected: boolean;
  deviceName: string | null;
  error: string | null;
}

class BLEManager {
  private device: BluetoothDevice | null = null;
  private server: BluetoothRemoteGATTServer | null = null;
  private hapticChar: BluetoothRemoteGATTCharacteristic | null = null;
  private onTelemetryCallback: ((data: Uint8Array) => void) | null = null;
  private onGestureCallback: ((gestureCode: number) => void) | null = null;

  public isSupported(): boolean {
    return typeof window !== "undefined" && "bluetooth" in navigator;
  }

  public async connect(
    onTelemetry: (data: Uint8Array) => void,
    onGesture: (gestureCode: number) => void,
  ): Promise<string> {
    if (!this.isSupported()) {
      throw new Error("Web Bluetooth API is not supported in this browser. Use Chrome, Edge, or Android WebViews.");
    }

    this.onTelemetryCallback = onTelemetry;
    this.onGestureCallback = onGesture;

    this.device = await navigator.bluetooth.requestDevice({
      filters: [{namePrefix: "Guard"}, {namePrefix: "Hand"}, {namePrefix: "Baywatch"}],
      optionalServices: [SERVICE_UUID],
    });

    if (!this.device.gatt) {
      throw new Error("GATT server unavailable on selected BLE device.");
    }

    this.server = await this.device.gatt.connect();
    const service = await this.server.getPrimaryService(SERVICE_UUID);

    // Subscribe to telemetry characteristic notifications
    try {
      const telemChar = await service.getCharacteristic(TELEMETRY_CHAR_UUID);
      await telemChar.startNotifications();
      telemChar.addEventListener("characteristicvaluechanged", (event: Event) => {
        const target = event.target as unknown as BluetoothRemoteGATTCharacteristic;
        if (target.value && this.onTelemetryCallback) {
          const buffer = new Uint8Array(target.value.buffer);
          this.onTelemetryCallback(buffer);
        }
      });
    } catch {
      // Characteristic optional depending on device configuration
    }

    // Subscribe to gesture characteristic notifications
    try {
      const gestureChar = await service.getCharacteristic(GESTURE_CHAR_UUID);
      await gestureChar.startNotifications();
      gestureChar.addEventListener("characteristicvaluechanged", (event: Event) => {
        const target = event.target as unknown as BluetoothRemoteGATTCharacteristic;
        if (target.value && this.onGestureCallback) {
          const gestureCode = target.value.getUint8(0);
          this.onGestureCallback(gestureCode);
        }
      });
    } catch {
      // Characteristic optional
    }

    // Get haptic control characteristic for write operations
    try {
      this.hapticChar = await service.getCharacteristic(HAPTIC_CHAR_UUID);
    } catch {
      this.hapticChar = null;
    }

    return this.device.name || "Lifeguard BLE Hand Device";
  }

  public async sendHaptic(patternId: number, intensity: number, durationMs: number): Promise<boolean> {
    if (!this.server || !this.server.connected || !this.hapticChar) {
      return false;
    }

    // 6-byte packed C struct: [pattern_id(uint8), intensity(uint8), duration(uint16_be), freq(uint16_be)]
    const buffer = new ArrayBuffer(6);
    const view = new DataView(buffer);
    view.setUint8(0, patternId);
    view.setUint8(1, intensity);
    view.setUint16(2, durationMs, false);
    view.setUint16(4, 200, false); // Default 200 Hz for LRA motor

    await this.hapticChar.writeValueWithoutResponse(buffer);
    return true;
  }

  public disconnect() {
    if (this.device && this.device.gatt && this.device.gatt.connected) {
      this.device.gatt.disconnect();
    }
    this.device = null;
    this.server = null;
    this.hapticChar = null;
  }
}

export const bleManager = new BLEManager();
