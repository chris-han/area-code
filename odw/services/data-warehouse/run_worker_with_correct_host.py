#!/usr/bin/env python3
"""
Run Temporal worker with correct host configuration
"""
import os
import asyncio
import subprocess
import json

def get_temporal_host():
    """Get the correct Temporal host using container name or IP"""
    try:
        # Check if we're running in Docker environment by checking if the Temporal container exists
        result = subprocess.run([
            'docker', 'inspect', 'data-warehouse-temporal-1'
        ], capture_output=True, text=True, check=True)

        # First try container name (works if worker is also in Docker network)
        import socket
        try:
            socket.gethostbyname("data-warehouse-temporal-1")
            return "data-warehouse-temporal-1:7233"
        except socket.gaierror:
            # Container name not resolvable, get container IP
            import json
            data = json.loads(result.stdout)
            if data and len(data) > 0:
                networks = data[0].get('NetworkSettings', {}).get('Networks', {})
                for network_name, network_info in networks.items():
                    ip_address = network_info.get('IPAddress')
                    if ip_address:
                        print(f"Using container IP: {ip_address}")
                        return f"{ip_address}:7233"

            # Fallback to localhost
            return "localhost:7233"

    except Exception as e:
        print(f"Docker container not found, using localhost: {e}")
        return "localhost:7233"

async def main():
    temporal_host = get_temporal_host()
    print(f"🔗 Connecting to Temporal at: {temporal_host}")

    # Set environment variable
    os.environ['TEMPORAL_HOST'] = temporal_host

    # Import and run worker
    from app.azure_billing.workflows.temporal_worker import run_worker

    config = {
        'temporal_host': temporal_host,
        'task_queue': 'abi-workflows'
    }

    await run_worker(config)

if __name__ == "__main__":
    asyncio.run(main())