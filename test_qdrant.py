from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import os

load_dotenv()

qdrant_client = QdrantClient(
    url=os.getenv("qdrant_client_url"), 
    api_key=os.getenv("qdrant_client_api_key"),
)

print(qdrant_client.get_collections())

collection_name = "knowledge_base"
model_name = "BAAI/bge-small-en-v1.5"

# qdrant_client.create_collection(
#     collection_name=collection_name,
#     vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
# )


# # Uploading data to the collection
# documents = [
#     models.Document(
#         id="1",
#         text="This is a sample document.",
#         metadata={"source": "test"}
#     ),
#     models.Document(
#         id="2",
#         text="This is another sample document.",
#         metadata={"source": "test"}
#     )
# ]

#

