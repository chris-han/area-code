# Docker + WSL2 + Hiddify: Proxy Configuration Notes

## Problem

Running Docker inside WSL2 while routing traffic through a Hiddify proxy on the _Windows_ host produced repeated failures such as:

- `curl: (7) Failed to connect to 192.168.110.121 port 12334: Connection refused`
- `docker pull … proxyconnect tcp: dial tcp 192.168.110.121:12334: connect: connection refused`

Root cause:

- WSL2 was in **mirrored networking** mode, so the Linux VM and Windows shared the same LAN IP (e.g. `192.168.110.121`).
- Docker was configured to use the proxy at `http://192.168.110.121:12334`. Inside WSL this loops back into the Linux VM (no listener), so Windows never received the connection.
- Other tools (e.g. Git) succeeded because they were either using SSH or relying on WSL’s loopback forwarding to reach `127.0.0.1`, which _does_ forward into Windows.

## Solution

1. **Drive Docker through Windows loopback (127.0.0.1).**
   - WSL2 forwards `127.0.0.1` to the Windows host’s loopback automatically.
   - The proxy generator script in `/usr/local/sbin/gen-docker-proxy.sh` now defaults to:
     ```bash
     HTTP_PROXY=http://127.0.0.1:12334
     HTTPS_PROXY=http://127.0.0.1:12334
     NO_PROXY=localhost,127.0.0.1,::1
     ```
     (Override with `HIDDIFY_HOST_IP=auto` if NAT mode or a fixed host IP is required.)
2. **Systemd drop-in for Docker** (`/etc/systemd/system/docker.service.d/proxy.conf`):
   ```ini
   [Service]
   ExecStartPre=/usr/local/sbin/gen-docker-proxy.sh
   EnvironmentFile=-/run/docker-proxy.env
   ```
   This regenerates `/etc/docker/daemon.json` and Docker’s proxy env vars before each start.
3. **Restart Docker** after updating the script:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart docker
   ```

## Verification

```bash
cat /etc/docker/daemon.json
sudo docker info | grep -i Proxy
curl -v --proxy http://127.0.0.1:12334 https://registry-1.docker.io/v2/
sudo docker run --rm curlimages/curl -I https://registry-1.docker.io/v2/
```

If pulls still fail with transient `EOF` errors, retry or test another image—the proxy path is confirmed when the plain `curl` succeeds through Hiddify.

## Optional cleanup / switches

- Remove old port proxy rules (run in elevated PowerShell):
  ```powershell
  netsh interface portproxy delete v4tov4 listenaddress=192.168.110.121 listenport=12334
  netsh interface portproxy delete v4tov4 listenaddress=172.22.224.1 listenport=12334
  netsh advfirewall firewall delete rule name="Hiddify LAN 12334"
  ```
- To revert to automatic host detection (e.g. after switching WSL2 to **NAT** mode), restart Docker with:
  ```bash
  sudo HIDDIFY_HOST_IP=auto systemctl restart docker
  ```

With these changes Docker, Git, and other HTTPS clients inside WSL2 transparently use the Hiddify proxy running on the Windows host.
