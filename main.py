
import streamlit as st
from paper_retriever import PaperRetriever
from review_generator import ReviewGenerator
from config import DomainInput, Paper, ReviewOutput
import json
import re
from typing import List
from security import security_validator

# --- Caching Functions ---
# By using @st.cache_data, Streamlit will store the results of these functions.
# If the function is called again with the same inputs, it will return the cached result
# instead of re-running the code, saving time and API calls.

@st.cache_data
def get_papers(domain: str, years: str, count: int) -> List[Paper]:
    """Retrieves and caches papers from arXiv."""
    # This message will only appear when the cache is "missed" (i.e., the function is run).
    st.info("Cache miss: Retrieving fresh papers from source...")
    retriever = PaperRetriever()
    return retriever.search_papers(domain, years, count)

@st.cache_data
def generate_review(_papers: List[Paper], domain: str, temperature: float, model: str) -> ReviewOutput:
    """Generates and caches the review using the selected LLM."""
    # This message will only appear when the cache is "missed".
    st.info("Cache miss: Generating new review with LLM...")
    generator = ReviewGenerator()
    return generator.generate_with_params(_papers, domain, temperature, model)

# --- Helper function for Markdown export ---
def format_review_as_markdown(review: ReviewOutput, domain: str) -> str:
    """Formats the review object into a downloadable Markdown string."""
    md_content = f"# Academic Review for: {domain}\n\n"
    md_content += "## Overview\n"
    md_content += f"{review.overview}\n\n"
    
    md_content += "## Key Papers Analyzed\n"
    for paper in review.key_papers:
        md_content += f"### {paper.title} ({paper.year})\n"
        md_content += f"- **Authors:** {', '.join(paper.authors)}\n"
        md_content += f"- **Citations:** {paper.citations}\n"
        md_content += f"- **Abstract:** {paper.abstract}\n"
        md_content += f"- **Link:** [{paper.url}]({paper.url})\n\n"
        
    md_content += "## Current Trends\n"
    md_content += f"{review.trends}\n\n"
    
    md_content += "## Major Challenges\n"
    md_content += f"{review.challenges}\n\n"
    
    md_content += "## Future Directions\n"
    md_content += f"{review.future_directions}\n"
    
    return md_content

# --- Streamlit App UI ---

st.title("Domain Paper Review Generation System")
st.markdown("""
Enter the name of the research domain, and the system will automatically retrieve relevant papers and generate a review report.
""")

# Sidebar Configuration
with st.sidebar:
    st.header("Parameter Configuration")
    domain = st.text_input("Research Domain", "Large Language Models", 
                          help="Enter a research domain (letters, numbers, spaces, hyphens only)")
    years = st.text_input("Year Range", "2020-2024",
                         help="Format: YYYY-YYYY (e.g., 2020-2024)")
    paper_count = st.slider("Number of Papers", 1, 20, 5)
    temperature = st.slider("Temperature", 0.1, 2.0, 0.7, 0.1)
    model_choice = st.radio("Model Selection", ["DeepSeek", "GPT-4"])
    
    # Real-time input validation feedback
    if domain:
        try:
            security_validator._sanitize_text_input(domain, 100)
            if not re.match(r'^[\w\s\-\.\(\)\+\&\/]+$', domain):
                st.warning("⚠️ Domain contains invalid characters")
            else:
                st.success("✅ Domain format valid")
        except ValueError as e:
            st.error(f"❌ Domain validation error: {str(e)}")
    
    if years:
        if not re.match(r'^\d{4}-\d{4}$', years):
            st.warning("⚠️ Year format should be YYYY-YYYY")
        else:
            year_start, year_end = map(int, years.split('-'))
            if year_start > year_end or year_start < 1990 or year_end > 2025:
                st.warning("⚠️ Invalid year range")
            else:
                st.success("✅ Year range valid")

if st.button("Generate Review"):
    try:
        # Enhanced Input Validation with security checks
        validated_input = security_validator.validate_domain_input(
            domain, years, paper_count, temperature
        )
        
        # Input Validation
        input_data = DomainInput(
            domain=validated_input['domain'],
            years=validated_input['years'],
            paper_count=validated_input['paper_count'],
            temperature=validated_input['temperature']
        )
        
        # Security check passed message
        st.success("✅ Security validation passed")
        
        # Paper Retrieval (now uses the cached function)
        papers = get_papers(
            input_data.domain,
            input_data.years,
            input_data.paper_count
        )
        
        # Displaying search results
        st.subheader("Retrieved Key Papers")
        for i, paper in enumerate(papers, 1):
            with st.expander(f"{i}. {paper.title} ({paper.year})"):
                st.markdown(f"""
                **Authors**: {', '.join(paper.authors)}  
                **Citations**: {paper.citations}  
                **Abstract**: {paper.abstract}  
                [Original Link]({paper.url})
                """)
        
        # Generating review (now uses the cached function)
        review = generate_review(
            papers,
            input_data.domain,
            input_data.temperature,
            model_choice.lower()
        )
        
        # Displaying review results
        st.subheader(f"{input_data.domain} Domain Review")
        st.markdown(review.overview)
        
        st.subheader("Current Trends")
        st.markdown(review.trends)
        
        st.subheader("Major Challenges")
        st.markdown(review.challenges)
        
        st.subheader("Future Directions")
        st.markdown(review.future_directions)
        
        # --- Download Buttons ---
        st.subheader("Download Report")
        
        # Prepare data for download
        markdown_data = format_review_as_markdown(review, input_data.domain)
        # Note: .dict() is for Pydantic v1. For v2, it's .model_dump()
        json_data = json.dumps(review.model_dump(), indent=2, ensure_ascii=False)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download as Markdown",
                data=markdown_data,
                file_name=f"{domain}_review.md",
                mime="text/markdown"
            )
        with col2:
            st.download_button(
                label="Download as JSON",
                data=json_data,
                file_name=f"{domain}_review.json",
                mime="application/json"
            )
        
    except ValueError as e:
        # Security validation failed
        st.error(f"🚫 Security validation failed: {str(e)}")
        st.warning("Please check your input and try again with valid parameters.")
    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")

# Temperature Parameter Comparison Example
if st.checkbox("Show Temperature Parameter Comparison Example"):
    st.subheader("Temperature Comparison (0.7 vs 1.2)")
    
    example_prompt = "Describe the core concept of quantum computing in one sentence"
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Temperature=0.7**")
        st.code("Quantum computing is a new computing paradigm that uses the principles of quantum mechanics (such as superposition and entanglement) for information processing.", language="text")
    
    with col2:
        st.markdown("**Temperature=1.2**")
        st.code("Imagine that in the microscopic world, those naughty little qubits can be both 0 and 1 at the same time, and they hold hands (entanglement) and dance together. This is the magic of quantum computing!", language="text")