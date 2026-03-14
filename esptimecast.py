"""
ESPTimeCast Python Client Library

A Python client for interacting with ESPTimeCast LED matrix clock API.
https://github.com/mfactory-osaka/ESPTimeCast
"""

import requests
from typing import Optional, Dict, Any
import json


class ESPTimeCastException(Exception):
    """Base exception for ESPTimeCast client"""
    pass


class MessageProtectedException(ESPTimeCastException):
    """Raised when API returns 409 Conflict (protected message is currently displaying)"""
    pass


class InvalidConfigException(ESPTimeCastException):
    """Raised when configuration file is invalid"""
    pass


class ESPTimeCastClient:
    """
    Python client for ESPTimeCast API

    Args:
        host: IP address or hostname of ESPTimeCast device
        timeout: Request timeout in seconds (default: 10)

    Example:
        >>> client = ESPTimeCastClient("192.168.1.100")
        >>> client.send_message("HELLO WORLD", speed=50)
        {'status_code': 200, 'message': 'Message sent successfully'}
    """

    def __init__(self, host: str, timeout: int = 10):
        """
        Initialize ESPTimeCast client

        Args:
            host: IP address or hostname (e.g., "192.168.1.100")
            timeout: Request timeout in seconds
        """
        self.host = host
        self.base_url = f"http://{host}"
        self.timeout = timeout
        self._uptime_data = None  # Stores the device uptime information

    def send_message(
        self,
        message: str,
        speed: int = 85,
        seconds: int = 0,
        scrolltimes: int = 0,
        allow_interrupt: bool = True,
        large_nums: bool = False
    ) -> Dict[str, Any]:
        """
        Send custom message to ESPTimeCast display

        Args:
            message: Text to display (A-Z, 0-9, symbols). Empty string clears message.
                    Automatically converted to uppercase.
            speed: Scroll speed 10-200 (lower = faster). Default: 85
            seconds: Display duration 0-3600 seconds. 0 = infinite. Default: 0
            scrolltimes: Number of scroll cycles 0-100. 0 = infinite. Default: 0
            allow_interrupt: Allow new messages to interrupt this one. Default: True
            large_nums: Use large numbers font. Default: False

        Returns:
            dict: Response with 'status_code' and 'message' keys

        Raises:
            MessageProtectedException: When status code is 409 (protected message is active)
            ESPTimeCastException: On connection or HTTP errors

        Example:
            >>> client.send_message("HELLO", speed=50, seconds=10)
            >>> client.send_message("ALERT", allow_interrupt=False, scrolltimes=5)
        """
        url = f"{self.base_url}/set_custom_message"

        # Validate parameters
        if not isinstance(message, str):
            raise ValueError("message must be a string")
        if not (10 <= speed <= 200):
            raise ValueError("speed must be between 10 and 200")
        if not (0 <= seconds <= 3600):
            raise ValueError("seconds must be between 0 and 3600")
        if not (0 <= scrolltimes <= 100):
            raise ValueError("scrolltimes must be between 0 and 100")

        # Prepare form data
        data = {
            'message': message,
            'speed': speed,
            'seconds': seconds,
            'scrolltimes': scrolltimes,
            'allowInterrupt': 1 if allow_interrupt else 0,
            'largenums': 1 if large_nums else 0
        }

        try:
            response = requests.post(
                url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )

            if response.status_code == 409:
                raise MessageProtectedException(
                    "Display is busy showing a protected message. "
                    "Wait for it to finish or send a message with allow_interrupt=False to override."
                )

            response.raise_for_status()

            return {
                'status_code': response.status_code,
                'message': 'Message sent successfully'
            }

        except requests.exceptions.Timeout:
            raise ESPTimeCastException(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise ESPTimeCastException(f"Could not connect to {self.host}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 409:
                raise ESPTimeCastException(f"HTTP error: {e}")
            raise

    def export_config(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Download device configuration

        Args:
            output_path: Optional path to save config file (e.g., "config.json")
                        If None, returns config as dict without saving

        Returns:
            dict: Configuration data

        Raises:
            ESPTimeCastException: On connection or HTTP errors

        Example:
            >>> config = client.export_config("backup.json")
            >>> config = client.export_config()  # Just return, don't save
        """
        url = f"{self.base_url}/export"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            config = response.json()

            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(config, f, indent=2)

            return config

        except requests.exceptions.Timeout:
            raise ESPTimeCastException(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise ESPTimeCastException(f"Could not connect to {self.host}")
        except requests.exceptions.HTTPError as e:
            raise ESPTimeCastException(f"HTTP error: {e}")
        except json.JSONDecodeError:
            raise ESPTimeCastException("Invalid JSON response from device")

    def upload_config(self, config_path: str) -> Dict[str, Any]:
        """
        Upload configuration JSON file to device

        Note: Device will automatically reboot after successful upload

        Args:
            config_path: Path to config.json file

        Returns:
            dict: Response with 'status_code' and 'message' keys

        Raises:
            InvalidConfigException: If config file is invalid or cannot be read
            ESPTimeCastException: On connection or HTTP errors

        Example:
            >>> client.upload_config("config.json")
        """
        url = f"{self.base_url}/upload"

        try:
            with open(config_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(url, files=files, timeout=self.timeout)

            if response.status_code == 400:
                raise InvalidConfigException("Invalid configuration file")

            response.raise_for_status()

            return {
                'status_code': response.status_code,
                'message': 'Configuration uploaded successfully. Device will reboot.'
            }

        except FileNotFoundError:
            raise InvalidConfigException(f"Config file not found: {config_path}")
        except json.JSONDecodeError:
            raise InvalidConfigException(f"Invalid JSON in config file: {config_path}")
        except requests.exceptions.Timeout:
            raise ESPTimeCastException(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise ESPTimeCastException(f"Could not connect to {self.host}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 400:
                raise ESPTimeCastException(f"HTTP error: {e}")
            raise

    def clear_message(self) -> Dict[str, Any]:
        """
        Convenience method to clear current message

        Returns:
            dict: Response with 'status_code' and 'message' keys

        Example:
            >>> client.clear_message()
        """
        return self.send_message(message="")

    def send_protected_message(
        self,
        message: str,
        speed: int = 85,
        scrolltimes: int = 5
    ) -> Dict[str, Any]:
        """
        Convenience method to send a protected message that won't be interrupted

        Args:
            message: Text to display
            speed: Scroll speed 10-200 (lower = faster). Default: 85
            scrolltimes: Number of scroll cycles before expiring. Default: 5

        Returns:
            dict: Response with 'status_code' and 'message' keys

        Example:
            >>> client.send_protected_message("ALERT", speed=40, scrolltimes=10)
        """
        return self.send_message(
            message=message,
            speed=speed,
            scrolltimes=scrolltimes,
            allow_interrupt=False
        )

    def send_timed_message(
        self,
        message: str,
        seconds: int,
        speed: int = 85
    ) -> Dict[str, Any]:
        """
        Convenience method to send a message with time-based expiration

        Args:
            message: Text to display
            seconds: Display duration in seconds (1-3600)
            speed: Scroll speed 10-200 (lower = faster). Default: 85

        Returns:
            dict: Response with 'status_code' and 'message' keys

        Example:
            >>> client.send_timed_message("MEETING IN 5 MIN", seconds=300)
        """
        return self.send_message(
            message=message,
            speed=speed,
            seconds=seconds
        )

    def get_uptime(self, refresh: bool = False) -> Dict[str, Any]:
        """
        Get device uptime information and store it in the client instance

        Fetches and stores:
        - hostname: Device hostname
        - total_seconds: Total uptime in seconds since first boot
        - total_formatted: Total uptime formatted as "Xd HH:MM:SS"
        - session_seconds: Current session uptime in seconds
        - session_formatted: Current session uptime formatted as "HH:MM:SS"
        - version: Firmware version

        Args:
            refresh: If True, fetch fresh data from device. If False, return cached data if available.

        Returns:
            dict: Uptime data in JSON format

        Raises:
            ESPTimeCastException: On connection or HTTP errors

        Example:
            >>> uptime = client.get_uptime()
            >>> print(uptime)
            {'hostname': 'esptimecast', 'total_seconds': 151118, ...}
            >>> print(client.uptime_hostname)
            'esptimecast'
            >>> print(client.uptime_version)
            '1.4.0'
        """
        if self._uptime_data is None or refresh:
            url = f"{self.base_url}/uptime"

            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()

                self._uptime_data = response.json()

            except requests.exceptions.Timeout:
                raise ESPTimeCastException(f"Request timed out after {self.timeout} seconds")
            except requests.exceptions.ConnectionError:
                raise ESPTimeCastException(f"Could not connect to {self.host}")
            except requests.exceptions.HTTPError as e:
                raise ESPTimeCastException(f"HTTP error: {e}")
            except json.JSONDecodeError:
                raise ESPTimeCastException("Invalid JSON response from device")

        return self._uptime_data

    # Uptime property accessors
    @property
    def uptime_data(self) -> Optional[Dict[str, Any]]:
        """Get the cached uptime data (returns None if not yet fetched)"""
        return self._uptime_data

    @property
    def uptime_hostname(self) -> Optional[str]:
        """Get device hostname from uptime data. Returns None if uptime not loaded."""
        return self._uptime_data.get('hostname') if self._uptime_data else None

    @property
    def uptime_total_seconds(self) -> Optional[int]:
        """Get total uptime in seconds. Returns None if uptime not loaded."""
        return self._uptime_data.get('total_seconds') if self._uptime_data else None

    @property
    def uptime_total_formatted(self) -> Optional[str]:
        """Get total uptime formatted string. Returns None if uptime not loaded."""
        return self._uptime_data.get('total_formatted') if self._uptime_data else None

    @property
    def uptime_session_seconds(self) -> Optional[int]:
        """Get session uptime in seconds. Returns None if uptime not loaded."""
        return self._uptime_data.get('session_seconds') if self._uptime_data else None

    @property
    def uptime_session_formatted(self) -> Optional[str]:
        """Get session uptime formatted string. Returns None if uptime not loaded."""
        return self._uptime_data.get('session_formatted') if self._uptime_data else None

    @property
    def uptime_version(self) -> Optional[str]:
        """Get firmware version. Returns None if uptime not loaded."""
        return self._uptime_data.get('version') if self._uptime_data else None
