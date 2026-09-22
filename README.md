farang-control is the control plane of the farang proxy network.

It is responsible for managing and coordinating distributed proxy instances ([farang-edge](https://github.com/infanasotku/farang-edge)) across the network.

Core responsibilities:

- edge node registration
- configuration distribution
- health monitoring

farang-control does not proxy traffic itself. Instead, it orchestrates the behavior of farang-edge instances.

## Status reads and infrastructure

PostgreSQL is the authoritative store for engines, desired specs, and runtime state.
The admin list and detail pages read these tables directly with outer joins, so
engines without a spec or runtime report remain visible. Sync status and liveness
are derived when read; listing uses stable name/ID ordering and a total engine count.
