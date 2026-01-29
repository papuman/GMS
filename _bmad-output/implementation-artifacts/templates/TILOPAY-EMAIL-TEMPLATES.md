# TiloPay Payment Gateway - Email Templates

**Version:** 1.0
**Date:** 2025-12-28
**Purpose:** Ready-to-use email templates for TiloPay implementation

---

## Template 1: TiloPay Fee Negotiation Email

**To:** sac@tilopay.com
**Subject:** Solicitud de Tarifas Preferenciales - Gimnasio con 300 Miembros Activos

```
Estimado Equipo de TiloPay,

Me pongo en contacto con ustedes en representación de [NOMBRE DE SU GIMNASIO],
un gimnasio establecido en Costa Rica con 300 miembros activos.

Estamos interesados en integrar TiloPay como nuestra pasarela de pagos en línea
para procesar pagos de membresías y servicios. Nuestros números proyectados son:

VOLUMEN MENSUAL PROYECTADO:
- Total de transacciones: ~₡15,000,000 mensuales (₡180M anuales)
- 300 miembros activos pagando regularmente
- Mix esperado: 70% SINPE Móvil, 30% Tarjetas

Distribución estimada:
- SINPE Móvil: ₡10,500,000/mes
- Tarjetas: ₡4,500,000/mes

SOLICITUD DE TARIFAS PREFERENCIALES:

Entendemos que sus tarifas estándar son:
- SINPE Móvil: 1.5%
- Tarjetas: 3.9%

Dado nuestro volumen significativo y la naturaleza recurrente de nuestros pagos,
solicitamos las siguientes tarifas preferenciales:

TARIFAS OBJETIVO:
- SINPE Móvil: 1.0% - 1.25% (vs 1.5% estándar)
- Tarjetas: 3.5% (vs 3.9% estándar)

JUSTIFICACIÓN:
1. Alto volumen mensual garantizado (₡15M/mes)
2. Pagos recurrentes predecibles (membresías mensuales)
3. Bajo riesgo de chargebacks (modelo de suscripción)
4. Compromiso a largo plazo (contrato anual)
5. Potencial de crecimiento (expansión planificada)

INTEGRACIÓN:
- Plataforma: Odoo 19
- Módulo: Desarrollado internamente con integración a TiloPay API
- E-facturación: Sistema completo de facturación electrónica Costa Rica
- Timeline: Listos para comenzar integración inmediatamente

Estamos evaluando también otras opciones de pasarelas de pago, pero preferimos
trabajar con TiloPay debido a su excelente reputación en el mercado costarricense
y su soporte técnico.

¿Sería posible agendar una llamada para discutir estas tarifas preferenciales?

Quedo atento a su respuesta.

Saludos cordiales,

[SU NOMBRE]
[SU CARGO]
[NOMBRE DEL GIMNASIO]
[TELÉFONO]
[EMAIL]
```

---

## Template 2: Member Announcement - New Payment Feature

**Subject:** ¡Nueva Forma de Pagar! 💳 Pagos en Línea Ahora Disponibles

