
## Page 1


Guía de integración
SDK Tilopay
www.tilopay.com



## Page 2


Historial de cambios
Las versiones del documento cambian de acuerdo a las nuevas funcionalidades
que se integran al SDK
Fecha Versión Descripción
29/07/2022 1.0.0 Integración de payment form Tilopay
Agrega uso de tokens guardados
05/10/2022 1.1.0
Integra pagos con Sinpe Móvil
30/08/2023 1.2.0 Agrega método para tokenizar tarjetas
1



## Page 3


Esta integración proporciona la funcionalidad de usar en su formulario de pago la
seguridad que proporciona Tilopay.
El proceso de configuración de esta integración requiere de un conocimiento básico o
intermedio en tecnologías javascript y Html
Pasos de integración:
Paso Descripción
1 Importar librería en su formulario de pago
2 Crear estructura requerida para solicitar datos del pago
3 Inicializar y procesar el flujo de pago
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
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://app.tilopay.com/sdk/v1/sdk.min.js"></script>
</body>
</html>
2



## Page 4


Paso 2: Crear estructura requerida para los datos de pago.
Los campos requeridos son los siguientes:
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
mes / año (01 / 22)
Campo de tipo text donde el usuario debe digitar el código de seguridad de la
cvv
tarjeta
Estos campos mencionados, deben estar dentro de un div con la clase
payFormTilopay, similar al siguiente ejemplo.
<body>
<div class="payFormTilopay">
<label>Payment Method</label>
<select name="method" id="method">
<option value="">Select payment method</option>
</select>
<label>Cards</label>
<select name="cards" id="cards">
<option value="">Select card</option>
</select>
<label>Card Number</label>
<input type="text" id="ccnumber" name="ccnumber" value="">
<label>Card Expire</label>
<input type="text" id="expdate" name="expdate" value="">
<label>Cvv Number</label>
<input type="text" id="cvv" name="cvv" value="">
</div>
…
</body>
3



## Page 5


Adicional requiere agregar un contenedor con el id result, su función será llevar a cabo
el proceso de 3ds en caso que el método de pago así lo requiera.
<body>
<div class="payFormTilopay">
…
</div>
<div id="result"></div>
…
</body>
4



## Page 6


Paso 3: Implementar interacción con el SDK de Tilopay, para ello se establecen varias
funciones.
Funciones para manejo del proceso de compra por medio de Tilopay:
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
disponibles.
Método para obtener el tipo de tarjeta Retorna el tipo de tarjeta
Tilopay.getCardType()
que ingreso el usuario visa – mastercard – amex
Método para obtener datos de pago Retorna mensaje de error en
Tilopay.getSinpeMovil() para el método Sinpe Móvil caso de existir, y retorna los
parámetros de Sinpe Móvil
En caso de ser necesario, con este Retorna mensaje Success o
método puede recargar los valores descripción del error ocurrido
Tilopay.updateOptions({})
necesarios para realizar el proceso de
pago.
Método para enviar a procesar el pago Retorna mensaje de error en
Tilopay.startPayment()
en Tilopay, no recibe ningún parámetro caso de existir
Opcional Requerido
Formulario de pago
Tilopay.Init
Formulario carga métodos
de pago y tarjetas
Tilopay.getCardType
guardadas
Usuario ingresa datos de
Tilopay.updateOptions
pago
Finaliza proceso de pago Tilopay.startPayment
5



## Page 7


Tilopay.Init({})
Da inicio al proceso de compra con Tilopay, por medio de el se realiza la autenticación
y se reciben los métodos de pago disponibles para la compra. Los parámetros que
recibe son los siguientes:
Parámetro Descripción Tipo Posibles Obligatorio en
valores llamado Init()
Token obtenido del método
token String Obligatorio
GetTokenSdk del Api Tiliopay
Códigos de
currency Moneda de la compra String 3 Obligatorio
divisa ISO 4217
Idioma para manejo de
language String 2 es, en Obligatorio
mensajes
Decimal
amount Monto de la compra Obligatorio
12,2
billToEmail Correo electrónico del cliente String Obligatorio
Alfanumeri No se puede
orderNumber Número de orden Obligatorio
co repetir
Tipo de identificación Ver tabla tipos
typeDni integer
(obligatorio para sinpe movil) de identificación
Número de identificación del
dni cliente (obligatorio para sinpe String
movil)
billToFirstName Nombre del cliente String
billToLastName Apellidos del cliente String
billToAddress Dirección 1 del cliente String
billToAddress2 Dirección 2 del cliente String
billToCity Ciudad del cliente String
billToState Estado del cliente String
billToZipPostCode Código postal del cliente String
billToCountry País del cliente String
billToTelephone Teléfono del cliente String
Continúa en siguiente página.
6



