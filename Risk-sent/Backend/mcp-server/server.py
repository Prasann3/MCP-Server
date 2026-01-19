from mcp.server.fastmcp import FastMCP
from app.services.ai_service import rag_service  # Importing your RAG brain
import sys
import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


# Initialize the Specialist Server
mcp = FastMCP("RiskSensingSpecialist")

# Defineing the Specialist Tool
@mcp.tool()
async def semantic_search(query: str , doc_id : str) -> str:
    """
    Search for any specific context.
    """
    try:
        # Trigger the RAG Engine
        # Returns Parent paragraphs (rich context) for better AI reasoning
        logger.info("The tool is called in the MCP server")
        if not doc_id :
            return "**ERROR** : Cannot use this tool"
        retrieved_docs = await rag_service.search_risks(query , doc_id)
        
        if not retrieved_docs:
            return "No specific risks found for this query in the documents."

        # Formatting the "Observation" for the LLM
        formatted_results = []
        for doc in retrieved_docs:
            page_num = doc.get("page", "Unknown")
            content = doc.get("text", "Unknown").strip()
            formatted_results.append(f"--- [SOURCE: PAGE {page_num}] ---\n{content}")

        return "\n\n".join(formatted_results)

    except Exception as e:
        return f"Error during document retrieval: {str(e)}"

# Launch via STDIO Transport
if __name__ == "__main__":
    mcp.run(transport="stdio")