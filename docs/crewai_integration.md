# CrewAI Integration Documentation

## Overview
This document outlines the integration of CrewAI into the Language Tutor application, focusing on the implementation of the Dutch Tutor AI with RAG functionality.

## Features of CrewAI Integration
- **Agent Management**: Create and manage agents for various tasks such as scraping, processing, and querying.
- **Task Automation**: Automate tasks related to language learning and content retrieval.
- **Real-time Interaction**: Enable real-time interactions with users for language practice using the latest news articles.

## Setup Instructions
1. **Install Dependencies**: Ensure that the necessary packages are installed in your environment:
   ```bash
   pip install crewai crewai-tools openai weaviate-client
   ```

2. **Configure Environment Variables**: Add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Define Agents**: Create agents in the `agents.yaml` file to handle tasks such as scraping and processing.

4. **Create Tasks**: Define tasks in the `tasks.yaml` file to automate the workflow for the Dutch Tutor.

## Example Agent Configuration
```yaml
agents:
  - name: ScraperAgent
    role: "Web Scraper"
    goal: "Fetch the latest Dutch news articles."
  - name: ProcessingAgent
    role: "Data Processor"
    goal: "Process scraped articles and generate embeddings."
```

## Conclusion
Integrating CrewAI enhances the Language Tutor application by providing advanced capabilities for language learning and content management, making the experience more engaging and effective for users.
