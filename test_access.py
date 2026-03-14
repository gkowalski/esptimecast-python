#!/usr/bin/env python3
# Quick Example of how to use the client
# Substitute your own IP address if name resolution doesn't work'
from esptimecast import ESPTimeCastClient
client = ESPTimeCastClient("esptimecast.local")
client.send_message("HELLO WORLD", speed=50)
client.clear_message()