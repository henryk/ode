function amu_user_enhancements(password_is_required) {

    $(function(){
        var username_remove_regex = new RegExp('\\b(' + ["bgdr"].join('|') + ')\\b|\\w+\\.', 'g');
        var fullname_changed = false;
        var username_changed = false;
        var computed_fullname = function() {
            return $.trim($('#givenname').val() + " " + $('#surname').val());
        };
        var computed_username = function() {
            var candidate = $('#givenname').val().toLowerCase();
            candidate = $.trim( candidate.replace(username_remove_regex, "") );
            return candidate.replace(/\s+/g, '.');
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

        // Dummy, for the benefit of extract
        i18n.gettext("less than a second");
        i18n.ngettext("%d second", "%d seconds", 2);
        i18n.ngettext("%d minute", "%d minutes", 2);
        i18n.ngettext("%d hour", "%d hours", 2);
        i18n.ngettext("%d day", "%d days", 2);
        i18n.ngettext("%d month", "%d months", 2);
        i18n.ngettext("%d year", "%d years", 2);
        i18n.gettext("centuries");
        var i18n_crack_time = function(crack_time) {
            var re = /^(\d+) (\S+?)s?$/;
            var match = re.exec(crack_time);
            if(match) {
                var count = parseInt(match[1]);
                var singular = "%d " + match[2];
                var plural = "%d " + match[2]+"s";
                return Jed.sprintf( i18n.ngettext(singular, plural, count), count);
            } else {
                return i18n.gettext(crack_time);
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
                var new_div = $('<div class="input-group"><span class="input-group-btn"><button class="btn btn-default" id="generate_password" type="button"></button></span></div>');
                $("button", new_div).text( i18n.gettext("Generate!") );
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
                    $('#password').val("").change();
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
                    .text( i18n.gettext("Crack time approximately: ") + 
                        i18n_crack_time(result.crack_times_display.offline_slow_hashing_1e4_per_second));
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

        var aliases = $('#aliases').val().split(",").map(function(i){return i.trim();});
        if(aliases[0]=="") {aliases.pop()};
        replace_with_select2('aliases');
        $('#aliases').select2({
            theme: 'bootstrap',
            tags: aliases,
            tokenSeparators: [',', ' '],
        });
        $('#aliases').val(aliases).trigger("change");
        $('div[role=main] > form').submit(function(){
            $('#aliases').replaceWith(function(){
                var result = $('<input type="hidden" name="aliases">');
                var thisval = $(this).val();
                result.val(thisval ? thisval.join(",") : "");
                return result;
            });
        });
    });

};

function amu_list_enhancements(target) {
    var seen = {};
    var tags = (all_groups.map(function(i){
                seen[i[0]] = true;
                return { "id": i[0], text: i18n.gettext("Group") + ": "+i[1] };
            })).concat(
                all_users.map(function(i){
                    seen[i[0]] = true;
                    return { "id": i[0], text: i18n.gettext("User") + ": "+i[1] };
            })).concat(
                all_aliases.map(function(i){
                    seen[i[0]] = true;
                    return { "id": i[0], text: i18n.gettext("Alias") + ": "+i[1] };
            }));
    $(function(){
        var list_members = $('#' + target +' > li input').map(function(i, obj){return $(obj).val()}).get();
        var additional_members = list_members.filter(function(i){return !seen.hasOwnProperty(i)});
        replace_with_select2(target);
        $('#' + target).select2({
            theme: 'bootstrap',
            tags: tags.concat(additional_members.map(
                function(i){
                    return { "id": i, "text": i };
                }
            )),
        });

        $('#' + target).val(list_members).trigger("change");
        $('div[role=main] > form').submit(function(){
            var new_members = $('#' + target).val();
            var new_inputs = $();
            $.each(new_members, function(i, obj){
                new_inputs = new_inputs.add( $('<input type="hidden" name="'+target+'-'+i+'">').val(obj) );
            });
            $('#'+target).replaceWith(new_inputs);
        });
    });
};