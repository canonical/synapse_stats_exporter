#!/usr/bin/env python
"""Synapse Stats Exporter"""

import os
import time
from prometheus_client import start_http_server, Gauge
import requests

ENDPOINT_ROOMS = "_synapse/admin/v1/rooms?dir=f&from=0&limit=10"
ENDPOINT_USERS = "_synapse/admin/v2/users?deactivated=false&dir=f&from=0&guests=true&limit=10"


class SynapseStatsMetrics:
    """
    Represent Synapse statistics.
    """

    def __init__(self, base_url="http://localhost:8008", admin_token="", polling_interval_seconds=60):
        self.base_url = base_url
        self.admin_token = admin_token
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.synapse_total_rooms = Gauge("synapse_total_rooms", "Total number of rooms in Synapse server")
        self.synapse_total_users = Gauge("synapse_total_users", "Total number of users in Synapse server")

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from Synapse and refresh Prometheus metrics with
        new values.
        """

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response = requests.get(f'{self.base_url}{ENDPOINT_ROOMS}', headers=headers)
        data = response.json()
        self.synapse_total_rooms.set(data["total_rooms"])
        response = requests.get(f'{self.base_url}{ENDPOINT_USERS}', headers=headers)
        data = response.json()
        self.synapse_total_users.set(data["total"])


def main():
    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
    base_url = os.getenv("PROM_SYNAPSE_BASE_URL", "http://localhost:8008")
    admin_token = os.getenv("PROM_SYNAPSE_ADMIN_TOKEN", "password")
    exporter_port = int(os.getenv("EXPORTER_PORT", "9877"))

    synapse_stats_metrics = SynapseStatsMetrics(
        base_url=base_url,
        admin_token=admin_token,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    synapse_stats_metrics.run_metrics_loop()


if __name__ == "__main__":
    main()
