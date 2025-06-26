from openai import OpenAI
from typing import List
from config import ReviewOutput, Paper, DomainInput
import json
import time
import os
from security import security_validator

class ReviewGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        
    def generate_with_params(self, papers: List[Paper], domain: str, 
                           temperature: float, model: str = "deepseek") -> ReviewOutput:
        """Generate review with different parameters and security validation"""
        # Validate inputs
        validated_input = security_validator.validate_domain_input(domain, "2020-2024", len(papers), temperature)
        domain = validated_input['domain']
        temperature = validated_input['temperature']
        
        prompt = self._build_prompt(papers, domain)
        
        if model == "deepseek":
            response = self._stream_deepseek(prompt, temperature)
        else:
            response = self._stream_openai(prompt, temperature)
        
        # Use basic sanitization for output content
        response = security_validator.sanitize_output(response)
            
        try:
            # The model might return the JSON wrapped in markdown ```json ... ```
            # or with some leading/trailing text. We need to extract the JSON object.
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return ReviewOutput(**json.loads(json_str))
            
            # If we can't find a JSON object, we'll fall through to the 'except' block
            raise json.JSONDecodeError("Could not find JSON object in the response", response, 0)

        except json.JSONDecodeError:
            # Fallback for failed structured output
            return ReviewOutput(
                overview=f"Error: The model did not return a valid JSON object. Below is the raw response from the model:\n\n---\n\n{security_validator.sanitize_output(response)}",
                key_papers=papers[:3],
                trends="",
                challenges="",
                future_directions=""
            )
    
    def _build_prompt(self, papers: List[Paper], domain: str) -> str:
        papers_str = ""
        for i, p in enumerate(papers):
            # Sanitize paper data to prevent injection through paper content
            safe_title = security_validator.sanitize_output(p.title)
            safe_authors = [security_validator.sanitize_output(author) for author in p.authors]
            safe_abstract = security_validator.sanitize_output(p.abstract[:200])
            
            papers_str += f"{i+1}. {safe_title} ({p.year}) - Citations: {p.citations}\n"
            papers_str += f"Authors: {', '.join(safe_authors)}\nAbstract: {safe_abstract}..."
        
        # Sanitize domain input as well
        safe_domain = security_validator.sanitize_output(domain)
        
        return f"""Please generate a structured review based on the following papers in the '{safe_domain}' field.

Your entire response MUST be a single, valid JSON object. Do not add any text, comments, or explanations before or after the JSON object.

The JSON object must conform to the following schema:
{json.dumps(ReviewOutput.model_json_schema(), indent=2)}

Instructions for the content inside the JSON:
1.  The text for "overview", "trends", "challenges", and "future_directions" should be written in clear, readable Markdown.
2.  The "key_papers" analysis should be based on the papers provided below.
3.  Ensure all fields in the schema are present in your JSON output.

Available papers:
{papers_str}

Now, generate the JSON response:"""
    
    def _stream_deepseek(self, prompt: str, temperature: float) -> str:
        full_response = ""
        for chunk in self.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=True
        ):
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)  # Streaming output
            full_response += content
            time.sleep(0.05)
        print("\n")
        return full_response
    
    def _stream_openai(self, prompt: str, temperature: float) -> str:
        full_response = ""
        for chunk in self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=True
        ):
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)  # Streaming output
            full_response += content
            time.sleep(0.05)
        print("\n")
        return full_response