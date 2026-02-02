import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict
import json

class WebsiteAnalyzer:
    def __init__(self, base_url: str, max_pages: int = 50):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.pages: List[Dict] = []
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to the same domain"""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return parsed_base.netloc == parsed_url.netloc
    
    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> tuple:
        """Fetch a page and return its content"""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        html = await response.text()
                        return html, response.status
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None, None
    
    def analyze_page(self, url: str, html: str) -> Dict:
        """Analyze page content and extract information"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No title"
        
        # Extract forms
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'inputs': [{'name': inp.get('name', ''), 'type': inp.get('type', 'text')} 
                          for inp in form.find_all(['input', 'textarea', 'select'])]
            }
            forms.append(form_data)
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if self.is_valid_url(full_url):
                links.append(full_url)
        
        # Identify functionality
        functionality = []
        if forms:
            functionality.append(f"Contains {len(forms)} form(s)")
        if soup.find_all('button'):
            functionality.append(f"Contains {len(soup.find_all('button'))} button(s)")
        if soup.find_all('table'):
            functionality.append(f"Contains {len(soup.find_all('table'))} table(s)")
        
        elements = {
            'forms': forms,
            'links_count': len(links),
            'buttons': len(soup.find_all('button')),
            'tables': len(soup.find_all('table')),
            'images': len(soup.find_all('img'))
        }
        
        return {
            'url': url,
            'title': title,
            'functionality': ', '.join(functionality) if functionality else 'Static page',
            'elements': json.dumps(elements),
            'links': links
        }
    
    async def crawl(self) -> List[Dict]:
        """Crawl the website and return analyzed pages"""
        to_visit = [self.base_url]
        self.visited_urls.add(self.base_url)
        
        async with aiohttp.ClientSession() as session:
            while to_visit and len(self.pages) < self.max_pages:
                current_url = to_visit.pop(0)
                
                html, status = await self.fetch_page(session, current_url)
                if html:
                    page_data = self.analyze_page(current_url, html)
                    self.pages.append(page_data)
                    
                    # Add new links to visit
                    for link in page_data['links']:
                        if link not in self.visited_urls and len(self.visited_urls) < self.max_pages:
                            self.visited_urls.add(link)
                            to_visit.append(link)
        
        return self.pages
    
    def generate_user_stories(self, pages: List[Dict]) -> List[Dict]:
        """Generate user stories based on analyzed pages"""
        stories = []
        
        # Generate stories based on forms found
        for page in pages:
            elements = json.loads(page['elements'])
            forms = elements.get('forms', [])
            
            for i, form in enumerate(forms):
                form_purpose = "submit data"
                if any('login' in inp.get('name', '').lower() for inp in form['inputs']):
                    form_purpose = "log in to the system"
                elif any('register' in inp.get('name', '').lower() or 'signup' in inp.get('name', '').lower() for inp in form['inputs']):
                    form_purpose = "register a new account"
                elif any('search' in inp.get('name', '').lower() for inp in form['inputs']):
                    form_purpose = "search for content"
                
                story = {
                    'title': f"User can {form_purpose} on {page['title']}",
                    'description': f"As a user, I want to {form_purpose} so that I can interact with the application.",
                    'gherkin': self.generate_gherkin(form_purpose, page['url'])
                }
                stories.append(story)
        
        # Generate story for navigation
        if len(pages) > 1:
            story = {
                'title': "User can navigate between pages",
                'description': f"As a user, I want to navigate between {len(pages)} different pages so that I can access various features.",
                'gherkin': self.generate_gherkin("navigate between pages", self.base_url)
            }
            stories.append(story)
        
        return stories
    
    def generate_gherkin(self, action: str, url: str) -> str:
        """Generate Gherkin format story"""
        # Make action more specific for better test scenarios
        verb = "perform the action"
        expected = "see the result"
        
        if "log in" in action.lower() or "login" in action.lower():
            verb = "enter my credentials and submit"
            expected = "be logged into my account"
        elif "register" in action.lower() or "sign up" in action.lower():
            verb = "fill in the registration form and submit"
            expected = "see a confirmation message"
        elif "search" in action.lower():
            verb = "enter my search query and submit"
            expected = "see relevant search results"
        elif "submit" in action.lower():
            verb = "fill in the form and submit"
            expected = "see a success confirmation"
        elif "navigate" in action.lower():
            verb = "click on navigation links"
            expected = "be taken to the correct page"
        
        return f"""Feature: {action.capitalize()}
  
  Scenario: User wants to {action}
    Given I am on the page "{url}"
    When I {verb}
    Then I should {expected}
    And the action completes successfully"""
