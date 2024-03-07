#!/usr/bin/env python
"""Synapse Stats Exporter"""

import json
import os
import time
from prometheus_client import start_http_server, Gauge
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

ENDPOINT_ROOMS = "_synapse/admin/v1/rooms?dir=f&from=0&limit=10"
ENDPOINT_USERS = "_synapse/admin/v2/users?deactivated=false&dir=f&from=0&guests=true&limit=10"


class SynapseStatsMetrics:
    """
    Represent Synapse statistics.
    """

    def __init__(self, base_url="http://localhost:8008/", admin_token="", polling_interval_seconds=60):
        self.base_url = base_url
        self.admin_token = admin_token
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.synapse_total_rooms = Gauge("synapse_total_rooms", "Total number of rooms in Synapse server")
        self.synapse_total_users = Gauge("synapse_total_users", "Total number of users in Synapse server")

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        print("Synapse Stats Exporter started.")
        while True:
            print("Synapse Stats Exporter will fetch statistics. Next polling in %d seconds.", self.polling_interval_seconds)
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from Synapse and refresh Prometheus metrics with
        new values.
        """
        try:
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            response = requests.get(f'{self.base_url}{ENDPOINT_ROOMS}', headers=headers)
            response.raise_for_status()
            data = response.json()
            self.synapse_total_rooms.set(data["total_rooms"])
            response = requests.get(f'{self.base_url}{ENDPOINT_USERS}', headers=headers)
            data = response.json()
            self.synapse_total_users.set(data["total"])
        except requests.exceptions.RequestException as e:
            print(f"Fetch request failed. Exception: {e}")
        except (json.decoder.JSONDecodeError, KeyError) as e:
            print(f"Fetch read failed. Exception: {e}")

def login(base_url, user, password):
    url = base_url + "_synapse/client/r0/login"
    data = {
        "type": "m.login.password",
        "user": user,
        "password": password
    }
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=3,
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    try:
        response = session.request("POST", url, json=data, timeout=5)
        response.raise_for_status()
        response_data = response.json()
        if "access_token" in response_data:
            access_token = response_data["access_token"]
            return access_token
        else:
            print("Login failed. Access token not found in response.")
    except requests.exceptions.RequestException as e:
        print(f"Login failed. Exception: {e}")
    finally:
        session.close()

def main():
    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
    base_url = os.getenv("PROM_SYNAPSE_BASE_URL", "http://localhost:8008/")
    user = os.getenv("PROM_SYNAPSE_USER", "user")
    password = os.getenv("PROM_SYNAPSE_USER", "password")
    exporter_port = int(os.getenv("EXPORTER_PORT", "9877"))

    admin_token = login(base_url=base_url, user=user, password=password)

    print("Login succeed. Synapse Stats Exporter will be started.")
    synapse_stats_metrics = SynapseStatsMetrics(
        base_url=base_url,
        admin_token=admin_token,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    synapse_stats_metrics.run_metrics_loop()


if __name__ == "__main__":
    main()
