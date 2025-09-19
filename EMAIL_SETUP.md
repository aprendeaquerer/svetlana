# Configuración de Email para Eldric

## Variables de Entorno Requeridas

Para habilitar el envío de emails, configura las siguientes variables de entorno:

```bash
# Configuración de Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password
FROM_EMAIL=noreply@eldric.com
FROM_NAME=Eldric - Tu Coach Emocional
```

## Configuración para Gmail

### 1. Habilitar Autenticación de 2 Factores
- Ve a tu cuenta de Google
- Seguridad → Verificación en 2 pasos
- Actívala si no está activada

### 2. Generar Contraseña de Aplicación
- Ve a Seguridad → Contraseñas de aplicaciones
- Selecciona "Correo" y "Otro (nombre personalizado)"
- Escribe "Eldric" como nombre
- Copia la contraseña generada (16 caracteres)

### 3. Configurar Variables de Entorno
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@gmail.com
SMTP_PASSWORD=la_contraseña_de_16_caracteres
FROM_EMAIL=tu_email@gmail.com
FROM_NAME=Eldric - Tu Coach Emocional
```

## Configuración para Zoho Mail

### 1. Configuración Básica
```bash
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@tudominio.com
SMTP_PASSWORD=tu_contraseña_normal
FROM_EMAIL=tu_email@tudominio.com
FROM_NAME=Eldric - Tu Coach Emocional
```

### 2. Si tienes Autenticación de 2 Factores (Recomendado)
- Ve a tu panel de Zoho Mail
- Configuración → Seguridad → Contraseñas de aplicación
- Genera una nueva contraseña para "Eldric"
- Usa esa contraseña como `SMTP_PASSWORD`

### 3. Configuración Alternativa (Puerto 465 con SSL)
Si el puerto 587 no funciona, prueba con:
```bash
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=465
SMTP_USERNAME=tu_email@tudominio.com
SMTP_PASSWORD=tu_contraseña
FROM_EMAIL=tu_email@tudominio.com
FROM_NAME=Eldric - Tu Coach Emocional
```

**Nota:** Para el puerto 465, necesitarás modificar el código para usar SSL en lugar de STARTTLS.

## Configuración para Otros Proveedores

### Zoho Mail
```bash
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@tudominio.com
SMTP_PASSWORD=tu_contraseña
FROM_EMAIL=tu_email@tudominio.com
FROM_NAME=Eldric - Tu Coach Emocional
```

**Nota para Zoho:**
- Si usas autenticación de 2 factores, necesitarás generar una contraseña de aplicación
- Ve a Configuración → Seguridad → Contraseñas de aplicación
- Genera una nueva contraseña para "Eldric"

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@outlook.com
SMTP_PASSWORD=tu_contraseña
```

### Yahoo
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@yahoo.com
SMTP_PASSWORD=tu_contraseña
```

## Funcionalidades de Email

### 1. Códigos de Verificación
- Se envían automáticamente al registrarse
- Código de 6 dígitos
- Expira en 15 minutos
- Diseño HTML profesional

### 2. Reportes PDF
- Solo para usuarios con email verificado
- Incluye análisis completo de tests
- Personalizado con nombre del usuario
- Adjunto PDF del reporte

### 3. Seguridad
- Verificación gradual (básico sin verificar, avanzado con verificar)
- Códigos con expiración
- Validación de formato de email
- Prevención de spam

## Testing

Para probar sin configurar email real:
- No configures las variables SMTP_USERNAME y SMTP_PASSWORD
- Los códigos se mostrarán en los logs del servidor
- Los PDFs se simularán como enviados

## Troubleshooting

### Error: "Authentication failed"
- Verifica que la contraseña de aplicación sea correcta
- Asegúrate de que la autenticación de 2 factores esté activada

### Error: "Connection refused"
- Verifica el SMTP_SERVER y SMTP_PORT
- Asegúrate de que el firewall permita conexiones SMTP

### Error: "Email not sent"
- Revisa los logs del servidor para más detalles
- Verifica que el email de destino sea válido
