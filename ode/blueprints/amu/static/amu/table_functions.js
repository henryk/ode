function sortTable(n, table_index) {
    var table = document.getElementsByTagName("table")[table_index]
    if (!table) {
        return;
    }

    var isSwitching = true;
    var switchCount = 0; // how many rows were switched
    var order = "up"; // up - alphabetical / down - backward
    while (isSwitching) {
        isSwitching = false;
        var rows = table.rows;
        var canSwitch;
        var i;
        for (i = 1; i < (rows.length - 1); i++) {
            canSwitch = false;
            var a = rows[i].getElementsByTagName("td")[n];
            var b = rows[i + 1].getElementsByTagName("td")[n];
            if (order == "up") {
                if (a.innerText.toUpperCase() > b.innerText.toUpperCase()) {
                    canSwitch = true;
                    break;
                }
            } else if (order == "down") {
                if (a.innerText.toUpperCase() < b.innerText.toUpperCase()) {
                    canSwitch = true;
                    break;
                }
            }
        }

        // switch
        if (canSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            isSwitching = true;
            switchCount++;
        } else {
            if (switchCount == 0 && order == "up") {
                order = "down";
                isSwitching = true;
            }
        }
    }
}

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
        var isFound; // true if input is in td-text
        var td = tr[i].getElementsByTagName("td");
        for (j = 0; j < td.length; j++) {
            if (td[j].innerText.toUpperCase().includes(input.value.toUpperCase())) {
                td[j].style.background = "";
                if (input.value.toUpperCase() != '' && td[j].innerText.toUpperCase().includes(input.value.toUpperCase())) {
                    td[j].style.background = "lightgreen"; // colorize items
                }
                isFound = true;
            } else {
                td[j].style.background = "";
            }
        }

        // filter items
        if (isFound) {
            tr[i].style.display = "";
            isFound = false;
        } else {
            tr[i].style.display = "none";
        }
    }
}
