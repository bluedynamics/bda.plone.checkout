/* jslint browser: true */
/* global jQuery, common_content_filter */
(function($) {
    "use strict";

    $(document).ready(function() {
        var delivery_address = $('#form-checkout div.delivery_address');
        var toggle = function(input) {
            if (input.attr('type') === 'hidden') {
                delivery_address.show();
                return;
            }
            if (input.is(':checked')) {
                delivery_address.show();
            } else {
                delivery_address.hide();
            }
        };
        var fld_name = "checkout.delivery_address.alternative_delivery";
        var input = $('input[name="' + fld_name + '"]');
        toggle(input);
        input.change(function(event) {
            toggle($(this));
        });

    });

}(jQuery));
