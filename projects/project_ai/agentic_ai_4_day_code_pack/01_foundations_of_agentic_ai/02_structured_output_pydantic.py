"""
Structured output:
Useful when model output must feed a database, dashboard, or risk system.
"""

from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class MacroSignal(BaseModel):
    asset: str
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float = Field(ge=0, le=1)
    reason: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(MacroSignal)

result = structured_llm.invoke(
    "USDJPY rallied after US yields moved higher. Extract the market signal."
)

print(result)
print(result.model_dump())

##################################################
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class TradeSignal(BaseModel):
    asset: str
    strategy: str
    direction: Literal["long", "short", "neutral"]
    confidence: float = Field(ge=0, le=1)
    rationale: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured = llm.with_structured_output(TradeSignal)

result = structured.invoke("EURUSD implied vol is cheap versus realized before ECB. Extract a trade signal.")
print(result)
print(result.model_dump())


""" 
>>> print(result)
asset='EURUSD' strategy='Buy EURUSD options to capitalize on the potential increase in implied volatility post-ECB meeting.' direction='long' 
confidence=0.75 rationale="Implied volatility is currently low compared to realized volatility, 
suggesting that the market may be underestimating the potential for significant price movement following the ECB's decisions.
 Buying options can provide a leveraged way to benefit from this expected increase in volatility."


>>> print(result.model_dump())

{'asset': 'EURUSD', 
'strategy': 'Buy EURUSD options to capitalize on the potential increase in implied volatility post-ECB meeting.', 
'direction': 'long', 
'confidence': 0.75, 
'rationale': "Implied volatility is currently low compared to realized volatility, suggesting that the market may be underestimating the potential for 
            significant price movement following the ECB's decisions. Buying options can provide a leveraged way to benefit from this expected increase in volatility."}
 """