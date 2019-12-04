function sortTable() {
    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

    const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
        v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
        )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

    document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
        const table = th.closest('table');
        const tbody = table.getElementsByTagName('tbody')[0];
        Array.from(tbody.querySelectorAll('tr'))
            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
            .forEach(tr => tbody.appendChild(tr) );
    })));
}

window.onload = sortTable;

function searchTable(table_id = "search_table") {
    // input field
    var input = document.getElementById("search_input");

    // searchable table
    var tables = document.getElementsByClassName(table_id);
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
