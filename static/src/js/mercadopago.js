odoo.define('exdoo_sale_web_payment.mercadopago', function (require) {
    'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    const mp = new MercadoPago($("#ky").val());
    console.log("MP:", mp)
    console.log("==== MercadoPago init ===")
    // Inicializa el checkout
    mp.checkout({
        preference: {
            id: $("#mercadopago_id").val(),
        },
        render: {
            container: ".exdoo-mercadopago", // Indica el nombre de la clase donde se mostrará el botón de pago
            label: "Pagar con MercadoPago", // Cambia el texto del botón de pago (opcional)
        },

    });

});
