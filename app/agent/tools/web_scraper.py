"""
Web Scraper Tool for the ice breaker agent.
"""
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import re
from app.core.logging import logger

class WebScraperTool:
    """Tool for scraping content from web pages."""
    
    def __init__(self, user_agent: str, timeout: int = 10):
        """Initialize the web scraper tool.
        
        Args:
            user_agent: User agent string to use for requests
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def scrape(self, url: str) -> Dict[str, Any]:
        """Scrape content from a web page.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing the scraped content
        """
        logger.info(f"Scraping URL: {url}")
        
        try:
            # Determine which specialized scraper to use
            if "linkedin.com" in url.lower():
                return await self._scrape_linkedin(url)
            elif any(domain in url.lower() for domain in ["twitter.com", "x.com"]):
                return await self._scrape_twitter(url)
            elif "github.com" in url.lower():
                return await self._scrape_github(url)
            else:
                # Generic scraper for other websites
                return await self._scrape_generic(url)
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "content": "",
                "title": "",
                "platform": "unknown"
            }
    
    async def _scrape_generic(self, url: str) -> Dict[str, Any]:
        """Generic scraper for any website.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing the scraped content
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, timeout=self.timeout) as response:
                if response.status != 200:
                    return {
                        "url": url,
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "content": "",
                        "title": "",
                        "platform": "unknown"
                    }
                
                html = await response.text()
                
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        
        # Extract title
        title = soup.title.string if soup.title else ""
        
        # Extract main content
        # Try to find the main content area
        main_content = soup.find(["main", "article", "div", "body"])
        
        # Clean the content
        if main_content:
            # Remove script and style tags
            for script in main_content(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get the text
            content = main_content.get_text(separator="\n", strip=True)
        else:
            content = soup.get_text(separator="\n", strip=True)
        
        # Determine the platform
        platform = "unknown"
        if "linkedin.com" in url:
            platform = "LinkedIn"
        elif any(domain in url for domain in ["twitter.com", "x.com"]):
            platform = "Twitter"
        elif "github.com" in url:
            platform = "GitHub"
        elif "facebook.com" in url:
            platform = "Facebook"
        elif "instagram.com" in url:
            platform = "Instagram"
        elif "medium.com" in url:
            platform = "Medium"
        elif re.search(r"\.(edu|ac\.[a-z]{2})\/", url):
            platform = "Academic"
        elif "about" in url.lower() or "bio" in url.lower():
            platform = "Personal Website"
        
        return {
            "url": url,
            "success": True,
            "content": content,
            "html": html,
            "title": title,
            "platform": platform
        }
    
    async def _scrape_linkedin(self, url: str) -> Dict[str, Any]:
        """Specialized scraper for LinkedIn profiles.
        
        Args:
            url: LinkedIn profile URL
            
        Returns:
            Dictionary containing the scraped content
        """
        # LinkedIn is tricky to scrape due to authentication requirements
        # First try with the generic approach
        result = await self._scrape_generic(url)
        
        # Enhance the response with LinkedIn-specific metadata
        result["platform"] = "LinkedIn"
        
        # Check if the content indicates a login wall
        if "Sign in" in result["content"] and "to view" in result["content"]:
            logger.warning("LinkedIn login wall detected")
            result["login_required"] = True
            result["content"] += "\n\nNote: Full LinkedIn profile requires login. Only public information is available."
        
        # Extract structured data if available
        soup = BeautifulSoup(result["html"], "lxml")
        
        # Try to extract profile sections
        sections = {}
        
        # Name and headline
        name_elem = soup.select_one(".pv-top-card-section__name, .text-heading-xlarge")
        if name_elem:
            sections["name"] = name_elem.get_text(strip=True)
        
        headline_elem = soup.select_one(".pv-top-card-section__headline, .text-body-medium")
        if headline_elem:
            sections["headline"] = headline_elem.get_text(strip=True)
        
        # About/summary section
        about_elem = soup.select_one("#about-section, .pv-about-section")
        if about_elem:
            sections["about"] = about_elem.get_text(separator="\n", strip=True)
        
        # Add the structured data to the result
        result["structured_data"] = sections
        
        return result
    
    async def _scrape_twitter(self, url: str) -> Dict[str, Any]:
        """Specialized scraper for Twitter profiles.
        
        Args:
            url: Twitter profile URL
            
        Returns:
            Dictionary containing the scraped content
        """
        result = await self._scrape_generic(url)
        
        # Enhance the response with Twitter-specific metadata
        result["platform"] = "Twitter"
        
        # Extract structured data if available
        soup = BeautifulSoup(result["html"], "lxml")
        
        # Try to extract profile sections
        sections = {}
        
        # Bio
        bio_elem = soup.select_one("[data-testid='UserDescription'], .ProfileHeaderCard-bio")
        if bio_elem:
            sections["bio"] = bio_elem.get_text(strip=True)
        
        # Location
        location_elem = soup.select_one("[data-testid='UserLocation'], .ProfileHeaderCard-location")
        if location_elem:
            sections["location"] = location_elem.get_text(strip=True)
        
        # Recent tweets
        tweets = []
        tweet_elems = soup.select("[data-testid='tweet'], .tweet")
        for tweet_elem in tweet_elems[:5]:  # Limit to 5 tweets
            tweet_text = tweet_elem.get_text(separator=" ", strip=True)
            if tweet_text:
                tweets.append(tweet_text)
        
        sections["recent_tweets"] = tweets
        
        # Add the structured data to the result
        result["structured_data"] = sections
        
        return result
    
    async def _scrape_github(self, url: str) -> Dict[str, Any]:
        """Specialized scraper for GitHub profiles.
        
        Args:
            url: GitHub profile URL
            
        Returns:
            Dictionary containing the scraped content
        """
        result = await self._scrape_generic(url)
        
        # Enhance the response with GitHub-specific metadata
        result["platform"] = "GitHub"
        
        # Extract structured data if available
        soup = BeautifulSoup(result["html"], "lxml")
        
        # Try to extract profile sections
        sections = {}
        
        # Bio
        bio_elem = soup.select_one(".user-profile-bio")
        if bio_elem:
            sections["bio"] = bio_elem.get_text(strip=True)
        
        # Repositories
        repos = []
        repo_elems = soup.select(".pinned-item-list-item")
        for repo_elem in repo_elems:
            repo_name_elem = repo_elem.select_one("a.text-bold")
            repo_desc_elem = repo_elem.select_one("p.pinned-item-desc")
            
            if repo_name_elem:
                repo = {
                    "name": repo_name_elem.get_text(strip=True),
                    "description": repo_desc_elem.get_text(strip=True) if repo_desc_elem else ""
                }
                repos.append(repo)
        
        sections["pinned_repositories"] = repos
        
        # Add the structured data to the result
        result["structured_data"] = sections
        
        return result