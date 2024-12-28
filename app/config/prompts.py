"""Prompt templates for various AI tasks."""

RELEVANCY_CHECK_PROMPT = """Analyze if the response is both relevant to the query and supported by at least some of the given contexts.
Do not explain, just output a single word: 'yes' or 'no'.

Query: {query}

Contexts:
{contexts}

Response to check:
{response}

Is the response both relevant AND fully supported by the contexts (yes/no)?"""


REGENERATION_PROMPT = """Your previous response was found to be {issue_type}. 
Please provide a new response that is strictly based on the given contexts.
If the contexts don't contain relevant information, explicitly say so.

Contexts:
{contexts}

Query: {query}

Requirements:
1. Only use information explicitly stated in the contexts
2. If information is not in contexts, say "I cannot find relevant information about [specific aspect]"
3. Be clear about what information is and isn't available"""
