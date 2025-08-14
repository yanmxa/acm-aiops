"""
Utility functions for validating MCP server configuration.
"""

import os
import subprocess
from typing import Dict, List, Tuple


def validate_docker_availability() -> Tuple[bool, str]:
    """
    Check if Docker is available and running.
    
    Returns:
        Tuple of (is_available, error_message)
    """
    try:
        result = subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            return True, "Docker is available"
        else:
            return False, f"Docker command failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Docker command timed out"
    except FileNotFoundError:
        return False, "Docker command not found. Please install Docker."
    except Exception as e:
        return False, f"Error checking Docker: {str(e)}"


def validate_prometheus_connectivity(prometheus_url: str) -> Tuple[bool, str]:
    """
    Check if Prometheus server is accessible.
    
    Args:
        prometheus_url: The Prometheus server URL
        
    Returns:
        Tuple of (is_accessible, error_message)
    """
    try:
        import requests
        response = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=5)
        if response.status_code == 200:
            return True, "Prometheus server is accessible"
        else:
            return False, f"Prometheus server returned status {response.status_code}"
    except ImportError:
        return False, "requests library not available for connectivity check"
    except requests.exceptions.ConnectTimeout:
        return False, f"Connection to {prometheus_url} timed out"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {prometheus_url}"
    except Exception as e:
        return False, f"Error connecting to Prometheus: {str(e)}"


def validate_environment_variables() -> Dict[str, str]:
    """
    Validate required environment variables for MCP servers.
    
    Returns:
        Dictionary of environment variable status
    """
    status = {}
    
    # Check Prometheus URL
    prometheus_url = os.getenv("PROMETHEUS_URL")
    if prometheus_url:
        status["PROMETHEUS_URL"] = f"Set to: {prometheus_url}"
    else:
        status["PROMETHEUS_URL"] = "Not set, will use default: https://localhost:30090"
    
    # Check Docker-related environment variables
    docker_host = os.getenv("DOCKER_HOST")
    if docker_host:
        status["DOCKER_HOST"] = f"Set to: {docker_host}"
    else:
        status["DOCKER_HOST"] = "Not set, will use default Docker socket"
    
    return status


def run_mcp_diagnostics() -> Dict[str, any]:
    """
    Run comprehensive diagnostics for MCP server setup.
    
    Returns:
        Dictionary containing diagnostic results
    """
    diagnostics = {}
    
    # Check Docker
    docker_available, docker_message = validate_docker_availability()
    diagnostics["docker"] = {
        "available": docker_available,
        "message": docker_message
    }
    
    # Check environment variables
    diagnostics["environment"] = validate_environment_variables()
    
    # Check Prometheus connectivity if URL is available
    prometheus_url = os.getenv("PROMETHEUS_URL", "https://localhost:30090")
    prometheus_accessible, prometheus_message = validate_prometheus_connectivity(prometheus_url)
    diagnostics["prometheus"] = {
        "accessible": prometheus_accessible,
        "message": prometheus_message,
        "url": prometheus_url
    }
    
    return diagnostics


def print_diagnostics_report():
    """Print a formatted diagnostics report."""
    print("=== MCP Server Diagnostics ===")
    
    diagnostics = run_mcp_diagnostics()
    
    # Docker status
    docker_status = "✓" if diagnostics["docker"]["available"] else "✗"
    print(f"{docker_status} Docker: {diagnostics['docker']['message']}")
    
    # Environment variables
    print("\n📋 Environment Variables:")
    for var, status in diagnostics["environment"].items():
        print(f"  • {var}: {status}")
    
    # Prometheus connectivity
    prometheus_status = "✓" if diagnostics["prometheus"]["accessible"] else "✗"
    print(f"\n{prometheus_status} Prometheus: {diagnostics['prometheus']['message']}")
    print(f"  URL: {diagnostics['prometheus']['url']}")
    
    # Overall status
    all_good = (
        diagnostics["docker"]["available"] and 
        diagnostics["prometheus"]["accessible"]
    )
    
    if all_good:
        print("\n🎉 All systems ready for MCP server initialization!")
    else:
        print("\n⚠️  Some issues detected. Please resolve them before running MCP servers.")
    
    return diagnostics


if __name__ == "__main__":
    print_diagnostics_report()