import streamlit as st
from snowflake.snowpark.session import Session
from snowflake.core import Root
from snowflake.cortex import Complete
import pandas as pd
import os
from typing import List
import tomllib


# Load Snowflake connection configuration
def load_config(file_path: str):
    with open(file_path, "rb") as config_file:
        return tomllib.load(config_file)

# Initialize Snowpark session and root
@st.cache_resource()
def get_snowpark_session():
    """Create and retrieve a single instance of Snowpark session."""
    connection_params = {
        "account": st.secrets.snowflake.account,
        "user": st.secrets.snowflake.user,
        "password": st.secrets.snowflake.password,
        "role": st.secrets.snowflake.role,
        "database": st.secrets.snowflake.database,
        "schema": st.secrets.snowflake.schema,
        "warehouse": st.secrets.snowflake.warehouse,
    }
    return Session.builder.configs(connection_params).create()

# Initialize root using the single Snowpark session
def get_root():
    """Create and retrieve a single instance of Root."""
    session = get_snowpark_session()
    return Root(session)

# Retrieve the session and root globally
snowpark_session = get_snowpark_session()
root = get_root()

# Service Parameters
CORTEX_SEARCH_DATABASE = "LEGAL_DATA_DB"
CORTEX_SEARCH_SCHEMA = "LEGAL_DATA_SCHEMA"
CORTEX_SEARCH_SERVICE = "LEGAL_JUDGEMENTS_CORTEX_SEARCH_SERVICE"

# Cortex Search Retriever Class
class CortexSearchRetriever:
    def __init__(self, limit_to_retrieve: int = 4):
        self._limit_to_retrieve = limit_to_retrieve

    def retrieve(self, query: str) -> List[str]:
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
        if st.session_state.use_chat_history:
            chat_history = get_chat_history()

        question_summary = ""
        if chat_history:
            question_summary = summarize_question_with_history(chat_history, query)

        if not context:
            context = ["No relevant context found"]

        prompt = f"""
        You are an expert Indian legal assistant analyzing Supreme Court cases.
        Analyze the following legal scenario and relevant case laws to provide advice.

        Scenario Question:
        {query}
        <chat history> {question_summary} </chat history>
        Context: {context[0]}

        Please provide:
        1. A brief analysis of how the top 3 cases relate to the scenario
        2. Key legal principles established in these cases (keep it short)
        3. Potential application to the current scenario
        4. Recommended course of action based on these precedents

        Format your response in a clear, structured manner with case citations.
        If certain aspects are not covered by these cases, clearly state so.
        """

        try:
            return Complete("mistral-7b", prompt)
        except Exception as e:
            return str(e)

    def query(self, query: str) -> str:
        raw_cases = self.retrieve_context(query)
        return self.generate_legal_analysis(query, raw_cases)

@st.cache_resource()
def get_legal_rag():
    """Create or retrieve LegalRAG instance."""
    return LLegalRAG()

def init_messages():
    """Initialize chat history."""
    if st.session_state.get("clear_conversation", False) or "messages" not in st.session_state:
        st.session_state.messages = []

def get_chat_history():
    """Get the chat history within the sliding window."""
    slide_window = 5  # Set an appropriate sliding window size
    start_index = max(0, len(st.session_state.messages) - slide_window)
    return st.session_state.messages[start_index:]

def config_options():
    """Set up sidebar options."""
    st.sidebar.selectbox(
        'Select your model:',
        ('mistral-7b', 'mistral-large', 'mixtral-8x7b'),
        key="model_name"
    )
    st.sidebar.checkbox('Remember chat history?', key="use_chat_history", value=True)
    st.sidebar.button("Start Over", key="clear_conversation", on_click=init_messages)

def summarize_question_with_history(chat_history, question):
    prompt = f"""
        Based on the chat history below and the question, generate a query that extends the question
        with the chat history provided. The query should be in natural language. 
        Answer with only the query. Do not add any explanation.
        
        <chat_history>
        {chat_history}
        </chat_history>
        <question>
        {question}
        </question>
        """
    return Complete(st.session_state.model_name, prompt)

def main():
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
                response = legal_rag.query(question)
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
