"""Provider-neutral AI gateway placeholder."""


class ModelGateway:
    def run(self, prompt_name: str, payload: dict[str, object]) -> dict[str, object]:
        return {"prompt_name": prompt_name, "payload": payload, "provider": "stub"}

