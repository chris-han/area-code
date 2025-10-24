#!/usr/bin/env python3
"""
Service Discovery and Integration Script

This script provides service discovery capabilities for the bia system,
automatically detecting and configuring connections to all infrastructure services.
"""

import asyncio
import aiohttp
import socket
import json
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    name: str
    host: str
    port: int
    protocol: str = "http"
    health_path: str = "/"
    description: str = ""
    management_ui: Optional[str] = None


class ServiceDiscovery:
    """Service discovery and health monitoring"""
    
    def __init__(self):
        self.services = {
            "moose_api": ServiceEndpoint(
                name="Moose API",
                host="localhost",
                port=4200,
                health_path="/health",
                description="Main bia API server"
            ),
            "clickhouse_http": ServiceEndpoint(
                name="ClickHouse HTTP",
                host="localhost", 
                port=18123,
                health_path="/ping",
                description="ClickHouse analytics database"
            ),
            "clickhouse_native": ServiceEndpoint(
                name="ClickHouse Native",
                host="localhost",
                port=9000,
                protocol="tcp",
                description="ClickHouse native protocol"
            ),
            "temporal_server": ServiceEndpoint(
                name="Temporal Server",
                host="localhost",
                port=7233,
                protocol="grpc",
                description="Workflow orchestration server"
            ),
            "temporal_ui": ServiceEndpoint(
                name="Temporal UI",
                host="localhost",
                port=8080,
                management_ui="http://localhost:8080",
                description="Temporal workflow monitoring"
            ),
            "kafdrop": ServiceEndpoint(
                name="Kafdrop UI",
                host="localhost",
                port=9999,
                management_ui="http://localhost:9999",
                description="RedPanda message queue UI"
            ),
            "minio_api": ServiceEndpoint(
                name="MinIO API",
                host="localhost",
                port=9500,
                health_path="/minio/health/live",
                description="S3-compatible object storage"
            ),
            "minio_console": ServiceEndpoint(
                name="MinIO Console",
                host="localhost",
                port=9501,
                management_ui="http://localhost:9501",
                description="MinIO management interface"
            ),
            "redis": ServiceEndpoint(
                name="Redis",
                host="localhost",
                port=6379,
                protocol="tcp",
                description="In-memory cache and session store"
            ),
            "postgresql": ServiceEndpoint(
                name="PostgreSQL",
                host="localhost",
                port=5432,
                protocol="tcp",
                description="Temporal metadata database"
            ),
            "redpanda": ServiceEndpoint(
                name="RedPanda",
                host="localhost",
                port=19092,
                protocol="tcp",
                description="Kafka-compatible message streaming"
            )
        }
    
    async def check_tcp_port(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """Check if TCP port is open"""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (OSError, asyncio.TimeoutError):
            return False
    
    async def check_http_health(self, endpoint: ServiceEndpoint, timeout: float = 5.0) -> Tuple[bool, Optional[str]]:
        """Check HTTP service health"""
        if endpoint.protocol != "http":
            return False, "Not an HTTP service"
        
        url = f"http://{endpoint.host}:{endpoint.port}{endpoint.health_path}"
        
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(url) as response:
                    if response.status < 400:
                        return True, f"HTTP {response.status}"
                    else:
                        return False, f"HTTP {response.status}"
        except aiohttp.ClientError as e:
            return False, f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            return False, "Timeout"
    
    async def discover_service(self, service_id: str, endpoint: ServiceEndpoint) -> Dict:
        """Discover and check a single service"""
        result = {
            "id": service_id,
            "name": endpoint.name,
            "host": endpoint.host,
            "port": endpoint.port,
            "protocol": endpoint.protocol,
            "description": endpoint.description,
            "management_ui": endpoint.management_ui,
            "status": "unknown",
            "health": "unknown",
            "response_time": None
        }
        
        # Check if port is open
        import time
        start_time = time.time()
        
        port_open = await self.check_tcp_port(endpoint.host, endpoint.port)
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        result["response_time"] = round(response_time, 2)
        
        if not port_open:
            result["status"] = "down"
            result["health"] = "Port not accessible"
            return result
        
        result["status"] = "up"
        
        # Check HTTP health if applicable
        if endpoint.protocol == "http":
            health_ok, health_msg = await self.check_http_health(endpoint)
            result["health"] = "healthy" if health_ok else f"unhealthy: {health_msg}"
        else:
            result["health"] = "port_open"
        
        return result
    
    async def discover_all_services(self) -> Dict[str, Dict]:
        """Discover all configured services"""
        print("🔍 Discovering bia services...")
        
        tasks = []
        for service_id, endpoint in self.services.items():
            task = self.discover_service(service_id, endpoint)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        return {result["id"]: result for result in results}
    
    def generate_service_config(self, discovery_results: Dict[str, Dict]) -> Dict:
        """Generate service configuration based on discovery results"""
        config = {
            "services": {},
            "management_interfaces": {},
            "api_endpoints": {},
            "direct_connections": {}
        }
        
        for service_id, result in discovery_results.items():
            if result["status"] == "up":
                service_config = {
                    "host": result["host"],
                    "port": result["port"],
                    "protocol": result["protocol"],
                    "health": result["health"],
                    "response_time_ms": result["response_time"]
                }
                
                config["services"][service_id] = service_config
                
                # Categorize services
                if result["management_ui"]:
                    config["management_interfaces"][service_id] = {
                        "name": result["name"],
                        "url": result["management_ui"],
                        "description": result["description"]
                    }
                
                if result["protocol"] == "http":
                    config["api_endpoints"][service_id] = {
                        "name": result["name"],
                        "url": f"http://{result['host']}:{result['port']}",
                        "description": result["description"]
                    }
                
                if result["protocol"] in ["tcp", "grpc"]:
                    config["direct_connections"][service_id] = {
                        "name": result["name"],
                        "endpoint": f"{result['host']}:{result['port']}",
                        "protocol": result["protocol"],
                        "description": result["description"]
                    }
        
        return config
    
    def print_discovery_results(self, discovery_results: Dict[str, Dict]):
        """Print formatted discovery results"""
        print("\n" + "="*80)
        print("🏗️  bia SERVICE DISCOVERY RESULTS")
        print("="*80)
        
        # Group by status
        up_services = []
        down_services = []
        
        for result in discovery_results.values():
            if result["status"] == "up":
                up_services.append(result)
            else:
                down_services.append(result)
        
        # Print healthy services
        if up_services:
            print(f"\n✅ HEALTHY SERVICES ({len(up_services)})")
            print("-" * 40)
            for service in sorted(up_services, key=lambda x: x["name"]):
                status_icon = "🟢" if service["health"] == "healthy" or service["health"] == "port_open" else "🟡"
                print(f"{status_icon} {service['name']:<20} {service['host']}:{service['port']:<6} ({service['response_time']}ms)")
                if service["management_ui"]:
                    print(f"   📊 Management: {service['management_ui']}")
        
        # Print down services
        if down_services:
            print(f"\n❌ DOWN SERVICES ({len(down_services)})")
            print("-" * 40)
            for service in sorted(down_services, key=lambda x: x["name"]):
                print(f"🔴 {service['name']:<20} {service['host']}:{service['port']:<6} - {service['health']}")
        
        # Print summary
        total_services = len(discovery_results)
        healthy_services = len(up_services)
        
        print(f"\n📊 SUMMARY")
        print("-" * 40)
        print(f"Total Services: {total_services}")
        print(f"Healthy: {healthy_services}")
        print(f"Down: {total_services - healthy_services}")
        print(f"Health Rate: {(healthy_services/total_services)*100:.1f}%")
        
        if healthy_services == total_services:
            print("\n🎉 All services are healthy! bia system is ready.")
        elif healthy_services > 0:
            print(f"\n⚠️  {total_services - healthy_services} service(s) need attention.")
        else:
            print("\n🚨 No services are running. Start services with: bun run bia:dev")


async def main():
    """Main service discovery function"""
    discovery = ServiceDiscovery()
    
    try:
        # Discover all services
        results = await discovery.discover_all_services()
        
        # Print results
        discovery.print_discovery_results(results)
        
        # Generate and save configuration
        config = discovery.generate_service_config(results)
        
        # Save configuration to file
        config_path = Path(".moose/service-config.json")
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Service configuration saved to: {config_path}")
        
        # Return appropriate exit code
        healthy_count = len([r for r in results.values() if r["status"] == "up"])
        total_count = len(results)
        
        if healthy_count == total_count:
            return 0  # All services healthy
        elif healthy_count > 0:
            return 1  # Some services down
        else:
            return 2  # All services down
            
    except Exception as e:
        print(f"\n❌ Service discovery failed: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))