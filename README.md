# synapse_stats_exporter

A prometheus exporter to collect the statistics from Synapse server instance.

So far, collects only the number of rooms and the number of users.

The exporter can be configured by setting the following environment variables:

POLLING_INTERVAL_SECONDS - Defaults to 60 seconds
PROM_SYNAPSE_BASE_URL - Defaults to http://localhost:8008
PROM_SYNAPSE_ADMIN_TOKEN - Defaults to password
EXPORTER_PORT - Defaults to 9877
