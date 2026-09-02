from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

VAULT_URL = "https://kv-topdeck.vault.azure.net"

def fetch_secret(name: str) -> str:
    client = SecretClient(VAULT_URL, DefaultAzureCredential())
    return client.get_secret(name).value
