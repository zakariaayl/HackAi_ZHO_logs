## Project Idea

This project is a **conversational AI assistant** designed to help Moroccan users easily access information about administrative documents and procedures in their own language, **Moroccan Darija**.

### Why This Idea?

In Morocco, many people struggle to find clear and accessible information about government paperwork — such as what documents are needed for a passport, ID card, or other official procedures. This problem is especially challenging for those who:

- Prefer to communicate in Moroccan Darija rather than formal Arabic or French,  
- Have limited experience using digital platforms, or  
- Face difficulties navigating complex official websites and bureaucracy.

### What Does the Project Do?

- The assistant accepts **user questions in Moroccan Darija via text or voice input**.  
- It includes **transcription capabilities** that convert voice inputs in Moroccan Darija into text.  
- It uses a powerful language model (Google’s Gemini model) combined with a web search tool that fetches current, relevant information from Moroccan websites using SerpAPI.  
- It processes and summarizes search results to provide clear, concise answers that are easy to understand.  
- It maintains conversation history to offer context-aware responses, supporting follow-up questions and clarifications.

### Benefits

- Helps bridge the information gap by making administrative knowledge accessible to a wider audience, including those who prefer speaking over typing.  
- Supports Morocco’s ongoing efforts to modernize and digitalize public administration by improving citizen access to information.  
- Reduces confusion and the risk of errors in bureaucratic processes, potentially saving time and effort for individuals.  
- Provides a user-friendly tool that leverages AI, speech-to-text technology, and web search tailored specifically for Moroccan users.


## Code Overview

The project combines several key components to deliver its functionality:

### 1. Language Model Integration

- Uses **Google’s Gemini model** via the `smolagents` library (`OpenAIServerModel`) to process and generate natural language responses.  
- The model understands Moroccan Darija and manages the conversational flow.

### 2. Custom Search Tool (`SearchWebTool`)

- A custom tool built as a subclass of `Tool` that performs live web searches using **SerpAPI**.  
- Searches are restricted to Moroccan websites and Arabic language results to ensure relevant, local information.  
- Retrieves and summarizes the top search results to feed back to the user.

### 3. Agent (`ToolCallingAgent`)

- Manages interactions between the language model and the search tool.  
- Receives user inputs, decides when to call the search tool, and composes final responses based on model outputs and web search data.

### 4. Chat Interface and History

- Maintains a **conversation history** to provide context-aware responses.  
- Supports multiple user queries in a session, allowing for follow-up questions and clarifications.

### 5. (Optional) Voice Input and Transcription

- Can be extended to handle **voice inputs** by integrating a speech-to-text engine that transcribes Moroccan Darija audio into text before processing.  
- Enables more natural, accessible interaction for users preferring spoken communication.

---

### How to Extend or Modify

- To add new tools, create subclasses of `Tool` and register them in the `ToolCallingAgent`.  
- Customize the model parameters or switch models by modifying the `OpenAIServerModel` initialization.  
- Implement front-end interfaces (web, mobile) that connect to this backend chat agent for user interaction.



---

This project empowers Moroccan citizens by giving them an intelligent assistant that understands their spoken language and connects them to vital bureaucratic information — simplifying their interactions with government services in the digital age.
