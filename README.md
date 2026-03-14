# ESPTimeCast Python Client

A Python client library for interacting with the [ESPTimeCast](https://github.com/mfactory-osaka/ESPTimeCast) LED matrix clock API.

## Installation

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from esptimecast import ESPTimeCastClient

# Initialize client with your device's IP address
client = ESPTimeCastClient("192.168.1.100")

# Send a simple message
client.send_message("HELLO WORLD")

# Send a message with custom speed
client.send_message("HELLO WORLD", speed=50)

# Send a timed message (displays for 30 seconds)
client.send_timed_message("MEETING IN 5 MIN", seconds=30)

# Send a protected message (won't be interrupted)
client.send_protected_message("ALERT", scrolltimes=5)

# Clear the current message
client.clear_message()
```

## Features

- **Send custom messages** to your ESPTimeCast display
- **Control scroll speed**, duration, and behavior
- **Protected messages** that won't be interrupted
- **Export/import** device configuration
- **Simple exception handling** for common errors

## API Reference

### ESPTimeCastClient

#### `__init__(host: str, timeout: int = 10)`

Initialize the client.

**Parameters:**
- `host`: IP address or hostname of your ESPTimeCast device
- `timeout`: Request timeout in seconds (default: 10)

#### `send_message(message, speed=85, seconds=0, scrolltimes=0, allow_interrupt=True, large_nums=False)`

Send a custom message to the display.

**Parameters:**
- `message`: Text to display (A-Z, 0-9, symbols). Empty string clears the message.
- `speed`: Scroll speed 10-200, lower = faster (default: 85)
- `seconds`: Display duration 0-3600 seconds, 0 = infinite (default: 0)
- `scrolltimes`: Number of scroll cycles 0-100, 0 = infinite (default: 0)
- `allow_interrupt`: Allow new messages to interrupt this one (default: True)
- `large_nums`: Use large numbers font (default: False)

**Returns:** `dict` with `status_code` and `message`

**Raises:**
- `MessageProtectedException`: When a protected message is currently displaying (HTTP 409)
- `ESPTimeCastException`: On connection or HTTP errors

**Examples:**

```python
# Basic message
client.send_message("HELLO WORLD")

# Fast scrolling message
client.send_message("URGENT", speed=30)

# Message that displays for 60 seconds
client.send_message("TEMPERATURE 72F", seconds=60)

# Message that scrolls 3 times then disappears
client.send_message("NOTIFICATION", scrolltimes=3)

# Protected message that won't be interrupted
client.send_message("CRITICAL ALERT", allow_interrupt=False, scrolltimes=10)

# Message with both time and scroll limits (whichever comes first)
client.send_message("TEST", seconds=120, scrolltimes=5)
```

#### `send_timed_message(message, seconds, speed=85)`

Convenience method to send a message with time-based expiration.

**Parameters:**
- `message`: Text to display
- `seconds`: Display duration in seconds (1-3600)
- `speed`: Scroll speed (default: 85)

**Example:**

```python
client.send_timed_message("MEETING STARTS NOW", seconds=300)
```

#### `send_protected_message(message, speed=85, scrolltimes=5)`

Convenience method to send a protected message that won't be interrupted.

**Parameters:**
- `message`: Text to display
- `speed`: Scroll speed (default: 85)
- `scrolltimes`: Number of scroll cycles (default: 5)

**Example:**

```python
client.send_protected_message("DOOR OPEN", scrolltimes=10)
```

#### `clear_message()`

Clear the current message from the display.

**Example:**

```python
client.clear_message()
```

#### `export_config(output_path=None)`

Download device configuration.

**Parameters:**
- `output_path`: Optional path to save config file. If None, returns config without saving.

**Returns:** `dict` with configuration data

**Examples:**

```python
# Save to file
config = client.export_config("backup.json")

# Just get the config as dict
config = client.export_config()
print(config)
```

#### `upload_config(config_path)`

Upload configuration file to device. Device will reboot after upload.

**Parameters:**
- `config_path`: Path to config.json file

**Raises:**
- `InvalidConfigException`: If config file is invalid

**Example:**

```python
client.upload_config("new_config.json")
```

## Exception Handling

```python
from esptimecast import ESPTimeCastClient, MessageProtectedException
import time

client = ESPTimeCastClient("192.168.1.100")

# Handle protected message conflicts with retry
for attempt in range(5):
    try:
        client.send_message("NOTIFICATION")
        break
    except MessageProtectedException:
        print(f"Display busy, retrying... (attempt {attempt+1}/5)")
        time.sleep(10)
else:
    print("Failed to send message after 5 attempts")
```

## Home Automation Examples

### Send notification on event

```python
from esptimecast import ESPTimeCastClient

client = ESPTimeCastClient("192.168.1.100")

def on_doorbell():
    client.send_message("DOORBELL", speed=40, seconds=10)

def on_temperature_alert(temp):
    client.send_protected_message(
        f"TEMP {temp}F",
        scrolltimes=5
    )
```

### Scheduled messages

```python
import schedule
import time
from esptimecast import ESPTimeCastClient

client = ESPTimeCastClient("192.168.1.100")

def morning_message():
    client.send_timed_message("GOOD MORNING", seconds=30)

def evening_message():
    client.send_timed_message("GOOD EVENING", seconds=30)

schedule.every().day.at("07:00").do(morning_message)
schedule.every().day.at("18:00").do(evening_message)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Supported Characters

The display supports:
- Uppercase letters: A-Z (lowercase automatically converted)
- Numbers: 0-9
- Symbols: `: ! ' . , _ + % / ? [ ] ° # @ ^ ~ * = < > { } \ - & $ |`
- Spaces

## Message Behavior

- **Short messages** (≤8 characters): Display static and centered
- **Long messages**: Scroll across the display
- **Protected messages** (`allow_interrupt=False`): Won't be replaced by new messages unless the new message is also protected
- **Multiple conditions**: When both `seconds` and `scrolltimes` are set, message expires when the first condition is met

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

MIT License

## Credits

This library interfaces with the [ESPTimeCast](https://github.com/mfactory-osaka/ESPTimeCast) project by mfactory-osaka.
