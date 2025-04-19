"""
Profile Identifier Tool for the ice breaker agent.
"""
import json
import re
from typing import List, Dict, Any, Optional, Union
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from app.agent.prompts import PROFILE_IDENTIFICATION_PROMPT, PROFILE_ANALYSIS_PROMPT
from app.core.logging import logger
from app.models.schemas import SearchResult, ProfileInfo

class ProfileIdentifierTool:
    """Tool for identifying relevant profiles from search results and analyzing profiles."""
    
    def __init__(self, llm):
        """Initialize the profile identifier tool.
        
        Args:
            llm: Language model to use for generating responses
        """
        self.llm = llm
        
        # Create prompt templates
        self.identification_prompt = PromptTemplate.from_template(PROFILE_IDENTIFICATION_PROMPT)
        self.analysis_prompt = PromptTemplate.from_template(PROFILE_ANALYSIS_PROMPT)
        
        # Create LLM chains
        self.identification_chain = LLMChain(llm=llm, prompt=self.identification_prompt)
        self.analysis_chain = LLMChain(llm=llm, prompt=self.analysis_prompt)
    
    async def identify_profiles(self, input_data: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Identify relevant profiles from search results.
        
        Args:
            input_data: Either a JSON string or a list of search results
            
        Returns:
            List of relevant profiles with relevance scores
        """
        logger.info("Identifying relevant profiles from search results")
        
        try:
            # Parse input if it's a string
            if isinstance(input_data, str):
                try:
                    search_results = json.loads(input_data)
                except json.JSONDecodeError:
                    # If not valid JSON, try to parse as a SearchResult object
                    search_results = [{"title": input_data, "link": "", "snippet": ""}]
            else:
                search_results = input_data
            
            # Extract the name from the search results
            name = self._extract_name_from_search_results(search_results)
            
            # Format search results for the prompt
            formatted_results = "\n\n".join([
                f"Title: {result.get('title', '')}\n"
                f"URL: {result.get('link', '')}\n"
                f"Snippet: {result.get('snippet', '')}"
                for result in search_results
            ])
            
            # Run the identification chain
            response = await self.identification_chain.ainvoke({
                "name": name,
                "search_results": formatted_results
            })
            
            # Parse the response to extract profile information
            profiles = self._parse_profile_identification_response(response["text"])
            
            logger.info(f"Identified {len(profiles)} relevant profiles")
            return profiles
        
        except Exception as e:
            logger.error(f"Error identifying profiles: {str(e)}", exc_info=True)
            return []
    
    async def analyze_profile(self, profile_content: str) -> Dict[str, Any]:
        """Analyze a profile to extract structured information.
        
        Args:
            profile_content: HTML or text content of a profile
            
        Returns:
            Structured information extracted from the profile
        """
        logger.info("Analyzing profile content")
        
        try:
            # Run the analysis chain
            response = await self.analysis_chain.ainvoke({
                "profile_content": profile_content
            })
            
            # Parse the response to extract profile information
            profile_info = self._parse_profile_analysis_response(response["text"])
            
            logger.info("Profile analysis complete")
            return profile_info
        
        except Exception as e:
            logger.error(f"Error analyzing profile: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "raw_text": profile_content[:500] + "..." if len(profile_content) > 500 else profile_content
            }
    
    def _extract_name_from_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Extract the name of the person from search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            Extracted name or empty string
        """
        # Look for patterns like "John Doe - LinkedIn", "John Doe | Twitter", etc.
        for result in search_results:
            title = result.get("title", "")
            
            # Check for common profile title patterns
            match = re.search(r"^([^|–-]+)[\s]*[|–-]", title)
            if match:
                return match.group(1).strip()
            
            # Check for name in URL
            link = result.get("link", "")
            for platform in ["linkedin.com/in/", "twitter.com/", "github.com/"]:
                if platform in link:
                    parts = link.split(platform)[1].split("/")[0].split("?")[0]
                    # Convert username to potential name (e.g., "john-doe" -> "John Doe")
                    name = " ".join([p.capitalize() for p in parts.split("-") if p])
                    if name:
                        return name
        
        # If no name found, return empty string
        return ""
    
    def _parse_profile_identification_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response to extract profile information.
        
        Args:
            response: LLM response text
            
        Returns:
            List of profiles with relevance scores
        """
        profiles = []
        
        # Split response by lines
        lines = response.split("\n")
        
        current_profile = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new profile entry
            if re.match(r"^[0-9]+[\.\)]*", line) or "Platform:" in line or "URL:" in line:
                # Save previous profile if exists
                if current_profile and "url" in current_profile and "platform" in current_profile:
                    profiles.append(current_profile)
                    current_profile = {}
            
            # Extract URL
            url_match = re.search(r"URL:?\s*(https?://[^\s]+)", line, re.IGNORECASE)
            if url_match:
                current_profile["url"] = url_match.group(1)
            
            # Extract platform
            platform_match = re.search(r"Platform:?\s*([^\s:]+)", line, re.IGNORECASE)
            if platform_match:
                current_profile["platform"] = platform_match.group(1)
            
            # Extract relevance score
            score_match = re.search(r"(Relevance|Score|Likelihood):?\s*(0\.\d+|1\.0)", line, re.IGNORECASE)
            if score_match:
                current_profile["relevance_score"] = float(score_match.group(2))
            
            # Extract title
            title_match = re.search(r"Title:?\s*(.+)$", line, re.IGNORECASE)
            if title_match:
                current_profile["title"] = title_match.group(1)
        
        # Add the last profile if exists
        if current_profile and "url" in current_profile and "platform" in current_profile:
            profiles.append(current_profile)
        
        # Ensure required fields and set defaults
        for profile in profiles:
            profile.setdefault("relevance_score", 0.5)
            profile.setdefault("title", "")
        
        # Sort by relevance score (descending)
        profiles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return profiles
    
    def _parse_profile_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract structured profile information.
        
        Args:
            response: LLM response text
            
        Returns:
            Structured profile information
        """
        profile_info = {
            "name": None,
            "title": None,
            "bio": None,
            "experience": [],
            "education": [],
            "skills": [],
            "interests": [],
            "posts": [],
            "raw_text": response
        }
        
        # Split response by sections
        sections = re.split(r"\n\s*#+\s*|\n\s*\*{3,}\s*|\n\s*-{3,}\s*|\n\s*_{3,}\s*", response)
        
        current_section = "unknown"
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Identify section type
            lines = section.split("\n")
            header = lines[0].lower().strip()
            
            if "name" in header:
                current_section = "name"
                profile_info["name"] = "\n".join(lines[1:]).strip()
            elif any(k in header for k in ["title", "headline", "position"]):
                current_section = "title"
                profile_info["title"] = "\n".join(lines[1:]).strip()
            elif any(k in header for k in ["bio", "about", "summary"]):
                current_section = "bio"
                profile_info["bio"] = "\n".join(lines[1:]).strip()
            elif any(k in header for k in ["experience", "work", "employment", "job"]):
                current_section = "experience"
                # Parse experience entries
                experience_text = "\n".join(lines[1:]).strip()
                experiences = []
                
                # Split by potential experience entries
                exp_entries = re.split(r"\n\s*-\s*|\n\s*\*\s*|\n\s*[0-9]+\.\s*", experience_text)
                for entry in exp_entries:
                    entry = entry.strip()
                    if not entry:
                        continue
                    
                    # Try to extract company and position
                    company_match = re.search(r"at\s+([^,\.]+)", entry, re.IGNORECASE)
                    company = company_match.group(1).strip() if company_match else None
                    
                    # Extract date ranges
                    date_match = re.search(r"(\d{4}\s*-\s*\d{4}|\d{4}\s*-\s*Present|\d{4})", entry)
                    date_range = date_match.group(1).strip() if date_match else None
                    
                    experiences.append({
                        "description": entry,
                        "company": company,
                        "date_range": date_range
                    })
                
                profile_info["experience"] = experiences
            elif any(k in header for k in ["education", "study", "university", "college", "school"]):
                current_section = "education"
                # Parse education entries
                education_text = "\n".join(lines[1:]).strip()
                educations = []
                
                # Split by potential education entries
                edu_entries = re.split(r"\n\s*-\s*|\n\s*\*\s*|\n\s*[0-9]+\.\s*", education_text)
                for entry in edu_entries:
                    entry = entry.strip()
                    if not entry:
                        continue
                    
                    # Try to extract institution and degree
                    institution_match = re.search(r"([^,\.]+University|College|School|Institute)", entry)
                    institution = institution_match.group(1).strip() if institution_match else None
                    
                    degree_match = re.search(r"(Bachelor|Master|PhD|Doctorate|BSc|MSc|BA|MA|MBA)", entry)
                    degree = degree_match.group(1).strip() if degree_match else None
                    
                    # Extract date ranges
                    date_match = re.search(r"(\d{4}\s*-\s*\d{4}|\d{4}\s*-\s*Present|\d{4})", entry)
                    date_range = date_match.group(1).strip() if date_match else None
                    
                    educations.append({
                        "description": entry,
                        "institution": institution,
                        "degree": degree,
                        "date_range": date_range
                    })
                
                profile_info["education"] = educations
            elif any(k in header for k in ["skill", "expertise", "proficiency"]):
                current_section = "skills"
                # Parse skills
                skills_text = "\n".join(lines[1:]).strip()
                skills = []
                
                # Extract skills listed with separators
                skill_entries = re.split(r",|\n\s*-\s*|\n\s*\*\s*|\n\s*[0-9]+\.\s*", skills_text)
                for entry in skill_entries:
                    entry = entry.strip()
                    if entry:
                        skills.append(entry)
                
                profile_info["skills"] = skills
            elif any(k in header for k in ["interest", "hobby", "passion"]):
                current_section = "interests"
                # Parse interests
                interests_text = "\n".join(lines[1:]).strip()
                interests = []
                
                # Extract interests listed with separators
                interest_entries = re.split(r",|\n\s*-\s*|\n\s*\*\s*|\n\s*[0-9]+\.\s*", interests_text)
                for entry in interest_entries:
                    entry = entry.strip()
                    if entry:
                        interests.append(entry)
                
                profile_info["interests"] = interests
            elif any(k in header for k in ["post", "tweet", "activity", "update"]):
                current_section = "posts"
                # Parse posts
                posts_text = "\n".join(lines[1:]).strip()
                posts = []
                
                # Extract posts
                post_entries = re.split(r"\n\s*-\s*|\n\s*\*\s*|\n\s*[0-9]+\.\s*", posts_text)
                for entry in post_entries:
                    entry = entry.strip()
                    if entry:
                        posts.append({"content": entry})
                
                profile_info["posts"] = posts
        
        return profile_info