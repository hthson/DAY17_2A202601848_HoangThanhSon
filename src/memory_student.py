from __future__ import annotations

import time
from typing import Any

from .config import settings
from .context_budget import ContextBudgetManager
from .utils import cap_query, join_nonempty
from .zep_common import prime_eval_thread, render_graph_search


def _retry_call(fn, *args, retries: int = 3, delay: float = 1.0, **kwargs) -> Any:
    """Retry transient connection errors when contacting Zep cloud."""
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if attempt == retries:
                raise
            time.sleep(delay * attempt)


class StudentMemory:
    """Only this file needs to be edited by students."""

    def __init__(self, client: Any):
        self.client = client
        self.budget = ContextBudgetManager(settings.context_tokens)

    def retrieve_long_term(self, user_id: str, thread_id: str, query: str) -> str:
        _retry_call(prime_eval_thread, self.client, user_id, thread_id, query)
        user_context = _retry_call(self.client.thread.get_user_context, thread_id=thread_id)
        context_block = getattr(user_context, "context", "") or ""

        try:
            facts = _retry_call(
                self.client.graph.search,
                user_id=user_id,
                query=cap_query(query),
                scope="edges",
                limit=20,
            )
            fact_text = render_graph_search(facts)
        except Exception:
            fact_text = ""
        return join_nonempty([context_block, fact_text], sep="\n\n")

    def retrieve_episodic(self, user_id: str, query: str) -> str:
        results = _retry_call(
            self.client.graph.search,
            user_id=user_id,
            query=cap_query(query),
            scope="episodes",
            limit=15,
        )
        return render_graph_search(results, episode_char_cap=180)

    def retrieve_semantic(self, graph_id: str, query: str) -> str:
        q = cap_query(query)
        try:
            results = _retry_call(
                self.client.graph.search,
                graph_id=graph_id,
                query=q,
                scope="episodes",
                limit=8,
            )
        except Exception:
            results = _retry_call(
                self.client.graph.search,
                graph_id=graph_id,
                query=q,
                scope="nodes",
                limit=8,
            )
        return render_graph_search(results)

    def assemble_context(self, layers: dict[str, str]) -> tuple[str, dict[str, dict[str, int]]]:
        return self.budget.assemble(layers)
