import chromadb
import pandas as pd
from app.utils.logger import logger

def initialize_chromadb():
    try:
        # Initialize ChromaDB client
        chroma_client = chromadb.Client()
        collection_name = "DatasetEx"

        # Check if collection exists, if not create it
        try:
            collection = chroma_client.get_collection(name=collection_name)
            print(f"Collection {collection_name} already exists")
        except Exception:
            print(f"Creating new collection: {collection_name}")
            collection = chroma_client.create_collection(name=collection_name)
            
            # Load your CSV data
            file = "app/data/dataset.csv"
            try:
                df = pd.read_csv(file)
                
                # Add an ID column if it doesn't exist
                df["ID"] = ["doc_" + str(i) for i in range(len(df))]

                # Prepare documents using f-strings
                documents = df.apply(
                    lambda row: (
                        f"Document Name: {row['Document Name']} | "
                        f"Effective Date: {row['Effective Date']} | "
                        f"Category: {row['Category']} | "
                        f"Parties Involved: {row['Parties']} | "
                        f"Agreement Date: {row['Agreement Date']} | "
                        f"Expiration Date: {row['Expiration Date']} | "
                        f"Renewal Term: {row['Renewal Term']} | "
                        f"Governing Law: {row['Governing Law']} | "
                        f"Exclusivity: {row['Exclusivity']} | "
                        f"Contract Details: {row['contract']}"
                    ),
                    axis=1
                ).tolist()

                # Extract metadata
                metadata = df[["Document Name", "Effective Date", "Category"]].to_dict(orient="records")
                ids = df["ID"].tolist()

                # Add data to the ChromaDB collection
                collection.add(documents=documents, metadatas=metadata, ids=ids)
                print(f"Added {len(documents)} records to the ChromaDB collection")
            except Exception as e:
                print(f"Error loading CSV data: {str(e)}")
                # Create a dummy document if CSV loading fails
                collection.add(
                    documents=["Sample contract document"],
                    metadatas=[{"source": "dummy"}],
                    ids=["dummy_1"]
                )
                
        return chroma_client
    except Exception as e:
        print(f"Error initializing ChromaDB: {str(e)}")
        return None

# Initialize ChromaDB at startup
chroma_client = initialize_chromadb()