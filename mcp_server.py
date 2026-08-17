"""
AEGIS-SWARM :: Live Telemetry MCP Server (Standalone Protocol Provider)
=======================================================================
This script implements a REAL Model Context Protocol (MCP) server.
It operates as an independent tool provider that communicates with the 
AEGIS-SWARM orchestrator via JSON-RPC over stdio.
"""

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server. This registers the provider.
mcp = FastMCP("aegis-telemetry")

@mcp.tool()
def get_live_telemetry(lat: float = 34.0522, lon: float = -118.2437) -> dict:
    """
    Fetch real-time environmental telemetry for drone coordinates.
    Provides reality-grounding context for the Critic Agent.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    try:
        # Using httpx for synchronous, reliable HTTP calls
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json().get("current_weather", {})

        temperature = data.get("temperature", "Unknown")
        wind_speed = data.get("windspeed", "Unknown")

        return {
            "source": "Open-Meteo Live API (via Official MCP Protocol)",
            "temperature": f"{temperature}°C",
            "wind_speed": f"{wind_speed} km/h",
            "mcp_status": "Success - Live telemetry integrated via stdio.",
        }

    except httpx.TimeoutException:
        return {"error": "Telemetry request timed out.", "mcp_status": "degraded"}
    except httpx.RequestError as e:
        return {"error": f"Network failure: {e}", "mcp_status": "degraded"}
    except Exception as e:
        return {"error": f"Malformed response: {e}", "mcp_status": "degraded"}

if __name__ == "__main__":
    # Runs the server using standard input/output transport, which is the 
    # native architecture for MCP communication.
    mcp.run(transport="stdio")
