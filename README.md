farang-control is the control plane of the farang proxy network.

It is responsible for managing and coordinating distributed proxy instances ([farang-edge](https://github.com/infanasotku/farang-edge)) across the network.

Core responsibilities:
- edge node registration
- configuration distribution
- health monitoring

farang-control does not proxy traffic itself. Instead, it orchestrates the behavior of farang-edge instances.
