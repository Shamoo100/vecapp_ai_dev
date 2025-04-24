from typing import Dict, Any, Optional
from uuid import UUID
import langsmith
from langsmith.schemas import Run
from langsmith.evaluation import RunEvaluator
from app.config.settings import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class ReportEvaluator:
    """Evaluates report quality using LangSmith"""
    
    def __init__(self):
        self.client = langsmith.Client(
            api_key=settings.LANGSMITH_API_KEY,
            project_name=settings.LANGSMITH_PROJECT
        )
    
    def evaluate_report(self, report_data: Dict[str, Any], tenant_id: UUID) -> Dict[str, Any]:
        """Evaluate the quality of a generated report"""
        try:
            # Define custom evaluators
            evaluators = [
                self._create_completeness_evaluator(),
                self._create_consistency_evaluator(),
                self._create_bias_evaluator()
            ]
            
            # Get the run from LangSmith
            run_id = report_data.get("metadata", {}).get("run_id")
            if not run_id:
                logger.warning(f"No run_id found in report metadata for tenant {tenant_id}")
                return {"success": False, "error": "No run_id found in report metadata"}
            
            # Get the run
            run = self.client.get_run(run_id)
            
            # Run evaluations
            evaluation_results = {}
            for evaluator in evaluators:
                result = evaluator.evaluate_run(run)
                evaluation_results[evaluator.name] = result
            
            # Log the evaluation results
            self.client.create_feedback(
                run_id=run_id,
                key="report_evaluation",
                feedback_type="score",
                score=sum(r.get("score", 0) for r in evaluation_results.values()) / len(evaluators),
                comment=f"Report evaluation for tenant {tenant_id}",
                value=evaluation_results
            )
            
            return {
                "success": True,
                "results": evaluation_results,
                "run_id": run_id
            }
        except Exception as e:
            logger.error(f"Error evaluating report: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_completeness_evaluator(self) -> RunEvaluator:
        """Create an evaluator to check report completeness"""
        def evaluate_completeness(run: Run) -> Dict[str, Any]:
            # Check if all required sections are present
            required_sections = [
                "visitor_summary", 
                "engagement_breakdown", 
                "outcome_trends", 
                "individual_summaries", 
                "recommendations"
            ]
            
            output = run.outputs["output"] if isinstance(run.outputs, dict) else run.outputs
            
            # Check each section
            missing_sections = []
            for section in required_sections:
                if section not in output:
                    missing_sections.append(section)
            
            score = 1.0 if not missing_sections else max(0, 1 - len(missing_sections) / len(required_sections))
            
            return {
                "score": score,
                "missing_sections": missing_sections,
                "comment": "Completeness evaluation" if score == 1.0 else f"Missing sections: {', '.join(missing_sections)}"
            }
        
        return RunEvaluator(evaluate_completeness, name="completeness")
    
    def _create_consistency_evaluator(self) -> RunEvaluator:
        """Create an evaluator to check report consistency"""
        def evaluate_consistency(run: Run) -> Dict[str, Any]:
            # Check if metrics are consistent across sections
            output = run.outputs["output"] if isinstance(run.outputs, dict) else run.outputs
            
            # Simplified consistency check - in real implementation, would be more robust
            inconsistencies = []
            
            # Example check: visitor count in summary matches total count of individual summaries
            if "visitor_summary" in output and "individual_summaries" in output:
                visitor_count = output["visitor_summary"].get("total_visitors", 0)
                individual_count = len(output["individual_summaries"])
                
                if visitor_count != individual_count:
                    inconsistencies.append(
                        f"Visitor count mismatch: {visitor_count} in summary vs {individual_count} individuals"
                    )
            
            score = 1.0 if not inconsistencies else max(0, 1 - 0.2 * len(inconsistencies))
            
            return {
                "score": score,
                "inconsistencies": inconsistencies,
                "comment": "Consistency evaluation" if score == 1.0 else f"Found inconsistencies: {', '.join(inconsistencies)}"
            }
        
        return RunEvaluator(evaluate_consistency, name="consistency")
    
    def _create_bias_evaluator(self) -> RunEvaluator:
        """Create an evaluator to check for bias in the report"""
        def evaluate_bias(run: Run) -> Dict[str, Any]:
            # Check for potential bias in the report
            output = run.outputs["output"] if isinstance(run.outputs, dict) else run.outputs
            
            # Simplified bias detection - in real implementation, would use more sophisticated NLP
            bias_indicators = []
            
            # Look for bias in recommendations
            if "recommendations" in output:
                for recommendation in output["recommendations"]:
                    rec_text = recommendation.get("recommendation", "")
                    rationale = recommendation.get("rationale", "")
                    
                    # Simple keyword check (would be more sophisticated in reality)
                    bias_keywords = ["always", "never", "all", "none", "every", "only"]
                    for keyword in bias_keywords:
                        if keyword in rec_text.lower() or keyword in rationale.lower():
                            bias_indicators.append(
                                f"Potential absolutist language in recommendation: '{keyword}'"
                            )
            
            score = 1.0 if not bias_indicators else max(0, 1 - 0.1 * len(bias_indicators))
            
            return {
                "score": score,
                "bias_indicators": bias_indicators,
                "comment": "Bias evaluation" if score == 1.0 else f"Potential bias detected: {', '.join(bias_indicators)}"
            }
        
        return RunEvaluator(evaluate_bias, name="bias") 