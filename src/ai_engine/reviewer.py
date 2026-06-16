"""
AI Code Reviewer — wraps OpenAI / Anthropic with a rule-based fallback.
"""
from __future__ import annotations
import os
import re
from typing import Dict, List, Optional
from loguru import logger


class CodeReviewer:
    """
    Review code diffs with OpenAI GPT or Anthropic Claude.
    Falls back to pattern-based analysis when no API key is configured.

    Usage::

        reviewer = CodeReviewer()
        result = await reviewer.review(diff="...", pr_number=42)
    """

    RULE_PATTERNS = [
        (r"password\s*=\s*['\"][^'\"]+['\"]",  "Possible hardcoded password detected",        "security"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]",    "Possible hardcoded secret detected",           "security"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]",   "API key hardcoded in source",                  "security"),
        (r"except\s*:",                         "Bare except clause — catch specific exceptions","suggestion"),
        (r"except\s+Exception\s*:",             "Overly broad exception catch",                 "suggestion"),
        (r"TODO|FIXME|HACK|XXX",               "Unresolved TODO/FIXME comment",                "suggestion"),
        (r"print\s*\(",                         "Use logging instead of print()",               "suggestion"),
        (r"time\.sleep\(",                      "Blocking sleep — consider asyncio.sleep()",    "performance"),
        (r"SELECT \*",                          "Avoid SELECT * — specify column names",        "performance"),
    ]

    def __init__(self, provider: str = "auto"):
        self.provider = provider
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    async def review(self, diff: str, pr_number: int = 0) -> Dict:
        """
        Review a code diff.

        Returns a dict with: suggestions, security_issues, performance_tips, score, model_used
        """
        if self._openai_key and self.provider in ("auto", "openai"):
            return await self._openai_review(diff, pr_number)
        if self._anthropic_key and self.provider in ("auto", "anthropic"):
            return await self._anthropic_review(diff, pr_number)
        return self._rule_based_review(diff, pr_number)

    # ── Providers ────────────────────────────────────────────────────────────

    async def _openai_review(self, diff: str, pr_number: int) -> Dict:
        try:
            from openai import AsyncOpenAI
            import json as _json
            client = AsyncOpenAI(api_key=self._openai_key)
            prompt = self._build_prompt(diff)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            parsed = _json.loads(resp.choices[0].message.content)
            return self._format(parsed, pr_number, model="gpt-4o-mini")
        except Exception as exc:
            logger.warning(f"OpenAI review failed: {exc}; using rule-based fallback")
            return self._rule_based_review(diff, pr_number)

    async def _anthropic_review(self, diff: str, pr_number: int) -> Dict:
        try:
            import anthropic as _ant
            import json as _json
            client = _ant.Anthropic(api_key=self._anthropic_key)
            msg = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                messages=[{"role": "user", "content": self._build_prompt(diff)}],
            )
            parsed = _json.loads(msg.content[0].text)
            return self._format(parsed, pr_number, model="claude-3-haiku")
        except Exception as exc:
            logger.warning(f"Anthropic review failed: {exc}; using rule-based fallback")
            return self._rule_based_review(diff, pr_number)

    def _rule_based_review(self, diff: str, pr_number: int) -> Dict:
        suggestions: List[str] = []
        security: List[str] = []
        performance: List[str] = []

        for pattern, message, category in self.RULE_PATTERNS:
            if re.search(pattern, diff, re.IGNORECASE):
                if category == "security":
                    security.append(message)
                elif category == "performance":
                    performance.append(message)
                else:
                    suggestions.append(message)

        if not suggestions and not security:
            suggestions.append("Add docstrings to all public functions")
            suggestions.append("Ensure unit tests cover the changed logic")

        return self._format(
            {"suggestions": suggestions, "security_issues": security, "performance_tips": performance},
            pr_number,
            model="rule-based",
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(diff: str) -> str:
        return (
            "You are a senior code reviewer. Review the following diff.\n"
            "Return ONLY a JSON object with keys:\n"
            "  suggestions: list[str]  (max 3 improvement suggestions)\n"
            "  security_issues: list[str]  (any security concerns)\n"
            "  performance_tips: list[str]  (performance improvements)\n\n"
            f"DIFF (truncated to 3000 chars):\n{diff[:3000]}"
        )

    @staticmethod
    def _format(parsed: Dict, pr_number: int, model: str) -> Dict:
        suggestions = parsed.get("suggestions", [])
        security = parsed.get("security_issues", [])
        performance = parsed.get("performance_tips", [])
        score = max(40, 100 - len(security) * 20 - len(suggestions) * 5)
        return {
            "pr_number": pr_number,
            "status": "completed",
            "model_used": model,
            "score": score,
            "issues_found": len(suggestions) + len(security),
            "suggestions": suggestions,
            "security_issues": security,
            "performance_tips": performance,
        }
