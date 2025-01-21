import streamlit as st
from snowflake.snowpark.session import Session
from snowflake.core import Root
from snowflake.cortex import Complete
import pandas as pd
from dotenv import load_dotenv
import os
from typing import List

import tomllib
# Load environment variables from a .env file

def load_config(file_path: str):
    with open(file_path, "rb") as config_file:  # Use "r" for toml library
        return tomllib.load(config_file)


load_dotenv()
config = load_config(".streamlit/secrets.toml")

def get_snowpark_session():
    """Create or retrieve Snowpark session from streamlit session state"""
    if "snowpark_session" not in st.session_state:
        try:
            Session.close_all()
        except:
            pass
        connection_params = {
    "account": config["snowflake"]["account"],
    "user": config["snowflake"]["user"],
    "password": config["snowflake"]["password"],
    "role": config["snowflake"]["role"],
    "database": config["snowflake"]["database"],
    "schema": config["snowflake"]["schema"],
    "warehouse": config["snowflake"]["warehouse"]
}
        st.session_state.snowpark_session = Session.builder.configs(connection_params).create()
    return st.session_state.snowpark_session

# Service Parameters
CORTEX_SEARCH_DATABASE = "LEGAL_DATA_DB"
CORTEX_SEARCH_SCHEMA = "LEGAL_DATA_SCHEMA"
CORTEX_SEARCH_SERVICE = "LEGAL_JUDGEMENTS_CORTEX_SEARCH_SERVICE"

# Cortex Search Retriever Class
class CortexSearchRetriever:
    def __init__(self, limit_to_retrieve: int = 4):
        
        self._limit_to_retrieve = limit_to_retrieve

    def retrieve(self, query: str) -> List[str]:
        self._session = get_snowpark_session()
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
            limit_to_retrieve=5
        )

    def retrieve_context(self, query: str) -> List[str]:
        return self.retriever.retrieve(query)

    def generate_legal_analysis(self, query: str, context: List[str]) -> str:
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
        raw_cases = self.retrieve_context(query)
        return self.generate_legal_analysis(query, raw_cases)

@st.cache_resource
def get_legal_rag():
    """Create or retrieve LegalRAG instance"""
    return LLegalRAG()

def init_messages():
    """Initialize chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

def get_chat_history():
    """Get the chat history within the slide window."""
    start_index = max(0, len(st.session_state.messages) - 7)
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
    try:
        st.title("⚖️ Indian Legal Assistant")
        st.write("Ask questions about Indian Supreme Court cases and legal precedents.")
        
        init_messages()
        config_options()
        
        legal_rag = get_legal_rag()

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if question := st.chat_input("Ask your legal question..."):
            st.session_state.messages.append({"role": "user", "content": question})
            
            with st.chat_message("user"):
                st.markdown(f"**You asked:** {question}")
            
            with st.chat_message("assistant"):
                with st.spinner("Generating legal analysis..."):
                    chat_history = get_chat_history()
                    response = legal_rag.query(question)
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    finally:
        # Cleanup on exit
        if "snowpark_session" in st.session_state:
            try:
                st.session_state.snowpark_session.close()
            except:
                pass

if __name__ == "__main__":
    main()