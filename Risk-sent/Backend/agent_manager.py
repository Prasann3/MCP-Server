import logging
from app.utils.uploads import wrap_tool_with_context
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from contextlib import AsyncExitStack
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from app.core.config import settings 
from app.services.chat_services import update_chat , get_message_size
import json
import asyncio
from app.schemas.chat_schema import Message , ChatUpdate
from app.services.chat_services import add_message
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  
)

logger = logging.getLogger(__name__)

class RiskAgentManager:
    def __init__(self):
        # 1. Initialize the Brain (Groq LLM)
        # We use a high-reasoning model (Llama 3 70B) to make good decisions
        # No connection takes place here only the llm object is initialized
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant", 
            groq_api_key=settings.GROK_API_KEY
        )
        
        # 2. Define the MCP Connection
        # This tells the manager WHERE to find the "Specialist"
        self.mcp_client = MultiServerMCPClient({
            "risk_server": {
                "command": "python",
                "args": ["-m" , "mcp-server.server"], 
                "transport": "stdio",
            }
        })
        self.cached_tools = None
        self.stack = AsyncExitStack()
        self.base_tools = None


    async def initialize(self):
            """Starts the MCP child process and keeps it alive."""
            logger.info("Starting Persistent MCP Session...")
            
            # 1. Start the child process and enter the session
            # This is where the 'python -m mcp-server.server' command runs!
            self.session = await self.stack.enter_async_context(
                self.mcp_client.session("risk_server")
            )
            
            # 2. Pre-load tool definitions through the active pipe
            self.base_tools = await load_mcp_tools(self.session)
            logger.info("MCP Server is WARM and tools are cached.")

    async def shutdown(self):
            """Kills the child process. Call this when the app closes."""
            await self.stack.aclose()
            logger.info("MCP Child Process terminated.")

    async def get_agent(self , doc_id=None):
        # MCP tools
        logger.info("Collecting MCP Tools")
        mcp_tools = self.base_tools
        
        if doc_id :
         contextual_tools = [
         wrap_tool_with_context(t, doc_id) if t.name == "semantic_search" else t 
         for t in mcp_tools
         ] 

        else :

          contextual_tools = [
            t for t in mcp_tools if t.name != "semantic_search"
          ]  

    
        agent = create_react_agent(
            self.llm, 
            tools=contextual_tools
        )
        return agent


    async def run_query(self, user_input: str, chat , doc_id = None):
        """
        An async generator that yields status updates and 
        eventually the final answer, utilizing Long-term and Short-term memory.
        """ 
        try:
            chat_id = chat["_id"]
            
            # Step 1: Analysis
            yield json.dumps({"status": "Analyzing Query", "step": 1}) + "\n"
        
            # Step 2: Extract Context for the Prompt
            # Long-term: The stored summary
            long_term_summary = chat["summary"]
            
            # Short-term: Last 5 messages for immediate context
            recent_messages = chat["messages"]
            short_term_history = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])

            # Step 3: MCP Handshake
            yield json.dumps({"status": "Connecting to MCP", "step": 2}) + "\n"
            logger.info("Getting info about the tools")
            agent = await self.get_agent(doc_id)

            # Step 4: Context-Aware System Prompt
            # Merging your tool constraints with the Contextual Hierarchy logic
            strict_system_prompt = f"""
            ### ROLE
            You are a Financial Risk Analyst. You must provide professional, accurate answers using the provided tool.

            ### CONTEXTUAL HIERARCHY
            1. [LONG-TERM SUMMARY]: {long_term_summary}
            2. [SHORT-TERM HISTORY]: {short_term_history}

            ### OPERATIONAL LOGIC
            - **Relevance Check**: Determine if the current query relates to the memory above. If it does, use that context (e.g., resolve who 'they' or 'this company' refers to).
            - **Tool Usage**: You MUST use the tools provided to you for any data-heavy requests.
            - **Tone**: Do not leak internal details or mention that you were provided info by a tool. 
            -**Behaviour**: You must assisst the user in every way possible to get the best possible answer. Try to answer every question possible
            - **Scope**: Do not mention what internally you are doing to answer the query , just answer the query as best as you can."
            - Important: Call only the tools provided to you , if you cant answer the query using the tools provided to you , then say that you cant answer the query.

            ### FORMATTING
            You must format your tool call EXACTLY like this: 
            <function=tool_name>{{"parameters": "parameters"}}</function>

            """

            yield json.dumps({"status": "Searching 10-K", "step": 3}) + "\n"

            inputs = {
                "messages": [
                    ("system", strict_system_prompt),
                    ("user", user_input)
                ]
            }

            # Step 5: LLM Generation
            yield json.dumps({"status": "Thinking", "step": 4}) + "\n"
            logger.info("Calling the LLM for decision making")
            
            # Invoke the agent (LangGraph/LangChain)
            result = await agent.ainvoke(inputs)
            final_answer = result["messages"][-1].content
            
            for messages in result["messages"] :
                print(messages)

            # Step 6: Save Assistant Response
            llm_message = Message(
                role="assistant",
                content=final_answer,
            )
            await add_message(chat_id, llm_message)

            title = None
            if not chat["title"] :
              title = await self.get_title(user_input , final_answer) 
              
            #Check if messages multiple of 5 for resummerization
            count = await get_message_size(chat_id)
            summary = None
            print(title , summary)
            if count % 10 == 0 :
                current_summary = chat["summary"]
                if not current_summary : current_summary = ""
                summary = await self.summarize_messages(current_summary , chat["messages"])
            
            if title or summary :
                payload = ChatUpdate(
                title=title ,
                summary = summary
                )
                await update_chat(chat_id , payload)
               
            # Step 7: Yield Final Result
            yield json.dumps({"answer": final_answer}) + '\n'
            yield json.dumps({"status": "Complete", "step": 5}) + "\n"

            # # Step 8: Trigger Background Summarization
            # # We don't await this so the user gets their answer immediately
            # asyncio.create_task(self.background_summarize(chat_id))

        except Exception as e:
            logging.error(f"Error occurred while processing the request: {str(e)}")
            yield json.dumps({"status": "Error", "step": 5, "error": str(e)}) + "\n"
            

    async def summarize_messages(self , summary : str, messages : list[Message]) -> str : 
          
          """
          Update summary using previous summary + recent messages.
          """
          summary = summary.strip()
          llm_messages = []

          llm_messages.append(SystemMessage(content="""
            ### ROLE
            You are an expert Conversational Summarizer. Your task is to maintain a "Running Memory" of a discussion by merging new information into an existing context.

            ### OBJECTIVE
            Update the CURRENT SUMMARY by integrating critical insights from the NEW MESSAGES. Your goal is to produce a single, cohesive, and information-dense paragraph that preserves the "Long-term Memory" of the conversation.

            ### GUIDELINES
            - Information Density: Prioritize facts, entities (names, dates, technical terms), and specific decisions. Use semi-colons to pack multiple related insights into single, punchy sentences.
            - Eliminate Meta-Talk: Do not use phrases like "The user asked," "The AI responded," or "This conversation is about."
            - Recursive Integration: Ensure new information is woven into the existing summary logically; reflect the most current state.
            - Brevity: Keep the total output under 200 words unless strictly required.
            - No Hallucinations: Only summarize information explicitly present.

            ### OUTPUT FORMAT
            Provide ONLY the updated summary paragraph.
            """.strip()))

          llm_messages.append(SystemMessage(
            content=f"Here is the current summary of the chat (ignore this prompt if the summary if empty as it will be in case of new chat being generated) : \n {summary}"
          ))

          llm_messages.append(SystemMessage(
           content="The following messages are the previous conversation history between the user and the assistant."
            ))

          for msg in messages : 
            if msg["role"] == "user" : 
                llm_messages.append(HumanMessage(content=msg["content"]))
            else : llm_messages.append(AIMessage(content=msg["content"]))    

          llm_messages.append(HumanMessage(
            content="Summarize the conversation so far."
             ))  

          response = await self.llm.ainvoke(llm_messages) 
          return response.content  

    async def get_title(self , user_input : str , llm_response : str) -> str :

        llm_messages = []

        llm_messages.append(
            SystemMessage(
                content="""
                ### ROLE
                You are a precise Conversation Titler. Your task is to generate a professional, descriptive title for a chat session based on a provided exchange.

                ### INPUT DATA
                You will be provided with:
                1. USER_INPUT: The opening question or statement from the user.
                2. ASSISTANT_RESPONSE: The first response provided by the AI.

                ### OBJECTIVE
                Create a title that accurately reflects the specific topic of the interaction.

                ### CONSTRAINTS
                - WORD COUNT: The title must be exactly 3 to 4 words long.
                - OUTPUT FORMAT: Output ONLY the title text. Do not use quotation marks, bolding, or ending punctuation.
                - CASE: Use Title Case (capitalize the first letter of each major word).
                - NO META-TALK: Do not include phrases like "The title is:" or "Conversation about...".

                ### EXAMPLES
                - Input: "What are the liquidity risks?" / Response: "Based on the 10-K, the risks are..." 
                -> Title: Analysis of Liquidity Risks
                - Input: "Help me with my budget" / Response: "Sure, let's look at your expenses." 
                -> Title: Personal Budget Planning Guide
                - Input: "Compare Tesla and Ford debt" / Response: "Tesla has lower debt-to-equity..." 
                -> Title: Tesla Ford Debt Comparison
                """
            )
        )

        llm_messages.append(SystemMessage(
             content=f"Here is the user query : \n {user_input} \n Here is the first llm response to that query : \n {llm_response}"
        ))

        llm_messages.append(HumanMessage(
            content="Generate the title for the given inputs"
        ))

        response = await self.llm.ainvoke(llm_messages)
        return response.content      


agent_manager = RiskAgentManager()                