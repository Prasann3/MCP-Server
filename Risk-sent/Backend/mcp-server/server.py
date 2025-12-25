from mcp.server.fastmcp import FastMCP
from app.services.ai_service import ai_service  # Importing your RAG brain
import sys
import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)



# Initialize the Specialist Server
mcp = FastMCP("RiskSensingSpecialist")

# Defineing the Specialist Tool
@mcp.tool()
def search_10k_risks(query: str) -> str:
    """
    Search through Microsoft 10-K filings to find specific risk factors.
    Use this for questions about financial, legal, or market risks.
    """
    try:
        # Trigger the RAG Engine
        # Returns Parent paragraphs (rich context) for better AI reasoning
        retrieved_docs = ai_service.search_risks(query)
        
        if not retrieved_docs:
            return "No specific risks found for this query in the documents."

        # Formatting the "Observation" for the LLM
        formatted_results = []
        for doc in retrieved_docs:
            page_num = doc.metadata.get("page", "Unknown")
            content = doc.page_content.strip()
            formatted_results.append(f"--- [SOURCE: PAGE {page_num}] ---\n{content}")

        return "\n\n".join(formatted_results)

    except Exception as e:
        return f"Error during document retrieval: {str(e)}"

# Launch via STDIO Transport
if __name__ == "__main__":
    mcp.run(transport="stdio")