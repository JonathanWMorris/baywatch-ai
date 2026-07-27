/// <reference types="vite/client" />

interface BluetoothDevice {
  name?: string;
  gatt?: BluetoothRemoteGATTServer;
}

interface BluetoothRemoteGATTServer {
  connected: boolean;
  connect(): Promise<BluetoothRemoteGATTServer>;
  disconnect(): void;
  getPrimaryService(service: string): Promise<BluetoothRemoteGATTService>;
}

interface BluetoothRemoteGATTService {
  getCharacteristic(characteristic: string): Promise<BluetoothRemoteGATTCharacteristic>;
}

interface BluetoothRemoteGATTCharacteristic {
  value?: DataView;
  startNotifications(): Promise<BluetoothRemoteGATTCharacteristic>;
  addEventListener(type: string, listener: (event: Event) => void): void;
  writeValueWithoutResponse(value: BufferSource): Promise<void>;
}

interface Navigator {
  bluetooth: {
    requestDevice(options: {
      filters?: Array<{namePrefix?: string; name?: string}>;
      optionalServices?: string[];
    }): Promise<BluetoothDevice>;
  };
}
