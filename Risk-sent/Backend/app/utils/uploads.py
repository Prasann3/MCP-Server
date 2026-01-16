from fastapi import UploadFile
import pdfplumber
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

def extract_text_from_pdf(file_path: str) -> str:
    text = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)

    return "\n".join(text)

class SearchSchema(BaseModel):
    query: str = Field(description="The search terms for the 10-K")

def wrap_tool_with_context(tool, doc_id: str):
    """Wraps an MCP tool to inject doc_id automatically."""
    async def wrapped_func(*args, **kwargs):
        # Inject the doc_id into the arguments before calling the real tool
        kwargs["doc_id"] = doc_id
        return await tool.ainvoke(kwargs)

    return StructuredTool.from_function(
        func=None, # We use coroutine for async
        coroutine=wrapped_func,
        name=tool.name,
        description=tool.description,
        args_schema=SearchSchema # Keeps the original schema (minus doc_id if you prefer)
    )