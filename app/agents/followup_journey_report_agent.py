from typing import Dict, List, Any
import logging
import json
from .base_agent import BaseAgent
from app.llm.prompts import PromptLibrary

logger = logging.getLogger(__name__)

class FollowupJourneyReportAgent(BaseAgent):
    """AI agent for analyzing visitor follow-up journeys"""
    
    def __init__(self, agent_id: str, schema: str):
        super().__init__(agent_id, schema)
        self.prompts = PromptLibrary()
        self.temperature = 0.2  # Lower temperature for consistent analysis
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visitor journey data for analysis"""
        if "visitor_data" in data:
            return {"analyzed_entries": await self.analyze_journey_entries(data["visitor_data"])}
        return {"error": "No visitor_data provided"}
    
    async def analyze_journey_entries(self, visitor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze each visitor's journey with AI insights"""
        analyzed_entries = []
        
        for visitor in visitor_data:
            try:
                # Generate AI analysis for this visitor's journey
                analysis = await self._analyze_single_journey(visitor)
                
                # Merge analysis with visitor data
                enriched_entry = {**visitor, **analysis}
                analyzed_entries.append(enriched_entry)
                
            except Exception as e:
                logger.error(f"Failed to analyze journey for visitor {visitor.get('visitor_id')}: {str(e)}")
                # Add fallback analysis
                analyzed_entries.append({
                    **visitor,
                    "visitor_decision": "Analysis unavailable",
                    "decision_rationale": "AI analysis failed",
                    "ai_recommendations": ["Manual review recommended"],
                    "unresolved_needs": []
                })
        
        return analyzed_entries
    
    async def _analyze_single_journey(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI analysis for a single visitor's journey"""
        # Construct prompt with visitor journey data
        prompt = self.prompts.get_journey_analysis_prompt(
            visitor_profile=visitor_data.get("profile", {}),
            follow_up_tasks=visitor_data.get("tasks", []),
            notes=visitor_data.get("notes", []),
            interactions=visitor_data.get("interactions", [])
        )
        
        # Generate AI analysis using inherited method
        response = await self.generate_llm_content(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=800
        )
        
        # Parse and structure the response
        return self._parse_journey_analysis(response)
    
    def _parse_journey_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured journey analysis"""
        try:
            # Try to parse JSON response
            analysis = json.loads(response.strip())
            
            # Validate required fields and provide defaults
            return {
                "visitor_decision": analysis.get("visitor_decision", "undecided"),
                "decision_rationale": analysis.get("decision_rationale", "No rationale provided"),
                "unresolved_needs": analysis.get("unresolved_needs", []),
                "ai_recommendations": analysis.get("ai_recommendations", []),
                "sentiment_analysis": analysis.get("sentiment_analysis", "neutral"),
                "engagement_level": analysis.get("engagement_level", "medium")
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.debug(f"Raw response: {response}")
            
            # Fallback parsing for non-JSON responses
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails"""
        # Simple keyword-based parsing
        decision = "undecided"
        if "joined" in response.lower():
            decision = "joined"
        elif "not interested" in response.lower():
            decision = "not_interested"
        
        sentiment = "neutral"
        if any(word in response.lower() for word in ["positive", "good", "excellent", "great"]):
            sentiment = "positive"
        elif any(word in response.lower() for word in ["negative", "poor", "bad", "disappointed"]):
            sentiment = "negative"
        
        return {
            "visitor_decision": decision,
            "decision_rationale": "Parsed from unstructured response",
            "unresolved_needs": [],
            "ai_recommendations": ["Manual review recommended due to parsing issues"],
            "sentiment_analysis": sentiment,
            "engagement_level": "medium"
        }