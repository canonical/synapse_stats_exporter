#!/usr/bin/env python
"""Synapse Stats Exporter"""

import psycopg2
from psycopg2 import pool
import os
import time
from prometheus_client import start_http_server, Gauge

class SynapseStatsMetrics:
    """
    Represent Synapse statistics.
    """

    def __init__(self, dbname, user, password, host, port, polling_interval_seconds=60):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.synapse_total_rooms = Gauge("synapse_total_rooms", "Total number of rooms in Synapse server")
        self.synapse_total_users = Gauge("synapse_total_users", "Total number of users in Synapse server")

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        print("Synapse Stats Exporter started.")
        try:
                postgreSQL_pool = pool.SimpleConnectionPool(1,3,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port)
                while True:
                    print(f"Synapse Stats Exporter will fetch statistics. Next polling in {self.polling_interval_seconds} seconds.")
                    self.fetch(postgreSQL_pool)
                    time.sleep(self.polling_interval_seconds)
        except Exception as e:
                print(f"Error fetching data: {e}")
        finally:
            if postgreSQL_pool:
                    postgreSQL_pool.closeall
                    print("PostgreSQL connection pool is closed")

    def fetch(self, postgreSQL_pool):
        """
        Get metrics from Synapse and refresh Prometheus metrics with
        new values.
        """
        try:
            conn = postgreSQL_pool.getconn()

            if conn is None:
                print("Failed to get connection. Skipping.")
                return

            cur = conn.cursor()

            # Count total rooms
            cur.execute("SELECT COUNT(*) FROM rooms")
            total_rooms = cur.fetchone()[0]

            # Count total users
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]

            # Set Prometheus metrics
            self.synapse_total_rooms.set(total_rooms)
            self.synapse_total_users.set(total_users)

            cur.close()
            postgreSQL_pool.putconn(conn)
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")


def getenv_int(name, default):
    value = os.getenv(name)
    return int(value) if value and value.strip() else default


def main():
    polling_interval_seconds = getenv_int("POLLING_INTERVAL_SECONDS", 60)
    user = os.getenv("PROM_SYNAPSE_USER") or "user"
    password = os.getenv("PROM_SYNAPSE_PASSWORD") or "password"
    host = os.getenv("PROM_SYNAPSE_HOST") or "host"
    port = getenv_int("PROM_SYNAPSE_PORT", 5432)
    database = os.getenv("PROM_SYNAPSE_DATABASE") or "synapse"
    exporter_port = getenv_int("EXPORTER_PORT", 9877)

    synapse_stats_metrics = SynapseStatsMetrics(
        dbname=database,
        user=user,
        password=password,
        host=host,
        port=port,
        polling_interval_seconds=polling_interval_seconds,
    )

    start_http_server(exporter_port)
    synapse_stats_metrics.run_metrics_loop()


if __name__ == "__main__":
    main()
