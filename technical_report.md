# User Demand
In the academic field, large language models often struggle to provide real and reliable references, making it difficult to assist related studies. In particular, newcomers to a research area urgently need to quickly understand the basic knowledge, recent progress, challenges, and future directions of the field. If large language models can assist in reading relevant papers, it will greatly reduce the individual effort required.

Here, such an application will be designed.

**Input:**

The main input is the name of a research field of interest. Besides, one can also decide the year range of collected papers, number of papers collected, temperature, and whether to use DeepSeek-chat or GPT-4 to build summaries. 

**Output:**

1. List relevant papers in the field, including title, authors, abstract, link, etc.

2. Generate a review of the research field based on the related papers.

# Technology Selection
## Paper Retrieval Tools
Currently, easily accessible paper retrieval tools via API include Semantic Scholar and Arxiv. However, applying for the Semantic Scholar API takes three to four weeks, and access has not yet been granted.
Therefore, only the public `Arxiv` API is used as the paper retrieval tool here, which is a makeshift.
## Vectorization
`paraphrase-multilingual-MiniLM-L12-v2` is used to embed the title and abstract of a given paper. 
## Paper Summarization Tool
A large language model is needed to summarize the relevant papers. Here, the `deepseek-chat` model is called via API as the LLM for review generation.

# Academic Review System Archetecture
The archetecture of this system can be summarized as:
Domain Input → Paper Search → Content Processing → Comprehensive Review Generation
![System Archetecture](./flowchart.png)


# Implementation Details
## Retrieving Papers for a Given topic
Public Arxiv API is applied to obtain titles, authors, years, abstracts, and urls for each paper of the given topic.
## Paper Filtering
`SentenceTransformer` is used to apply `paraphrase-multilingual-MiniLM-L12-v2` to convert the title and abstract of each paper into a numerical vector (embedding) that captures the semantic meaning of the text. This allows the script to represent each paper as a point in a high-dimensional space, making it possible to compare papers based on their content.

`faiss` is a library for efficient similarity search and clustering of dense vectors. In this script, it is used to build an index of the paper embeddings and perform similarity-based deduplication. This helps to filter out duplicate or very similar papers by comparing their embeddings and keeping only unique ones.

## Review Generation
With specific prompts designed, `deepseek-chat` is used for generating a review on the given topic, outputs being JSONs containing overview, trends, challenges, and future directions. The review is generated from papers just retrieved.
## Injection protection
A comprehensive injection protection to the academic review system is added. 
`security.py` is constructed to provide functions checking the injections.
To be specific, it includes SQL injection protection (blocks `SELECT`, `DROP`, `Union`, etc.), command injection protection (blocks `system`, `rm`, etc.), script injection protection (blocks `<script>`, `javascript:`, etc.), python code injection protection (blocks `eval`, `__import__`, etc.), output sanitization (prevents XSS, invalidate URLs, etc), live feedback in the Streamlit sidebar with ✅/❌ indicators, and clear error messages for security violations. 
## Interacting Interface
The interface is built through `streamlit`. At sidebars, users are able to decide the desired topic, year range, number of collected papers, temperature, which model to use (DeepSeek or GPT-4, the latter is inaccessible due to API payment overdue), and whether generating the review simply from the abstracts. In addition, verbatim/chunked output effects are implemented for the output. And the output is converted to markdown.
## Memory Mechanism
Caching functions are build in `main.py`. By using @st.cache_data, Streamlit will store the results of these functions. If the function is called again with the same inputs, it will return the cached result instead of re-running the code, saving time and API calls.
## Download Report
The review generated could be downloaded as JSON or Markdown files. 

# Evaluation
## Comparison Between Different Temperatures
The input topic fixed as "Spice Netlist", year range being 2020-2024 and number of papers set at 5, temperatures at 0.7 and 1.2 are tested respectively as below. 

The review generated with temperature=0.7 is located at [./temperature_comparison_07.txt](./temperature_comparison_07.txt) while the review generated with temperature=1.2 is located at [./temperature_comparison_12.txt](./temperature_comparison_12.txt). 

When temperature=0.7, the review generated opens with a survey-style tone, emphasizing contributions of key papers and technologies like in-memory computing and advanced nodes. It feels more like a formal literature review with academic structure.

When temperature=1.2, the review is more synthesis-oriented, summarizing innovations as a response to real-world demands (“growing complexity,” “energy-efficient architectures”), rather than highlighting specific papers.

## Highlights 
Compared to directly calling LLM to give a scope on a certain academic topic, this system is distinguished in:

1. collecting true papers with URLs related to the topic

2. more well-structured review

3. adjustable temperatures and models (although only deepseek-chat is tested currently, with the absence of an OpenAI API with a credit card)

4. reviews based on the academic papers

# Reflection
Some detailed problems come up during the process, including errors when applying APIs, output format failures, etc. 
Furthermore, there are still some incapability of the system, which sometimes cannot returns closely-related papers on certain topics. This may reult from weakness of Arxiv API and could probably be resolved when turning to Semantic Scholar API. The latter, however, is currently not accessible since it requires at least three weeks to request.