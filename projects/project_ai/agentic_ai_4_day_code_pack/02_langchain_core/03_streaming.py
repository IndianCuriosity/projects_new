"""
Streaming:
Useful for Streamlit, chat UIs, dashboards, and long agent responses.
"""

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


################################################################
# basic .stream() method on the LLM itself
################################################################

for chunk in llm.stream("Explain RAG in simple terms."):
    print(chunk.content, end="", flush=True)


################################################################
# Streaming through a Chain (LCEL)
# If you build a chain using the pipe (|) operator, you can stream the entire chain. LangChain will automatically propagate the stream from the LLM through the output parser.
################################################################

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Tell me a short story about {topic}")
chain = prompt | llm | StrOutputParser()

# Even with a prompt and parser, streaming still works seamlessly
for chunk in chain.stream({"topic": "a polite robot"}):
    print(chunk, end="", flush=True)

########################################################################################################################################
# Async Streaming (astream)
# In web frameworks like FastAPI or Streamlit, you usually want to stream asynchronously so you don't block other tasks.
########################################################################################################################################

import asyncio

async def main():
    # astream is the async version of stream
    async for chunk in llm.astream("Write a 3-step workout plan."):
        print(chunk.content, end="", flush=True)

# Run the async function
asyncio.run(main())

########################################################################################################################################
# Streaming with Tools/Structured Output
# This is a bit more advanced. If you are using your Route model from earlier, you can stream the tool calls as they are being built. 
# This is great for showing the user "The AI is thinking about which category to choose..."

# Why use flush=True?
    # In your original code, you used flush=True. That's a pro move!
    # Standard Python print() statements are "buffered," meaning they wait for a newline (\n) before actually showing text on the screen. 
    # flush=True forces the terminal to show each character the millisecond it arrives from the API.
                                                                                    
########################################################################################################################################

from pydantic import BaseModel, Field

class Weather(BaseModel):
    city: str = Field(description="The name of the city")

llm_with_tools = llm.bind_tools([Weather])

# This will stream the "chunks" of the tool call (the JSON building up)
for chunk in llm_with_tools.stream("What is the weather in Tokyo?"):
    if chunk.tool_call_chunks:
        # Note: Tool chunks are parts of a JSON string
        print(chunk.tool_call_chunks[0].get("args"), end="", flush=True)




""" Summary Table

Method             Best For
.stream()          Simple CLI scripts and basic tests.
.astream()         Production web apps (FastAPI, Django)
.chain.stream()    When you have complex logic (Prompts + Parsers)
.astream_events()  High-level debugging (shows exactly what's happening at every step). """
