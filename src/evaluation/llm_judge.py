"""
LLM-as-Judge evaluation system for B2B Account Intelligence Agent.

Uses Claude to evaluate answer quality on 4 dimensions:
- Tool Selection (25 pts)
- Tool Execution (25 pts)
- Reasoning Quality (25 pts)
- Answer Quality (25 pts)
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import anthropic
import json

@dataclass
class DimensionScore:
    """Score for a single evaluation dimension."""
    dimension: str
    score: float  # 0-25
    max_score: float = 25.0
    reasoning: str = ""

@dataclass
class JudgeResult:
    """Complete evaluation result from LLM judge."""
    question: str
    answer: str
    total_score: float  # 0-100
    dimension_scores: List[DimensionScore] = field(default_factory=list)
    passed: bool = False
    pass_threshold: float = 60.0
    tools_used: List[str] = field(default_factory=list)
    expected_tools: List[str] = field(default_factory=list)
    evaluation_criteria: str = ""
    raw_judge_response: str = ""

class LLMJudge:
    """LLM-based evaluator using Claude for answer quality assessment."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic()
        self.model = model

    def evaluate(
        self,
        question: str,
        answer: str,
        tools_used: List[str],
        expected_tools: List[str],
        evaluation_criteria: str,
        tool_traces: Optional[List[Dict[str, Any]]] = None,
        pass_threshold: float = 60.0
    ) -> JudgeResult:
        """
        Evaluate an answer using Claude as judge.

        Args:
            question: The original question
            answer: The agent's answer
            tools_used: List of tools the agent used
            expected_tools: List of tools expected for this question
            evaluation_criteria: Specific criteria for evaluation
            tool_traces: Optional detailed tool execution traces
            pass_threshold: Minimum score to pass (default 60)

        Returns:
            JudgeResult with scores and reasoning
        """
        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(
            question, answer, tools_used, expected_tools,
            evaluation_criteria, tool_traces
        )

        # Call Claude for evaluation
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw_response = response.content[0].text

        # Parse the response
        return self._parse_judge_response(
            raw_response, question, answer, tools_used,
            expected_tools, evaluation_criteria, pass_threshold
        )

    def _build_evaluation_prompt(
        self,
        question: str,
        answer: str,
        tools_used: List[str],
        expected_tools: List[str],
        evaluation_criteria: str,
        tool_traces: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the evaluation prompt for Claude."""

        traces_section = ""
        if tool_traces:
            traces_section = f"""
## Tool Execution Traces
{json.dumps(tool_traces, indent=2)}
"""

        return f'''You are an expert evaluator for a B2B Account Intelligence Agent.
Evaluate the following agent response on 4 dimensions, each worth 25 points (100 total).

## Question
{question}

## Agent's Answer
{answer}

## Tools Used by Agent
{', '.join(tools_used) if tools_used else 'None'}

## Expected Tools for This Question
{', '.join(expected_tools)}

## Evaluation Criteria
{evaluation_criteria}
{traces_section}

## Scoring Rubric

### 1. Tool Selection (0-25 points)
- Did the agent choose appropriate tools for this query type?
- Did it avoid using unnecessary tools?
- Award 20-25 for optimal tool selection
- Award 10-19 for acceptable but suboptimal selection
- Award 0-9 for poor or wrong tool selection

### 2. Tool Execution (0-25 points)
- Were the tool parameters specific and appropriate?
- Was the tool result used correctly?
- Award 20-25 for excellent execution
- Award 10-19 for adequate execution
- Award 0-9 for poor execution

### 3. Reasoning Quality (0-25 points)
- Did the agent explain its tool choices?
- Is there a logical flow from tool results to the answer?
- Award 20-25 for clear, well-explained reasoning
- Award 10-19 for adequate reasoning
- Award 0-9 for unclear or missing reasoning

### 4. Answer Quality (0-25 points)
- Is the answer factually correct per the evaluation criteria?
- Is it well-structured and appropriately detailed?
- Award 20-25 for accurate, well-structured answer
- Award 10-19 for mostly correct answer
- Award 0-9 for incorrect or poorly structured answer

## Response Format
Respond with a JSON object containing your evaluation:

```json
{{
  "tool_selection": {{
    "score": <0-25>,
    "reasoning": "<explanation>"
  }},
  "tool_execution": {{
    "score": <0-25>,
    "reasoning": "<explanation>"
  }},
  "reasoning_quality": {{
    "score": <0-25>,
    "reasoning": "<explanation>"
  }},
  "answer_quality": {{
    "score": <0-25>,
    "reasoning": "<explanation>"
  }},
  "total_score": <0-100>,
  "overall_assessment": "<brief summary>"
}}
```

Evaluate fairly and provide specific reasoning for each score.'''

    def _parse_judge_response(
        self,
        raw_response: str,
        question: str,
        answer: str,
        tools_used: List[str],
        expected_tools: List[str],
        evaluation_criteria: str,
        pass_threshold: float
    ) -> JudgeResult:
        """Parse Claude's evaluation response into JudgeResult."""

        # Extract JSON from response
        try:
            # Find JSON block in response
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError:
            # Fallback: create default scores
            data = {
                "tool_selection": {"score": 15, "reasoning": "Unable to parse evaluation"},
                "tool_execution": {"score": 15, "reasoning": "Unable to parse evaluation"},
                "reasoning_quality": {"score": 15, "reasoning": "Unable to parse evaluation"},
                "answer_quality": {"score": 15, "reasoning": "Unable to parse evaluation"},
                "total_score": 60
            }

        # Build dimension scores
        dimension_scores = [
            DimensionScore(
                dimension="tool_selection",
                score=data.get("tool_selection", {}).get("score", 0),
                reasoning=data.get("tool_selection", {}).get("reasoning", "")
            ),
            DimensionScore(
                dimension="tool_execution",
                score=data.get("tool_execution", {}).get("score", 0),
                reasoning=data.get("tool_execution", {}).get("reasoning", "")
            ),
            DimensionScore(
                dimension="reasoning_quality",
                score=data.get("reasoning_quality", {}).get("score", 0),
                reasoning=data.get("reasoning_quality", {}).get("reasoning", "")
            ),
            DimensionScore(
                dimension="answer_quality",
                score=data.get("answer_quality", {}).get("score", 0),
                reasoning=data.get("answer_quality", {}).get("reasoning", "")
            )
        ]

        total_score = sum(d.score for d in dimension_scores)

        return JudgeResult(
            question=question,
            answer=answer,
            total_score=total_score,
            dimension_scores=dimension_scores,
            passed=total_score >= pass_threshold,
            pass_threshold=pass_threshold,
            tools_used=tools_used,
            expected_tools=expected_tools,
            evaluation_criteria=evaluation_criteria,
            raw_judge_response=raw_response
        )

    def evaluate_batch(
        self,
        evaluations: List[Dict[str, Any]],
        pass_threshold: float = 60.0
    ) -> List[JudgeResult]:
        """
        Evaluate multiple answers.

        Args:
            evaluations: List of dicts with keys:
                - question, answer, tools_used, expected_tools, evaluation_criteria
            pass_threshold: Minimum score to pass

        Returns:
            List of JudgeResult objects
        """
        results = []
        for eval_data in evaluations:
            result = self.evaluate(
                question=eval_data["question"],
                answer=eval_data["answer"],
                tools_used=eval_data.get("tools_used", []),
                expected_tools=eval_data.get("expected_tools", []),
                evaluation_criteria=eval_data.get("evaluation_criteria", ""),
                tool_traces=eval_data.get("tool_traces"),
                pass_threshold=pass_threshold
            )
            results.append(result)
        return results


def calculate_judge_metrics(results: List[JudgeResult]) -> Dict[str, Any]:
    """
    Calculate aggregate metrics from judge results.

    Returns:
        Dict with aggregate metrics
    """
    if not results:
        return {"error": "No results to evaluate"}

    total_scores = [r.total_score for r in results]
    pass_count = sum(1 for r in results if r.passed)

    # Dimension averages
    dimension_avgs = {}
    for dim in ["tool_selection", "tool_execution", "reasoning_quality", "answer_quality"]:
        scores = [
            d.score for r in results
            for d in r.dimension_scores
            if d.dimension == dim
        ]
        dimension_avgs[dim] = sum(scores) / len(scores) if scores else 0

    return {
        "total_evaluated": len(results),
        "pass_count": pass_count,
        "pass_rate": pass_count / len(results),
        "avg_total_score": sum(total_scores) / len(total_scores),
        "min_score": min(total_scores),
        "max_score": max(total_scores),
        "dimension_averages": dimension_avgs,
        "score_distribution": {
            "excellent_90_100": sum(1 for s in total_scores if s >= 90),
            "good_75_89": sum(1 for s in total_scores if 75 <= s < 90),
            "acceptable_60_74": sum(1 for s in total_scores if 60 <= s < 75),
            "failing_below_60": sum(1 for s in total_scores if s < 60)
        }
    }
