"use strict";

/**
 * Interfaz del acortador de enlaces.
 * - Valida la URL en el navegador antes de enviarla.
 * - Envía la URL al backend en EC2 con fetch() (POST /shorten).
 * - Muestra el enlace corto y permite copiarlo.
 * El UUID y el acceso a DynamoDB ocurren solo en el backend.
 */
(function () {
  const config = window.APP_CONFIG || {};
  const API_BASE_URL = String(config.API_BASE_URL || "").replace(/\/+$/, "");
  const TIMEOUT_MS = Number(config.REQUEST_TIMEOUT_MS) || 10000;
  const MAX_URL_LENGTH = Number(config.MAX_URL_LENGTH) || 2048;
  const DOMAIN_PATTERN = /^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*\.([a-z]{2,63}|xn--[a-z0-9-]{1,59})$/i;
  const IPV4_PATTERN = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/;

  const elements = {
    form: document.getElementById("shorten-form"),
    input: document.getElementById("original-url"),
    submit: document.getElementById("submit-button"),
    error: document.getElementById("url-error"),
    result: document.getElementById("result"),
    shortUrl: document.getElementById("short-url"),
    shortCode: document.getElementById("short-code"),
    originalResult: document.getElementById("original-result"),
    openLink: document.getElementById("open-link"),
    copyButton: document.getElementById("copy-button"),
    copyStatus: document.getElementById("copy-status"),
  };

  /** Devuelve un mensaje de error o null si la URL es válida. */
  function validateUrl(value) {
    if (!value) {
      return "Ingresa una URL para acortar.";
    }
    if (value.length > MAX_URL_LENGTH) {
      return "La URL supera el máximo de " + MAX_URL_LENGTH + " caracteres.";
    }
    if (/\s/.test(value)) {
      return "La URL no debe contener espacios.";
    }
    if (!/^https?:\/\//i.test(value)) {
      return "La URL debe comenzar con http:// o https://.";
    }

    let parsed;
    try {
      parsed = new URL(value);
    } catch (error) {
      return "El texto ingresado no es una URL válida.";
    }

    const host = parsed.hostname.replace(/^\[|\]$/g, "");
    const isValidHost =
      host === "localhost" || IPV4_PATTERN.test(host) || host.includes(":") || DOMAIN_PATTERN.test(host);
    if (!isValidHost) {
      return "La URL no tiene un dominio válido (ejemplo: https://www.ejemplo.com).";
    }
    if (parsed.username || parsed.password) {
      return "La URL no debe incluir usuario ni contraseña.";
    }
    if (isOwnShortLink(parsed)) {
      return "No se puede acortar un enlace que ya pertenece a este acortador.";
    }
    return null;
  }

  /** Evita bucles: la URL no puede apuntar al propio backend. */
  function isOwnShortLink(parsed) {
    try {
      return parsed.host === new URL(API_BASE_URL).host;
    } catch (error) {
      return false;
    }
  }

  function showError(message) {
    elements.error.textContent = message;
    elements.error.hidden = false;
    elements.input.setAttribute("aria-invalid", "true");
  }

  function clearError() {
    elements.error.textContent = "";
    elements.error.hidden = true;
    elements.input.removeAttribute("aria-invalid");
  }

  function setLoading(isLoading) {
    elements.submit.disabled = isLoading;
    elements.submit.textContent = isLoading ? "Acortando…" : "Acortar";
    elements.form.setAttribute("aria-busy", String(isLoading));
  }

  function renderResult(data) {
    elements.shortUrl.value = data.short_url;
    elements.shortCode.textContent = data.short_code;
    elements.originalResult.textContent = data.original_url;
    elements.openLink.href = data.short_url;
    elements.copyStatus.textContent = "";
    elements.result.hidden = false;
  }

  /** Lee el cuerpo de error del backend ({ detail }) sin romper si no es JSON. */
  async function readErrorDetail(response) {
    try {
      const body = await response.json();
      if (body && typeof body.detail === "string") {
        return body.detail;
      }
    } catch (error) {
      // Respuesta sin JSON: se usa el mensaje genérico.
    }
    if (response.status >= 500) {
      return "El servidor tuvo un problema al procesar la solicitud. Intenta de nuevo.";
    }
    return "No se pudo acortar la URL (código " + response.status + ").";
  }

  async function requestShortUrl(originalUrl) {
    const controller = new AbortController();
    const timer = setTimeout(function () {
      controller.abort();
    }, TIMEOUT_MS);

    try {
      const response = await fetch(API_BASE_URL + "/shorten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ original_url: originalUrl }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(await readErrorDetail(response));
      }

      const data = await response.json();
      if (!data || !data.short_url || !data.short_code) {
        throw new Error("La respuesta del servidor no tiene el formato esperado.");
      }
      return data;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new Error("El servidor no respondió a tiempo. Intenta de nuevo en unos segundos.");
      }
      if (error instanceof TypeError) {
        // fetch lanza TypeError cuando no hay conexión, el backend está caído o CORS lo bloquea.
        throw new Error("No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.");
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    clearError();

    const originalUrl = elements.input.value.trim();
    const validationError = validateUrl(originalUrl);
    if (validationError) {
      showError(validationError);
      elements.input.focus();
      return;
    }

    setLoading(true);
    try {
      const data = await requestShortUrl(originalUrl);
      renderResult(data);
      elements.shortUrl.focus();
    } catch (error) {
      elements.result.hidden = true;
      showError(error.message);
    } finally {
      setLoading(false);
    }
  }

  /** Copia con la API del portapapeles; si no está disponible (HTTP), usa la selección. */
  async function copyShortUrl() {
    const text = elements.shortUrl.value;
    let copied = false;

    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        copied = true;
      } catch (error) {
        copied = false;
      }
    }

    if (!copied) {
      elements.shortUrl.focus();
      elements.shortUrl.select();
      try {
        copied = document.execCommand("copy");
      } catch (error) {
        copied = false;
      }
    }

    elements.copyStatus.textContent = copied
      ? "¡Enlace copiado al portapapeles!"
      : "No se pudo copiar automáticamente. Selecciona el enlace y presiona Ctrl+C.";
  }

  elements.form.addEventListener("submit", handleSubmit);
  elements.input.addEventListener("input", clearError);
  elements.copyButton.addEventListener("click", copyShortUrl);
})();
