from typing import List, Dict
import json
from ..utils.anthropic_client import AnthropicClient
from ..utils.logger import get_logger

logger = get_logger(__name__)

class NewsProcessor:
    def __init__(self, anthropic_client: AnthropicClient):
        self.client = anthropic_client
        self.host_personalities = {
            "anchor": {
                "name": "Professional News Anchor",
                "style": "Professional, authoritative, and trustworthy",
                "tone": "Clear, measured, and objective",
                "instructions": """You are a professional news anchor delivering the news with authority and clarity. 
                Your delivery should be:
                - Concise and to the point
                - Objective and balanced
                - Professional but approachable
                - Using broadcast-style language
                - Including relevant context
                - Maintaining journalistic integrity"""
            },
            "friend": {
                "name": "Friendly Neighbor",
                "style": "Warm, conversational, and relatable",
                "tone": "Casual, friendly, and engaging",
                "instructions": """You are everyone's friendly neighbor sharing local news over the fence. 
                Your delivery should be:
                - Conversational and warm
                - Using everyday language
                - Adding personal touches and local relevance
                - Showing genuine interest and concern
                - Making complex topics accessible
                - Including "did you hear?" style introductions"""
            },
            "newsreel": {
                "name": "1940s Newsreel Announcer",
                "style": "Dramatic, theatrical, and vintage",
                "tone": "Bold, emphatic, and larger-than-life",
                "instructions": """You are a 1940s newsreel announcer with a dramatic flair. 
                Your delivery should be:
                - Theatrical and bombastic
                - Using vintage expressions and terminology
                - Adding dramatic emphasis and exclamations
                - Speaking in a rapid-fire, energetic style
                - Including phrases like "This just in!" and "Extraordinary developments!"
                - Making everything sound momentous and historic"""
            }
        }
    
    async def process_articles(
        self, 
        articles: List[Dict], 
        host_type: str,
        province: str = None
    ) -> List[Dict]:
        """Process articles with AI host personality"""
        if host_type not in self.host_personalities:
            raise ValueError(f"Unknown host type: {host_type}")
        
        personality = self.host_personalities[host_type]
        processed_articles = []
        
        for article in articles:
            try:
                processed_content = await self._process_single_article(
                    article, 
                    personality,
                    province
                )
                
                processed_articles.append({
                    'title': article['title'],
                    'url': article.get('link', article.get('url', '')),
                    'source': article.get('source_name', ''),
                    'content': processed_content,
                    'wtkr_id': article.get('wtkr_id', ''),
                    'original_content': article.get('content', article.get('summary', ''))
                })
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('title', 'Unknown')}: {str(e)}")
                # Include original content as fallback
                processed_articles.append({
                    'title': article['title'],
                    'url': article.get('link', article.get('url', '')),
                    'source': article.get('source_name', ''),
                    'content': article.get('content', article.get('summary', '')),
                    'wtkr_id': article.get('wtkr_id', ''),
                    'original_content': article.get('content', article.get('summary', ''))
                })
        
        return processed_articles
    
    async def _process_single_article(
        self, 
        article: Dict, 
        personality: Dict,
        province: str = None
    ) -> str:
        """Process a single article with host personality"""
        
        system_prompt = f"""You are a {personality['name']} for a local news broadcast.
        Style: {personality['style']}
        Tone: {personality['tone']}
        
        {personality['instructions']}
        
        Important guidelines:
        1. Rewrite the news content in your unique style
        2. Keep all factual information accurate
        3. Maintain appropriate length (30-60 seconds when read aloud)
        4. Make it engaging for radio/podcast listeners
        5. Include the source attribution naturally
        {f"6. Add local relevance for {province} when appropriate" if province else ""}
        """
        
        user_prompt = f"""Please rewrite this news article for your broadcast:

        Title: {article['title']}
        Source: {article.get('source_name', 'Local News')}
        
        Content:
        {article.get('content', article.get('summary', ''))}
        
        Remember to:
        - Start with an attention-grabbing introduction
        - Present the key facts clearly
        - Include source attribution
        - End with a natural transition or closing
        """
        
        processed_content = await self.client.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return processed_content.strip()