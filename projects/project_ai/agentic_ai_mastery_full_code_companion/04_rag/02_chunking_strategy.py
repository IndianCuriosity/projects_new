from langchain_text_splitters import RecursiveCharacterTextSplitter

text = """
Long gamma benefits when realized volatility exceeds implied volatility plus transaction costs.
However, theta decay can dominate if the spot market remains quiet.
Before central bank events, implied volatility often rises.
After the event, volatility can collapse quickly.
"""

splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=30)
chunks = splitter.split_text(text)

for i, chunk in enumerate(chunks, 1):
    print(f"--- chunk {i} ---")
    print(chunk)
