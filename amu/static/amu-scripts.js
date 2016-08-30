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

$(function() {
    if($("*[autofocus]").length == 0) {
        var mod = $("form *.has-error input").first().attr('autofocus', 'autofocus').focus();
        if(mod.length == 0) {
            $('form input:text[value=""]:visible:enabled:first').first().attr('autofocus', 'autofocus').focus();
        }
    }
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

function amu_mailing_list_enhancements() {
    var tags = all_groups.map(function(i){return { value: i[0], label: "Group: "+i[1] };}).concat(
        all_users.map(function(i){return { value: i[0], label: "User: "+i[1] };})
    );
    console.log(tags);
    $(function(){
        $('#list_members > li').replaceWith(function(){ return $("<li>").text( $("input", this).attr("value") ); });
        $('#list_members').tagit({
            removeConfirmation: true,
            showAutocompleteOnFocus: true,
            allowSpaces: true,
            fieldName: 'list_members',
            availableTags: tags.map(function(i){ return i.label; }),
            beforeTagAdded: function(event, ui) {
                var input=$("input", $(ui.tag));
                console.log(input.attr("value"));
                input.attr("value", tags.reduce(function(prev, cur){
                    
                    if(cur.value==ui.tagLabel) {
                        console.log(cur.value + ", "+ ui.tagLabel);
                        return cur.label;
                    }
                    return prev;
                }, ui.tagLabel));
                console.log(input.attr("value"));
                return true;
            },
        });
        $('div[role=main] > form').submit(function(){
            var i=0;
            $("input[name=list_members]", this).each(function(){
                $(this).attr("name", $(this).attr("name")+"-"+i);
                i=i+1;
            });
        });
    });
};