```
Estimado/a [NOMBRE_MIEMBRO],

¡Tenemos excelentes noticias! 🎉

A partir de hoy, puedes pagar tus membresías y servicios de [NOMBRE_GIMNASIO]
de forma rápida y segura en línea, directamente desde tu computadora o celular.

✨ ¿QUÉ HAY DE NUEVO?

Ahora puedes pagar usando:
• 📱 SINPE Móvil - ¡Pago instantáneo desde tu banco!
• 💳 Tarjeta de Crédito/Débito - Visa, Mastercard, American Express

⚡ VENTAJAS:

✅ Pago instantáneo 24/7 - Paga cuando quieras, donde estés
✅ Confirmación inmediata - Recibe tu factura electrónica al instante
✅ 100% seguro - Procesado por TiloPay, plataforma certificada
✅ Fácil y rápido - Solo 3 pasos, menos de 2 minutos

🚀 CÓMO PAGAR EN LÍNEA:

1. Ingresa a tu portal de miembros: [LINK_PORTAL]
2. Ve a "Mis Facturas"
3. Haz clic en "Pagar en Línea" en la factura que deseas pagar
4. Selecciona tu método de pago preferido (SINPE o Tarjeta)
5. ¡Listo! Recibirás tu factura electrónica por email

💡 CONSEJO: Si pagas con SINPE Móvil, la transacción es más rápida y tiene
    comisiones menores.

📧 TU FACTURA ELECTRÓNICA:

Después de cada pago recibirás automáticamente:
• Factura electrónica oficial (aprobada por Hacienda)
• Comprobante de pago
• Número de transacción para tus registros

🤔 ¿PREGUNTAS?

• Video tutorial: [LINK_A_VIDEO]
• Preguntas frecuentes: [LINK_A_FAQ]
• Contacto: [TELEFONO] | [EMAIL]

¡Estamos aquí para ayudarte! Si tienes alguna pregunta sobre los pagos en línea,
no dudes en contactarnos.

Gracias por ser parte de [NOMBRE_GIMNASIO]

Saludos,
Equipo [NOMBRE_GIMNASIO]

---
P.D. Si prefieres seguir pagando en recepción, por supuesto puedes hacerlo.
     Esta es solo una opción adicional para tu comodidad.
```

---

## Template 3: Payment Confirmation Email (Auto-sent)

**Subject:** ✅ Pago Recibido - Factura #[INVOICE_NUMBER]

```
Hola [NOMBRE_MIEMBRO],

¡Tu pago ha sido procesado exitosamente! ✅

DETALLES DEL PAGO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fecha: [FECHA]
Factura: [NUMERO_FACTURA]
Monto Pagado: ₡[MONTO]
Método de Pago: [METODO] (SINPE Móvil/Tarjeta)
ID Transacción: [TRANSACTION_ID]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 FACTURA ELECTRÓNICA:

Tu factura electrónica oficial está adjunta a este correo en formato PDF.
Esta factura ha sido enviada y aprobada por el Ministerio de Hacienda.

🏋️ ESTADO DE TU MEMBRESÍA:

Membresía: [TIPO_MEMBRESIA]
Válida hasta: [FECHA_VENCIMIENTO]
Estado: ✅ Activa

🔍 VER DETALLES:

Puedes ver todos tus pagos y facturas en tu portal:
[LINK_TO_PORTAL]

¿NECESITAS AYUDA?

Si tienes alguna pregunta sobre este pago, contáctanos:
📧 [EMAIL]
📱 [TELEFONO]
🕐 Horario: Lun-Vie 6:00-21:00, Sáb 7:00-15:00

¡Gracias por tu pago!

Equipo [NOMBRE_GIMNASIO]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este es un correo automático. Tu pago ha sido confirmado y registrado.
No es necesario responder a este mensaje.
```

---

## Template 4: Payment Failed Notification

**Subject:** ⚠️ Pago No Completado - Factura #[INVOICE_NUMBER]

```
Hola [NOMBRE_MIEMBRO],

Detectamos que tu intento de pago no se pudo completar.

DETALLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fecha del Intento: [FECHA]
Factura: [NUMERO_FACTURA]
Monto: ₡[MONTO]
Razón: [ERROR_MESSAGE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

😊 NO TE PREOCUPES - ES FÁCIL DE RESOLVER:

Las causas más comunes son:
• Fondos insuficientes en la cuenta
• Límite de transacción excedido
• Datos de tarjeta incorrectos
• Conexión interrumpida durante el proceso

🔄 INTENTA DE NUEVO:

Puedes volver a intentar el pago en cualquier momento:

1. Ingresa a: [LINK_TO_INVOICE]
2. Haz clic en "Pagar en Línea"
3. Completa el proceso nuevamente

💡 CONSEJOS:

• Verifica que tengas fondos suficientes
• Intenta con un método de pago diferente
• Si usaste tarjeta, revisa los datos ingresados
• Asegúrate de tener buena conexión a internet

💳 OPCIONES ALTERNATIVAS:

Si prefieres, también puedes:
• Pagar en recepción (efectivo, tarjeta, SINPE)
• Llamarnos para procesar el pago por teléfono: [TELEFONO]
• Programar un pago automático para el futuro

❓ ¿NECESITAS AYUDA?

Si el problema persiste o tienes dudas:
📧 [EMAIL]
📱 [TELEFONO]
🕐 Estamos aquí para ayudarte

¡No te preocupes! Estamos aquí para facilitarte el proceso.

Saludos,
Equipo [NOMBRE_GIMNASIO]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Factura pendiente de pago. Tu acceso al gimnasio continúa activo.
```

