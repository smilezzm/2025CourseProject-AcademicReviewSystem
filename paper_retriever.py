import arxiv
from typing import List
from config import Paper, DomainInput
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
from security import security_validator


class PaperRetriever:
    def __init__(self):
        # Load the model from a local path to avoid network issues.
        # Make sure you have downloaded the model files and placed them in this directory.
        local_model_path = 'd:\\yao\\PkU\\Academic2024-2025\\AI basics\\final_project\\academic_review\\local_models\\paraphrase-multilingual-MiniLM-L12-v2'
        self.embedder = SentenceTransformer(local_model_path)
        self.index = faiss.IndexFlatL2(384)  # Match embedding dimension
        
    def search_papers(self, domain: str, years: str, count: int) -> List[Paper]:
        """Search for papers using the arXiv API"""
        # Input validation and sanitization
        validated_input = security_validator.validate_domain_input(
            domain, years, count, 0.7  # temperature not used here, just for validation
        )
        
        domain = validated_input['domain']
        years = validated_input['years']
        count = validated_input['paper_count']
        
        # Parse year range
        year_start, year_end = map(int, years.split('-'))
        
        # Build arXiv query
        query = f'all:"{domain}"'
        if year_start and year_end:
            query += f" AND submittedDate:[{year_start}01010000 TO {year_end}12312359]"
        
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=min(count * 2, 50),  # Retrieve more for filtering
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        # Get paper results
        papers = []
        try:
            for result in client.results(search):
                papers.append({
                    "title": result.title,
                    "authors": [a.name for a in result.authors],
                    "year": result.published.year,
                    "abstract": result.summary,
                    "url": result.entry_id,
                    "citation_count": 0
                })
        except arxiv.ArxivError as e:
            raise ValueError(f"arXiv API Error: {str(e)}")
        
        # Vectorize search results and deduplicate
        if len(papers) > 1:
            texts = [f"{p['title']} {p['abstract']}" for p in papers]
            embeddings = self.embedder.encode(texts, normalize_embeddings=True)
            self.index.add(embeddings)
            
            # Use FAISS for similarity-based deduplication
            _, indices = self.index.search(embeddings, k=2)
            unique_indices = set()
            for i in range(len(indices)):
                # If the second nearest neighbor is itself (-1) or the first neighbor is not already added
                if len(indices[i]) < 2 or indices[i][1] == -1 or indices[i][0] not in unique_indices:
                    unique_indices.add(indices[i][0])
            
            # Ensure we don't try to access an index that doesn't exist
            valid_indices = [i for i in unique_indices if i < len(papers)]
            papers = [papers[i] for i in sorted(list(valid_indices))][:count]
        
        processed_papers = []
        for p in papers:
            # Apply security sanitization to paper content
            safe_title = security_validator.sanitize_output(self._clean_text(p["title"]))
            safe_abstract = security_validator.sanitize_output(self._clean_text(p["abstract"]))
            safe_authors = [security_validator.sanitize_output(author) for author in p["authors"]]
            
            # Validate URL for safety
            safe_url = p["url"] if security_validator.validate_url(p["url"]) else "https://arxiv.org/"
            
            paper_obj = Paper(
                title=safe_title,
                authors=safe_authors,
                year=p["year"],
                abstract=safe_abstract,
                url=safe_url,
                citations=p["citation_count"]
            )
            processed_papers.append(paper_obj)
            
        return processed_papers
    
    def _clean_text(self, text: str) -> str:
        """Clean LaTeX and special characters from arXiv text"""
        text = re.sub(r'\$.+?\$', '', text)  # Remove LaTeX equations
        text = re.sub(r'\\[a-z]{1,}', '', text)  # Remove LaTeX commands
        return text.strip()