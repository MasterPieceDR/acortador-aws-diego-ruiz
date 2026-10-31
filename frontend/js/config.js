// Configuración de la interfaz web.
// Antes de subir a S3, cambiar API_BASE_URL por la URL pública del backend en EC2,
// por ejemplo: "http://<ip-publica-ec2>:8000" (sin barra final).
window.APP_CONFIG = Object.freeze({
  API_BASE_URL: "http://localhost:8000",
  REQUEST_TIMEOUT_MS: 10000,
  MAX_URL_LENGTH: 2048,
});
