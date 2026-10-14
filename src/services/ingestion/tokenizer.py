from transformers import AutoTokenizer

class Tokenizer:
    def __init__(self, model_name = "BAAI/bge-large-en-v1.5"):
        self._tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self._tokenizer.model_max_length = int(1e9)

    def encode(self, text) -> list[int]:
        return self._tokenizer.encode(text, add_special_tokens=False)

    def decode(self, token_ids: list[int]) -> str:
        return self._tokenizer.decode(token_ids, skip_special_tokens=True).strip()

    def count_tokens(self, text: str) -> int:
        return len(self.encode(text))
