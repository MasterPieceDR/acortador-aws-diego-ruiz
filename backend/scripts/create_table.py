"""Crea la tabla de DynamoDB del acortador si todavía no existe.

Uso (desde la carpeta backend, con el entorno virtual activo):
    python scripts/create_table.py

- En local apunta a DynamoDB Local cuando DYNAMODB_ENDPOINT_URL está definido.
- En AWS (DYNAMODB_ENDPOINT_URL vacío) crea la tabla real con tus credenciales
  de AWS CLI. No se ejecuta en EC2: el rol IAM de la instancia solo permite
  PutItem y GetItem.
"""

import sys
from pathlib import Path

from botocore.exceptions import ClientError

# Los módulos viven en backend/src (igual que cuando se ejecuta "fastapi dev src/main.py").
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import get_settings  # noqa: E402
from database.dynamodb import get_dynamodb_resource  # noqa: E402


def create_table() -> None:
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    target = settings.dynamodb_endpoint_url or f"AWS ({settings.aws_region})"

    try:
        table = dynamodb.create_table(
            TableName=settings.dynamodb_table,
            KeySchema=[{"AttributeName": "short_code", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "short_code", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"Tabla '{settings.dynamodb_table}' creada en {target}.")
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ResourceInUseException":
            print(f"La tabla '{settings.dynamodb_table}' ya existe en {target}.")
        else:
            raise


if __name__ == "__main__":
    create_table()
