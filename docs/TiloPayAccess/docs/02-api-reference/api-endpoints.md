# TiloPay API Endpoints
**Extracted from:** SDK Documentation PDF

---

## Discovered API Information

### URLs

- `https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js`
- `https://app.tilopay.com/sdk/v1/sdk.min.js`
- `https://www.miwebsite.com/response`

### Parameters

- `Token`
- `token`

## Document Sections

### 3 Inicializar y procesar el flujo de pago

Paso 1: Importar las librerías requeridas, aquí puede establecer el diseño, colores y
estilos que desee acorde a su plataforma.
Se requiere de la librería Jquery y sdk de Tilopay.
https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js
https://app.tilopay.com/sdk/v1/sdk.min.js
<html>
<head>
<title>E-Commerce</title>
</head>
<body>

*[7 more lines...]*

### Los campos requeridos son los siguientes:

Campo Descripción
Este campo puede ser tipo text o select, en su valor debe contener el id del método
method
de pago obtenido de Tilopay, puede estar visible u oculto a discreción del comercio
Este campo debe ser tipo select, en su valor debe contener el id de la tarjeta
cards guardada obtenida de Tilopay, en caso de no tener tarjetas guardadas debe
ocultarse al usuario.
ccnumber Campo de tipo text donde el usuario debe digitar el número de tarjeta
Campo de tipo text donde el usuario debe digitar la fecha de expiración en forma
expdate

*[40 more lines...]*

### Funciones para manejo del proceso de compra por medio de Tilopay:

Método Descripción Retorno
Inicialización del método de pago, este Retorna mensaje de error, en
recibe una serie de parámetros caso de existir, y retorna los
Tilopay.Init({})
métodos de pago
disponibles.
Inicialización del método de Retorna mensaje de error, en
tokenizacion, este recibe una serie de caso de existir, y retorna los
Tilopay.InitTokenize({})
parámetros métodos de pago

*[269 more lines...]*

### 7 DIDI 5########### 12

Sinpe Móvil
Para un correcto funcionamiento de Sinpe Móvil se deben seguir algunas reglas
distintas al pago con tarjeta.
•
Enviar los parámetros y por medio del método ó
typeDni dni Init({}) updateOptions({})
•
Ocultar al usuario los campos para realizar pagos con tarjeta, y en su lugar mostrar
al usuario los parámetros de pago Sinpe Móvil obtenidos del método
getSinpeMovil()

*[299 more lines...]*

