"""labllm — the lab's model client. See README.md or `labllm --help`."""
from .client import DEFAULT, LabLLM, Result, chat, default_chat_prompt, embed, load_prompt, resolve_model
from .scan import Finding, IdentifierError, read_text_file, scan_text

__all__ = ["DEFAULT", "LabLLM", "Result", "chat", "default_chat_prompt", "embed", "load_prompt",
           "resolve_model", "Finding", "IdentifierError", "read_text_file", "scan_text"]
__version__ = "0.2.0"
