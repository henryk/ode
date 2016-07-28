$(function(){
    $('.table tr[data-href]').each(function(){
        $(this).css('cursor','pointer').hover(
            function(){ 
                $(this).addClass('active'); 
            },  
            function(){ 
                $(this).removeClass('active'); 
            }).click( function(){ 
                document.location = $(this).attr('data-href'); 
            }
        );
    });
});


function amu_user_enhancements(password_is_required) {

    $(function(){
        var fullname_changed = false;
        var username_changed = false;
        var computed_fullname = function() {
            return $.trim($('#givenname').val() + " " + $('#surname').val());
        };
        var computed_username = function() {
            return $.trim($('#givenname').val().toLowerCase());
        };
        var fullname_change_handler = function() {
            if(!fullname_changed) {
                $('#name').val(computed_fullname());
            }
        };
        var username_change_handler = function() {
            if(!username_changed) {
                $('#userid').val(computed_username());
            }
        }
        $('#name').change(function(){
            fullname_changed = ($('#name').val() != computed_fullname());
        });
        $('#userid').change(function(){
            username_changed = ($('#userid').val() != computed_username());
        });
        $('#givenname').bind("change keyup paste input", fullname_change_handler);
        $('#surname').bind("change keyup paste input", fullname_change_handler);
        $('#givenname').bind("change keyup paste input", username_change_handler);

        if(typeof window.crypto !== 'undefined' && typeof window.crypto.getRandomValues !== 'undefined') {
            var password_generated = false;
            var generate_password = function(do_focus) {
                if(password_generated) {
                    return
                };
                var array = new Uint32Array(5);
                crypto.getRandomValues(array);
                var pass = "";
                for(var i=0; i<array.length; i++) {
                    if(i > 0) {
                        pass = pass + " ";
                    }
                    var rnd = ((1.0*array[i])/Math.pow( 2, 32 ));
                    pass = pass + words_de[Math.floor(rnd*words_de.length)];
                }
                $('#password').val(pass).change();
                if(do_focus) {
                    $('#password').select();
                };
                $('#generate_password').prop("disabled", true);
                password_generated = true;
            }

            if(password_is_required) {
                $(function(){
                    generate_password(false);
                });
            } else {
                var pass_orig = $('#password');
                var new_div = $('<div class="input-group"><span class="input-group-btn"><button class="btn btn-default" id="generate_password" type="button">Generate!</button></span></div>');
                $('#password').replaceWith(new_div);
                new_div.prepend(pass_orig);
                $('#generate_password').on('click', function(){
                    generate_password(true);
                });
            }


            var update_password_visibility = function() {
                $('#password').removeAttr('type');
                if($('#send_password').prop('checked')) {
                    $('#password').prop('type', 'password');
                    generate_password(false);
                } else {
                    $('#password').prop('type', 'text');
                }
            };
            $('#send_password').bind("change",  update_password_visibility);
            $(update_password_visibility);
        
        } // end-if password generation is available

        $('#password').attr("autocomplete", "off");

        var meter_inserted = false;
        $('#password').bind("change keyup paste input", function(){
            if(typeof zxcvbn !== 'undefined') {
                if(!meter_inserted) {
                    var new_div = $('<div class="progress progress-text-center" id="passwordstrength"><div class="progress-bar" role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100" style="width: 60%;"><span>60% Complete</span></div></div>');
                    if($('#password').parent().hasClass("input-group")) {
                        new_div.insertAfter($('#password').parent());
                    } else {
                        new_div.insertAfter('#password');
                    }
                    meter_inserted = true;
                }
                var result = zxcvbn($('#password').val());
                var strength = parseInt(result.guesses_log10 * 3);
                if(strength > 100) {
                    strength = 100;
                }
                $('#passwordstrength div')
                    .attr("aria-valuenow", strength)
                    .attr("style", "width: "+strength+"%");
                $('#passwordstrength div span')
                    .text("Crack time approximately: " + 
                        result.crack_times_display.offline_slow_hashing_1e4_per_second);
                var display_class = "default";
                if(result.score <= 2) {
                    display_class = "danger";
                } else if(result.score == 3) {
                    display_class = "warning";
                } else if(result.score >= 4) {
                    display_class = "success";
                }
                $('#passwordstrength div')
                    .removeClass("progress-bar-default")
                    .removeClass("progress-bar-danger")
                    .removeClass("progress-bar-warning")
                    .removeClass("progress-bar-success")
                    .addClass("progress-bar-" + display_class);
            }
        });

    });

};