## Page 8


Parámetro Descripción Tipo Posibles Obligatorio en
valores llamado Init()
shipToFirstName Nombre del cliente para envío String
shipToLastName Apellidos del cliente para envío String
Dirección 1 del cliente para
shipToAddress String
envío
Dirección 2 del cliente para
shipToAddress2 String
envío
shipToCity Ciudad del cliente para envío String
shipToState Estado del cliente para envío String
Código postal del cliente para
shipToZipPostCode String
envío
shipToCountry País del cliente para envío String
shipToTelephone Teléfono del cliente para envío String
Indica si desea autorizar (0) o
capture integer 0, 1
capturar (1) la compra
Url (callback) donde se espera
redirect String
la respuesta final de la compra
Indica si el cliente desea
subscription guardar su tarjeta en Tilopay, 1 integer 0, 1
para si, 0 para no
7



## Page 9


Ejemplo de llamado al método Tilopay.Init({})
<body>
...
<script type="text/javascript">
$(document).ready(function() {
var initialize = Tilopay.Init({
token : "5f5bdc06b7318e4743104ece770bf…1995a61e3fc1d827c01a8f092",
currency : "USD",
language : "es",
amount : 100.00,
typeDni : 1,
dni : "707770777",
billToFirstName : "Jose",
billToLastName : "Lopez",
billToAddress : "San Jose",
billToAddress2 : "Aserri",
billToCity : "SJO",
billToState : "SJO",
billToZipPostCode : "1001",
billToCountry : "CR",
billToTelephone : "88888888",
billToEmail : "email@usuario.com",
orderNumber : "54221",
capture : 1,
redirect : "https://www.miwebsite.com/response",
subscription : 0
});
});
</script>
</body>
Ejemplo de respuesta método Tilopay.Init({})
{
message: "Success",
environment: "PROD"
sinpemovil: {"code" : "SM0212", "amount" : "100.00" },
methods: [
{"id":"452:3:15", "name":"Tarjeta Crédito / Débito", "type":"card"},
{"id":"362:3:18", "name":"Tasa cero 3 Meses", "type":"card"},
{"id":"742:3:14", "name":"Tasa cero 6 Meses", "type":"card"},
{"id":"582:3:10", "name":"Tasa cero 12 Meses", "type":"card"},
{"id":"587:4:17", "name":“Sinpe Móvil", "type":" sinpemovil "}
],
cards: [
{"id":“411112555451111:Ref", "name":“4111********1111", “brand":“visa"}
]
}
---------------------------------------------------------------------------------------------------------------------------------------
{
message: “Descripción del error"
methods: [],
cards: []
}
8



## Page 10


Métodos de pagos
Se listarán los métodos de pago disponibles del comercio para poder realizar el pago,
incluye métodos de pago con tarjeta y Sinpe Móvil.
methods: [
{"id":"452:3:15", "name":"Tarjeta Crédito / Débito", "type":"card"},
{"id":"362:3:18", "name":"Tasa cero 3 Meses", "type":"card"},
{"id":"742:3:14", "name":"Tasa cero 6 Meses", "type":"card"},
{"id":"582:3:10", "name":"Tasa cero 12 Meses", "type":"card"}
{"id":"585:4:15", "name":"Sinpe Móvil", "type":"sinpemovil"}
]
Tarjetas guardadas del usuario
Se listarán las tarjetas que posee disponibles el usuario para proceder a realizar el
pago.
cards: [
{"id":“4111ABCD1111:Ref", "name":“41111*******1111", “brand":“visa"},
{"id":“5111ABCD1111:Ref", "name":“51111*******1111", “brand":“mastercard"},
{"id":“3111ABCD1111:Ref", "name":“31111*******1111", “brand":“amex"}
]
Las tarjetas deben ser mostradas al usuario para que pueda seleccionar una de ellas,
o bien poder ingresar los datos de una nueva tarjeta. El select destinado a las tarjetas
debe tener el id cards
Cuando el cliente utiliza una de las tarjetas guardadas, debe habilitarse el campo cvv
para que el cliente pueda digitar el código de seguridad de su tarjeta.
Para obtener las tarjetas del cliente, es obligatorio enviar el parámetro con el
billToEmail
correo electrónico del cliente al hacer el llamado del método Tras obtener las
Init({}).
tarjetas no se podrá cambiar el correo del usuario por medio del método
updateOptions({})
9



## Page 11


Tilopay.InitTokenize({})
Da inicio al proceso de tokenizacion con Tilopay, por medio de el se realiza la
autenticación y se reciben los métodos de pago disponibles para guardar la tarjeta en
Tilopay. Los parámetros que recibe son los siguientes:
Parámetro Descripción Tipo Posibles Obligatorio en
valores llamado
InitTokenize()
Token obtenido del método
token String Obligatorio
GetTokenSdk del Api Tiliopay
Códigos de
currency Moneda de la compra String 3 Obligatorio
divisa ISO 4217
Idioma para manejo de
language String 2 es, en Obligatorio
mensajes
Correo electrónico del cliente, la
billToEmail String Obligatorio
tarjeta se asociara a este correo
billToFirstName Nombre del cliente String
billToLastName Apellidos del cliente String
billToAddress Dirección 1 del cliente String
billToAddress2 Dirección 2 del cliente String
billToCity Ciudad del cliente String
billToState Estado del cliente String
billToZipPostCode Código postal del cliente String
billToCountry País del cliente String
billToTelephone Teléfono del cliente String
Url (callback) donde se espera
redirect String
la respuesta final de la compra
Este método procesará un cobro al tarjetahabiente por $1 o su equivalente en la
moneda a procesar, con el fin de validar la tarjeta y proceder a guardarla, este monto
será reversado inmediatamente siendo devuelto al usuario en unos minutos.
Para utilizar el guardado de tarjetas, se reemplaza el método Init por InitTokenize, y se
concluye de igual manera con el método startPayment, cuando reciba la respuesta
almacene el token obtenido y asócielo al correo electrónico del usuario para su uso
posterior.
10



## Page 12


Ejemplo de llamado al método Tilopay.InitTokenize({})
<body>
...
<script type="text/javascript">
$(document).ready(function() {
var initialize = Tilopay.InitTokenize({
token : "5f5bdc06b7318e4743104ece770bf…1995a61e3fc1d827c01a8f092",
currency : "USD",
language : "es",
billToFirstName : "Jose",
billToLastName : "Lopez",
billToAddress : "San Jose",
billToAddress2 : "Aserri",
billToCity : "SJO",
billToState : "SJO",
billToZipPostCode : "1001",
billToCountry : "CR",
billToTelephone : "88888888",
billToEmail : "email@usuario.com",
redirect : "https://www.miwebsite.com/response"
});
});
</script>
</body>
Ejemplo de respuesta método Tilopay.InitTokenize({})
{
message: "Success",
environment: "PROD"
methods: [
{"id":"452:3:15", "name":"Tarjeta Crédito / Débito", "type":"card"},
{"id":"362:3:18", "name":"Tasa cero 3 Meses", "type":"card"},
{"id":"742:3:14", "name":"Tasa cero 6 Meses", "type":"card"},
{"id":"582:3:10", "name":"Tasa cero 12 Meses", "type":"card"},
{"id":"587:4:17", "name":“Sinpe Móvil", "type":" sinpemovil "}
],
}
---------------------------------------------------------------------------------------------------------------------------------------
{
message: “Descripción del error"
methods: []
}
11



## Page 13


Tipos de identificación
Si posee métodos de pago Sinpe Móvil, debe solicitar al usuario y aportar al sdk el
tipo de identificación, así como la identificación del cliente, con el fin de identificar más
rápidamente el pago realizado por el usuario.
Código Tipo Formato Longitud
1 Cédula de identidad 0#-####-#### 10
2 Cédula Jurídica 3-###-###### 10
3 Gobierno Central 2-###-###### 10
4 Institución Autónoma 4-###-###### 10
5 Extranjero no Residente 9&&&&&&&&&&&&&&&&&&& 20
6 Dimex 1########### 12
7 DIDI 5########### 12
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
estos parámetros se recomienda mostrar al usuario con un mensaje similar al
siguiente:
Para realizar el pago con SINPE Móvil, debe asegurarse de realizar el pago
de la siguiente forma:
Teléfono: 8888 8888
₡
Monto exacto: 100,00
Indicar en la descripción: TB095
•
Puede colocarse un botón, indicando al usuario “Una vez realizado el SINPE Móvil,
por favor confirme su transacción” y tras dar clic mostrar mensaje indicando al
cliente que se esta a la espera de recibir el deposito por SINPE Móvil. Asegurarse
de que el usuario ingrese un correo, tipo de identificación y la identificación antes
de poder presionar este botón.
12



## Page 14


Tilopay.getCardType()
Este método obtiene el tipo de tarjeta que el cliente ingreso, puede ser utilizado para
indicar al usuario mediante un icono el tipo de tarjeta que esta usando, su uso requiere
que el usuario ya haya ingresado el número de tarjeta. Este método no requiere el
envió de ningún parámetro. Retorna un mensaje con el valor correspondiente a la
marca de la tarjeta.
Valor Soportada
visa Si
mastercard Si
amex Si
elo No
visaelectron No
maestro No
forbrugsforeningen No
dankort No
hipercard No
dinersclub No
discover No
unionpay No
jcb No
laser No
Ejemplo de llamado al método Tilopay.getCardType()
<body>
...
<script type="text/javascript">
$(document).ready(function() {
var type = Tilopay.getCardType();
});
</script>
</body>
Ejemplo de respuesta método Tilopay.getCardType()
{
message: "visa"
}
13



## Page 15


Tilopay.getSinpeMovil()
Este método obtiene los datos a mostrar al usuario para realizar su pago mediante
Sinpe Móvil, para su uso es necesario que el usuario seleccione como método de
pago Sinpe Móvil.
Ejemplo de llamado al método Tilopay.getSinpeMovil()
<body>
...
<script type="text/javascript">
$(document).ready(function() {
var params = Tilopay.getSinpeMovil();
});
</script>
</body>
Ejemplo de respuesta método Tilopay.getSinpeMovil()
{
message: "Success",
code" : "TB095",
amount : 100.00,
number : “8888 8888“
}
---------------------------------------------------------------------------------------------------------------------------------------
{
message: “Descripción del error"
code" : "",
amount : "“,
number : "“
}
14



## Page 16


Tilopay.updateOptions({})
Este método puede ser utilizado para actualizar los parámetros del método Init que
pudieron variar, debe ser utilizado antes de finalizar el pago en caso de requerirse, su
uso es opcional. Los valores que pueden ser actualizados son los siguientes:
Parámetro Descripción Tipo Posibles valores
Tipo de identificación (obligatorio para Ver tabla tipos de
typeDni integer
Sinpe Móvil) identificación
Número de identificación del cliente
dni String
(obligatorio para Sinpe Móvil)
billToFirstName Nombre del cliente String
billToLastName Apellidos del cliente String
billToAddress Dirección 1 del cliente String
billToAddress2 Dirección 2 del cliente String
billToCity Ciudad del cliente String
billToState Estado del cliente String
billToZipPostCode Código postal del cliente String
billToCountry País del cliente String
billToTelephone Teléfono del cliente String
shipToFirstName Nombre del cliente para envío String
shipToLastName Apellidos del cliente para envío String
shipToAddress Dirección 1 del cliente para envío String
shipToAddress2 Dirección 2 del cliente para envío String
shipToCity Ciudad del cliente para envío String
shipToState Estado del cliente para envío String
shipToZipPostCode Código postal del cliente para envío String
shipToCountry País del cliente para envío String
shipToTelephone Teléfono del cliente para envío String
Capture Indica si desea autorizar (0) o capturar integer 0, 1
(1) la compra
Redirect Url (callback) donde se espera la String
respuesta final de la compra
Subscription Indica si el cliente desea guardar su integer 0, 1
tarjeta en Tilopay, 1 para si, 0 para no
15



## Page 17


Ejemplo de llamado al método Tilopay.updateOptions({})
<body>
...
<script type="text/javascript">
$(document).ready(function() {
var update = Tilopay. updateOptions({
typeDni : 1,
dni : "707770777",
billToFirstName : "Jose",
billToLastName : "Lopez",
billToAddress : "San Jose",
billToAddress2 : "Aserri",
billToCity : "SJO",
billToState : "SJO",
billToZipPostCode : "1001",
billToCountry : "CR",
billToTelephone : "88888888",
shipToFirstName : "Jose",
shipToLastName : "Lopez",
shipToAddress : "San Jose",
shipToAddress2 : "Aserri",
shipToCity : "SJO",
shipToState : "SJO",
shipToZipPostCode : "1001",
shipToCountry : "CR",
shipToTelephone : "88888888",
capture : 1,
redirect : "https://www.miwebsite.com/response",
subscription : 0
});
});
</script>
</body>
Ejemplo de respuesta método Tilopay.updateOptions({})
{
message: "Success"
}
16



## Page 18


Tilopay.startPayment()
Este método se utiliza para finalizar el proceso de compra, con ellos los datos de pago
viajaran a Tilopay y se procesarán. En caso de ocurrir un error se indicará en el retorno
de este método. Requiere que todos los datos de pago estén completos, sin embargo
no requiere envió de parámetros en su llamado.
Ejemplo de llamado al método Tilopay.startPayment()
<body>
...
<script type="text/javascript">
$(document).ready(function() {
var response = Tilopay.startPayment();
});
</script>
</body>
Ejemplo de respuesta método Tilopay.startPayment()
{
message: "Descripción del error"
}
17



## Page 19


Ejemplo completo
<html>
<head>
<title>E-Commerce</title>
</head>
<body>
<div class="payFormTilopay">
<label>Payment Method</label>
<select name="method" id="method">
<option value="">Select payment method</option>
</select>
<label>Cards</label>
<select name=“cards" id=“cards">
<option value="">Select card</option>
</select>
<label>Card number</label>
<input type="text" id="ccnumber" name="ccnumber" value="">
<label>Card expire</label>
<input type="text" id="expdate" name="expdate" value="">
<label>Cvv number</label>
<input type="text" id="cvv" name="cvv" value="">
<input type="button" onclick="pay();" value="Pay">
<input type="button" onclick=“updateOptions();" value=“Update">
<input type="button" onclick="getCardType();" value="Get Card Type">
<input type="button" onclick="getSinpeMovil ();" value="Get Sinpe Data">
</div>
<div id="result"></div>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://app.tilopay.com/sdk/v1/sdk.min.js"></script>
<script type="text/javascript">
$(document).ready(function() {
var initialize = Tilopay.Init({
token : "5f5bdc06b7318e4743104ec…95a61e3fc1d827c01a8f092",
currency : "USD",
language : "es",
amount : 100.00,
typeDni : 1,
dni : "707770777",
billToFirstName : "Jose",
billToLastName : "Lopez",
18



## Page 20


billToAddress : "San Jose",
billToAddress2 : "Aserri",
billToCity : "SJO",
billToState : "SJO",
billToZipPostCode : "1001",
billToCountry : "CR",
billToTelephone : "88888888",
shipToFirstName : "Jose",
shipToLastName : "Lopez",
shipToAddress : "San Jose",
shipToAddress2 : "Aserri",
shipToCity : "SJO",
shipToState : "SJO",
shipToZipPostCode : "1001",
shipToCountry : "CR",
shipToTelephone : "88888888",
billToEmail : "email@usuario.com",
orderNumber : "52214",
capture : 1,
redirect : "https://www.miwebsite.com/response",
subscription : 0
});
chargeMethods(initialize.methods);
chargeCards(initialize.cards);
});
function getCardType () {
var type = Tilopay.getCardType();
}
function updateOptions () {
var update = Tilopay.updateOptions({
typeDni : 1,
dni : "707770777",
billToFirstName : "Jose",
billToLastName : "Lopez",
billToAddress : "San Jose",
billToAddress2 : "Aserri",
billToCity : "SJO",
billToState : "SJO",
billToZipPostCode : "1001",
billToCountry : "CR",
billToTelephone : "88888888",
shipToFirstName : "Jose",
shipToLastName : "Lopez",
shipToAddress : "San Jose",
shipToAddress2 : "Aserri",
shipToCity : "SJO",
shipToState : "SJO",
shipToZipPostCode : "1001",
shipToCountry : "CR",
shipToTelephone : "88888888",
19



## Page 21


orderNumber : "52214",
capture : 1,
redirect : "https://www.miwebsite.com/response",
subscription : 0
});
}
function chargeMethods (methods) {
methods.forEach(function(method) {
$('#method').append('<option value="'+method.id+'">'+method.name+'</option>');
});
}
function chargeCards (cards) {
cards.forEach(function(card) {
$('#cards').append('<option value="'+card.id+'">'+card.name+'</option>');
});
}
function pay () {
var payment = Tilopay.startPayment();
}
function getSinpeMovil() {
var params = Tilopay.getSinpeMovil();
}
</script>
</body>
</html>
20



## Page 22


www.tilopay.com

