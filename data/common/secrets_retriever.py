from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

VAULT_URL = "https://kv-topdeck.vault.azure.net"

def fetch_secret(name: str) -> str:
    client = SecretClient(VAULT_URL, DefaultAzureCredential())
    secret = client.get_secret(name).value
    if secret is None:
        raise ValueError(f"secret '{name}' exists but has no value")

    return secret