---

## Template 5: Payment Reminder (Before Due Date)

**Subject:** 🔔 Recordatorio: Pago Próximo - Membresía [NOMBRE_GIMNASIO]

```
Hola [NOMBRE_MIEMBRO],

Este es un recordatorio amistoso de que tu próximo pago está próximo a vencer.

DETALLES DE PAGO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Concepto: [DESCRIPCION]
Monto: ₡[MONTO]
Fecha de Vencimiento: [FECHA_VENCIMIENTO]
Días restantes: [DIAS]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ PAGA EN LÍNEA EN SEGUNDOS:

¡Ahora es súper fácil! Solo haz clic aquí:

[BOTON: PAGAR AHORA]

O ingresa a: [LINK_TO_INVOICE]

Acepta SINPE Móvil 📱 y Tarjetas 💳

✨ BENEFICIOS DE PAGAR EN LÍNEA:

✅ Instantáneo - Paga en menos de 2 minutos
✅ 24/7 - Paga cuando quieras
✅ Seguro - Plataforma certificada
✅ Automático - Recibe tu factura al instante

🏋️ MANTÉN TU ACCESO ACTIVO:

Realizar el pago antes de [FECHA_VENCIMIENTO] asegura que tu acceso al
gimnasio continúe sin interrupciones.

💬 ¿TIENES PROBLEMAS PARA PAGAR?

Si tienes alguna situación que dificulte tu pago, por favor contáctanos.
Estamos aquí para ayudarte:

📧 [EMAIL]
📱 [TELEFONO]

Gracias por ser parte de [NOMBRE_GIMNASIO]

Equipo [NOMBRE_GIMNASIO]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
También puedes pagar en recepción durante nuestro horario de atención.
```

---

## Template 6: Refund Notification

**Subject:** ✅ Reembolso Procesado - [MONTO]

```
Hola [NOMBRE_MIEMBRO],

Te confirmamos que tu reembolso ha sido procesado exitosamente.

DETALLES DEL REEMBOLSO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monto Reembolsado: ₡[MONTO]
Factura Original: [NUMERO_FACTURA]
Fecha de Reembolso: [FECHA]
Método Original: [METODO]
ID de Reembolso: [REFUND_ID]
Razón: [RAZON]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ ¿CUÁNDO RECIBIRÉ MI DINERO?

El tiempo de procesamiento depende de tu método de pago original:

• SINPE Móvil: 1-2 días hábiles
• Tarjeta de Crédito: 5-10 días hábiles
• Tarjeta de Débito: 3-7 días hábiles

El reembolso aparecerá en el mismo método de pago que usaste originalmente.

📧 FACTURA ELECTRÓNICA:

Se ha generado una nota de crédito electrónica que anula la factura original.
Este documento está adjunto para tus registros.

❓ ¿PREGUNTAS?

Si tienes alguna duda sobre este reembolso o no ves el dinero en tu cuenta
después del tiempo indicado, contáctanos:

📧 [EMAIL]
📱 [TELEFONO]

Lamentamos cualquier inconveniente.

Saludos,
Equipo [NOMBRE_GIMNASIO]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este es un correo automático de confirmación.
```

---

## Template 7: Staff Training Announcement (Internal)

**To:** Staff Team
**Subject:** [IMPORTANTE] Nueva Pasarela de Pagos TiloPay - Capacitación Obligatoria

