function searchTable() {
    // input field
    var input = document.getElementById("search_input");

    // searchable table
    var tables = document.getElementsByClassName("search_table");
    var tr = []
    for (table of tables) {
        c_tr = table.getElementsByTagName("tr");
        for (item of c_tr) {
            if (!item.classList.contains('no_filter')) {
                tr.push(item)
            }
        }
    }

    var i, j;
    for (i = 0; i < tr.length; i++) {
        var found; // true if input is in td-text
        var td = tr[i].getElementsByTagName("td");
        for (j = 0; j < td.length; j++) {
            if (td[j].innerText.toUpperCase().includes(input.value.toUpperCase())) {
                td[j].style.background = "";
                if (input.value.toUpperCase() != '' && td[j].innerText.toUpperCase().includes(input.value.toUpperCase())) {
                    td[j].style.background = "lightgreen"; // colorize items
                }
                found = true;
            } else {
                td[j].style.background = "";
            }
        }

        // filter items
        if (found) {
            tr[i].style.display = "";
            found = false;
        } else {
            tr[i].style.display = "none";
        }
    }
}
