import streamlit as st
from snowflake.snowpark.session import Session
from snowflake.core import Root
from snowflake.cortex import Complete
import pandas as pd
from dotenv import load_dotenv
import os
from typing import List
from snowflake.snowpark.functions import udf  # Import udf from Snowpark

# Load environment variables from a .env file
load_dotenv()

# Set Snowflake connection parameters
connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_USER_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE")
}

# Create the Snowpark session (only once, stored in session state)
if "snowpark_session" not in st.session_state:
    snowpark_session = Session.builder.configs(connection_params).create()
    st.session_state.snowpark_session = snowpark_session
else:
    snowpark_session = st.session_state.snowpark_session

# Default Values
NUM_CHUNKS = 3  # Number of chunks to retrieve for context
SLIDE_WINDOW = 7  # Number of previous messages to consider for context

# Service Parameters
CORTEX_SEARCH_DATABASE = "LEGAL_DATA_DB"
CORTEX_SEARCH_SCHEMA = "LEGAL_DATA_SCHEMA"
CORTEX_SEARCH_SERVICE = "LEGAL_JUDGEMENTS_CORTEX_SEARCH_SERVICE"

# Use the session stored in the session state
session = snowpark_session

# Cortex Search Retriever Class
class CortexSearchRetriever:
    def __init__(self, session, limit_to_retrieve: int = 4):
        self._session = session
        self._limit_to_retrieve = limit_to_retrieve

    def retrieve(self, query: str) -> List[str]:
        root = Root(self._session)
        cortex_search_service = (
            root
            .databases[CORTEX_SEARCH_DATABASE]
            .schemas[CORTEX_SEARCH_SCHEMA]
            .cortex_search_services[CORTEX_SEARCH_SERVICE]
        )
        response = cortex_search_service.search(
            query=query,
            columns=["extracted_text"],
            limit=self._limit_to_retrieve,
        )

        if response.results:
            return [result["extracted_text"] for result in response.results]
        else:
            return []

# Legal RAG System
class LLegalRAG:
    def __init__(self):
        self.retriever = CortexSearchRetriever(
            session=session,
            limit_to_retrieve=5  # Increased to get more relevant cases
        )

    def retrieve_context(self, query: str) -> List[str]:
        """
        Retrieve relevant cases from vector store.
        Returns list of cases with their details.
        """
        return self.retriever.retrieve(query)

    def generate_legal_analysis(self, query: str, context: List[str]) -> str:
        """
        Generate comprehensive legal analysis based on retrieved cases.
        """
        prompt = f"""
        You are an expert Indian legal assistant analyzing Supreme Court cases.
        Analyze the following legal scenario and relevant case laws to provide advice.

        Scenario Question:
        {query}

        Context: {context[0]}

        Please provide:
        1. A brief analysis of how the top 3 cases relate to the scenario
        2. Key legal principles established in these cases (keep it short)
        3. Potential application to the current scenario
        4. Recommended course of action based on these precedents

        Format your response in a clear, structured manner with case citations.
        If certain aspects are not covered by these cases, clearly state so.
        """
        return Complete("mistral-large", prompt)

    def query(self, query: str) -> str:
        """
        Main method to process legal queries and generate analysis.
        """
        # 1. Retrieve relevant cases
        raw_cases = self.retrieve_context(query)
        return self.generate_legal_analysis(query, raw_cases)

# Register UDF for session
def udf_function(query: str) -> str:
    return legal_rag.query(query)

session.udf.register(udf_function, return_type="STRING", input_types=["STRING"])

# Initialize the Legal RAG system
legal_rag = LLegalRAG()

# Streamlit App

def init_messages():
    """Initialize chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

def get_chat_history():
    """Get the chat history within the slide window."""
    start_index = max(0, len(st.session_state.messages) - SLIDE_WINDOW)
    return st.session_state.messages[start_index:]

def config_options():
    """Set up sidebar options."""
    st.sidebar.selectbox(
        'Select your model:',
        ('mistral-7b', 'mistral-large', 'mixtral-8x7b'),
        key="model_name"
    )
    
    st.sidebar.checkbox('Remember chat history?', key="use_chat_history", value=True)
    st.sidebar.button("Start Over", on_click=init_messages)

def main():
    """Streamlit main function."""
    st.title("⚖️ Indian Legal Assistant")
    st.write("Ask questions about Indian Supreme Court cases and legal precedents.")
    init_messages()
    config_options()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if question := st.chat_input("Ask your legal question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Display the user's question before generating the response
        with st.chat_message("user"):
            st.markdown(f"**You asked:** {question}")
        
        # Show loading indicator while the response is being processed
        with st.chat_message("assistant"):
            with st.spinner("Generating legal analysis..."):
                chat_history = get_chat_history()
                response = legal_rag.query(question)
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