```
Equipo,

A partir del [FECHA], implementaremos TiloPay como nuestra nueva pasarela
de pagos en línea. Esto permitirá a los miembros pagar sus facturas directamente
desde el portal web usando SINPE Móvil o tarjetas.

CAPACITACIÓN OBLIGATORIA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fecha: [FECHA_CAPACITACION]
Hora: [HORA]
Lugar: [LUGAR/ZOOM_LINK]
Duración: 1 hora
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEMAS A CUBRIR:

1. ¿Qué es TiloPay? (15 min)
   - Qué pueden hacer los miembros
   - Beneficios para el gimnasio
   - Seguridad y cumplimiento

2. Cómo ayudar a los miembros (20 min)
   - Proceso de pago paso a paso
   - Problemas comunes y soluciones
   - Qué hacer si un pago falla
   - Cómo verificar pagos en el sistema

3. Procedimientos internos (15 min)
   - Verificación de pagos
   - Manejo de disputas
   - Contacto con soporte
   - Reportes y conciliación

4. Preguntas frecuentes (10 min)

MATERIAL DE ESTUDIO:

Por favor revisen ANTES de la capacitación:
- Video tutorial (5 min): [LINK]
- Guía rápida: [LINK]
- FAQ: [LINK]

IMPORTANTE:

• Asistencia obligatoria para todo el personal de recepción
• Traer laptop/tablet para práctica
• Habrá evaluación corta al final
• Certificado de participación

CONTACTO PARA DUDAS:

[NOMBRE_COORDINADOR]
[EMAIL]
[TELEFONO]

¡Nos vemos en la capacitación!

Gerencia
```

---

## Template 8: TiloPay Account Approval Follow-up

**To:** sac@tilopay.com
**Subject:** Seguimiento: Solicitud de Cuenta Merchant - [NOMBRE_GIMNASIO]

```
Estimado equipo de TiloPay,

Escribo para dar seguimiento a mi solicitud de cuenta merchant enviada el
[FECHA_SOLICITUD] para [NOMBRE_GIMNASIO].

DETALLES DE LA SOLICITUD:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre del Negocio: [NOMBRE]
RUC: [NUMERO_RUC]
Email de Registro: [EMAIL]
Fecha de Solicitud: [FECHA]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hemos completado toda la documentación requerida y estamos listos para
comenzar la integración técnica.

¿Podrían indicarme:
1. Estado actual de mi solicitud
2. Documentación adicional requerida (si aplica)
3. Tiempo estimado para aprobación
4. Siguiente paso en el proceso

Estamos muy entusiasmados de trabajar con TiloPay y queremos comenzar
lo antes posible.

Quedo atento a su respuesta.

Saludos cordiales,

[NOMBRE]
[CARGO]
[TELEFONO]
[EMAIL]
```

---

## Template 9: Member FAQ - Payment Gateway

**Subject:** Preguntas Frecuentes - Pagos en Línea

