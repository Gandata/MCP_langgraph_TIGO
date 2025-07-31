from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arith")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Suma dos números."""
    return a + b

@mcp.tool()
def sub(a: float, b: float) -> float:
    """Resta b de a."""
    return a - b

@mcp.tool()
def mul(a: float, b: float) -> float:
    """Multiplica dos números."""
    return a * b

@mcp.tool()
def div(a: float, b: float) -> float:
    """Divide a entre b."""
    if b == 0:
        return "Error: división por cero"
    return a / b

if __name__ == "__main__":
    mcp.run(transport="stdio")