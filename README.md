
# Indian Legal Assistant - Streamlit App - Team Lawgorithm

This application provides an interactive platform where users can ask questions related to Indian Supreme Court cases and receive legal analysis based on relevant case precedents. It uses a combination of Snowflake Cortex search and an AI model for generating legal advice.

## Features

- **Legal Query Handling**: Users can ask legal questions, and the system retrieves relevant Supreme Court cases.
- **Legal Analysis**: The system provides a structured legal analysis based on retrieved cases, including key legal principles and recommendations.
- **Model Selection**: The app allows users to choose the underlying AI model for generating legal analysis.
- **Chat History**: Users can opt to save chat history for context in future queries.
- **Search Service Integration**: Uses Snowflake's Cortex search service to retrieve relevant legal cases.

## Requirements

- **Streamlit**: Web app framework for building the UI.
- **Snowflake**: Snowflake's Snowpark and Cortex services for legal case retrieval.
- **pandas**: For handling data structures and displaying cases.
- **mistral-large**: AI model used for generating legal analysis.

## Setup

### 1. Install Dependencies

Install the required libraries by running:

```bash
pip install -r requirements.txt
```

### 2. Snowflake Setup

Ensure you have access to a Snowflake account and the following:

- Snowflake database `LEGAL_DATA_DB`
- Snowflake schema `LEGAL_DATA_SCHEMA`
- Snowflake Cortex search service `LEGAL_JUDGEMENTS_CORTEX_SEARCH_SERVICE`

Ensure your Snowflake credentials and connection parameters are correctly configured.

### 3. Configuration

Edit the configuration variables in the script to match your Snowflake setup:

- `CORTEX_SEARCH_DATABASE`: The database containing legal judgment data.
- `CORTEX_SEARCH_SCHEMA`: The schema containing the legal judgment data.
- `CORTEX_SEARCH_SERVICE`: The name of the Cortex search service to use.

### 4. Run the Streamlit App

Run the app using Streamlit:

```bash
streamlit run streamlit_app.py
```

This will start a local development server. Open the URL provided by Streamlit to access the application in your browser.

## Usage

1. **Select Model**: Choose the AI model you wish to use for legal analysis (e.g., `mistral-7b`, `mistral-large`).
2. **Ask Legal Questions**: Type your legal query in the input box and press enter. The system will retrieve relevant Supreme Court cases and provide legal analysis.
3. **View Analysis**: The app will show the analysis, including key legal principles, case citations, and recommendations.
4. **Save Chat History**: Choose whether you want to remember previous chat history for context in future queries.

## Code Structure

- **CortexSearchRetriever Class**: Handles querying the Snowflake Cortex search service for relevant legal cases.
- **LLegalRAG Class**: Implements the Legal RAG (Retrieve-Analyze-Generate) system, which retrieves relevant cases and generates legal analysis.
- **Streamlit Interface**: Provides a user-friendly chat interface for asking legal questions and displaying responses.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