```
PREGUNTAS FRECUENTES - PAGOS EN LÍNEA
[NOMBRE_GIMNASIO]

🔐 SEGURIDAD

P: ¿Es seguro pagar en línea?
R: ¡Absolutamente! Usamos TiloPay, una plataforma certificada y regulada
   en Costa Rica. Tus datos financieros están protegidos con encriptación
   de nivel bancario. Nunca almacenamos información de tu tarjeta.

P: ¿Quién procesa mi pago?
R: TiloPay procesa todos los pagos. Es la misma tecnología que usan
   grandes empresas en Costa Rica.

💳 MÉTODOS DE PAGO

P: ¿Qué métodos de pago aceptan?
R: Aceptamos:
   • SINPE Móvil (todos los bancos de CR)
   • Tarjetas Visa, Mastercard, American Express
   • Tarjetas de débito y crédito

P: ¿Cuál método es más rápido?
R: SINPE Móvil es instantáneo (5-30 segundos). Tarjetas también son
   rápidas pero pueden tomar 1-2 minutos.

P: ¿Hay cargos extra por pagar en línea?
R: No. El monto que ves es el que pagas. Sin cargos ocultos.

📱 PROCESO DE PAGO

P: ¿Cómo pago en línea?
R: 1. Entra a [PORTAL]
   2. Ve a "Mis Facturas"
   3. Clic en "Pagar en Línea"
   4. Selecciona tu método (SINPE o Tarjeta)
   5. ¡Listo!

P: ¿Necesito crear una cuenta?
R: Ya tienes acceso con tu usuario de miembro. Usa tu email y contraseña.

P: ¿Puedo pagar desde mi celular?
R: ¡Sí! El sistema funciona perfectamente en celulares, tablets y
   computadoras.

📧 FACTURA ELECTRÓNICA

P: ¿Cuándo recibo mi factura?
R: Inmediatamente después de completar el pago (1-2 minutos).
   Llega por email.

P: ¿La factura es válida para Hacienda?
R: ¡Sí! Es factura electrónica oficial, aprobada por Hacienda.

P: ¿Y si no recibo el email?
R: Revisa tu carpeta de spam. También puedes descargarla desde el portal
   en "Mis Facturas".

⚠️ PROBLEMAS

P: Mi pago falló. ¿Qué hago?
R: Puedes intentar de nuevo inmediatamente. Causas comunes:
   • Fondos insuficientes
   • Límite de transacción excedido
   • Conexión interrumpida
   Si persiste, contáctanos: [TELEFONO]

P: ¿Me cobrarán doble si intento de nuevo?
R: No. Si un pago falla, no se procesa. Puedes intentar sin preocupación.

P: Pagué pero mi factura sigue "pendiente"
R: El sistema toma 1-2 minutos en actualizar. Si después de 5 minutos
   sigue pendiente, contáctanos.

💰 REEMBOLSOS

P: ¿Puedo cancelar un pago?
R: Una vez procesado, debes solicitar reembolso contactándonos. Lo
   procesamos en 24-48 horas.

P: ¿Cuánto tarda un reembolso?
R: SINPE: 1-2 días. Tarjetas: 5-10 días (depende de tu banco).

🕐 DISPONIBILIDAD

P: ¿A qué horas puedo pagar?
R: ¡24/7! El sistema está disponible todo el día, todos los días.

P: ¿Funciona en fin de semana?
R: Sí. SINPE funciona 24/7. Tarjetas también, pero algunos bancos
   pueden demorar la confirmación hasta el lunes.

🔄 OTROS

P: ¿Puedo seguir pagando en recepción?
R: ¡Por supuesto! El pago en línea es opcional. Puedes seguir pagando
   en efectivo, SINPE o tarjeta en recepción.

P: ¿Puedo programar pagos automáticos?
R: Próximamente. Por ahora, cada pago debe hacerse manualmente.

P: ¿Guardan mi información de pago?
R: No. Por seguridad, debes ingresar tus datos en cada pago.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¿MÁS PREGUNTAS?

📧 [EMAIL]
📱 [TELEFONO]
🕐 Lun-Vie 6:00-21:00, Sáb 7:00-15:00

¡Estamos aquí para ayudarte!

Equipo [NOMBRE_GIMNASIO]
```

---

## Usage Instructions

### How to Use These Templates

1. **Replace Placeholders:**
   - `[NOMBRE_GIMNASIO]` → Your gym name
   - `[EMAIL]` → Your contact email
   - `[TELEFONO]` → Your phone number
   - `[LINK_PORTAL]` → Your member portal URL
   - etc.

2. **Customize Content:**
   - Add your branding/logo
   - Adjust tone to match your voice
   - Add/remove sections as needed
   - Translate if needed

3. **Test Before Sending:**
   - Send test emails to yourself
   - Check links work
   - Verify formatting
   - Spell check

4. **Schedule Appropriately:**
   - Template 1: Send immediately for negotiation
   - Template 2: Send when going live
   - Templates 3-6: Auto-send via Odoo
   - Template 7: Internal use
   - Template 9: Post on website/portal

---

**Template Set Version:** 1.0
**Last Updated:** 2025-12-28
**Language:** Spanish (Costa Rica)
**Total Templates:** 9
