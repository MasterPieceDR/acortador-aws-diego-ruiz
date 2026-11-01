#!/usr/bin/env bash
# Despliegue del backend en EC2 (Amazon Linux 2023).
# Uso, dentro de la instancia por SSH:
#   curl -O https://raw.githubusercontent.com/MasterPieceDR/acortador-aws-diego-ruiz/main/deploy/setup_ec2.sh
#   bash setup_ec2.sh http://<bucket>.s3-website-us-east-1.amazonaws.com
set -euo pipefail

S3_ORIGIN="${1:?Pasa como argumento la URL del sitio en S3 (sin barra final)}"
REPO_URL="https://github.com/MasterPieceDR/acortador-aws-diego-ruiz.git"
APP_DIR="/home/ec2-user/acortador-aws-diego-ruiz"

# 1. Python 3.11 y Git (Amazon Linux 2023 trae 3.9 y FastAPI 0.162 requiere 3.10+)
sudo dnf install -y python3.11 python3.11-pip git

# 2. Clonar (o actualizar) el repositorio
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull
else
  git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR/backend"

# 3. Entorno virtual y dependencias (FastAPI, Uvicorn y Boto3)
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 4. Variables de entorno (sin access keys: se usa el rol IAM de la instancia)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)
cat > .env <<EOF
APP_NAME=Acortador de enlaces - Diego Ruiz
APP_ENV=production
AWS_REGION=us-east-1
DYNAMODB_TABLE=shortener-links-diego
DYNAMODB_ENDPOINT_URL=
PUBLIC_BASE_URL=http://${PUBLIC_IP}:8000
CORS_ORIGINS=${S3_ORIGIN}
MAX_URL_LENGTH=2048
EOF
echo "---- .env generado ----"; cat .env

# 5. Servicio systemd (sigue activo al cerrar SSH y tras reiniciar)
sudo cp "$APP_DIR/deploy/shortener.service" /etc/systemd/system/shortener.service
sudo systemctl daemon-reload
sudo systemctl enable --now shortener
sudo systemctl restart shortener
sleep 3
sudo systemctl --no-pager status shortener | head -n 12

echo
echo "API:  http://${PUBLIC_IP}:8000/docs"
echo "Pon esta URL en frontend/js/config.js -> API_BASE_URL: \"http://${PUBLIC_IP}:8000\""
