from State import State
from SimpleDevice import SimpleDevice
from My_States import LockedState, UnlockedState


if __name__ == "__main__":
    device = SimpleDevice()
    device.on_event('device_locked')
    device.on_event('pin_entered')
    print(device.state)
