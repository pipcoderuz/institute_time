// Show/hide password onClick of button using Javascript only

function show() {
    var p = document.getElementById('id_password');
    p.setAttribute('type', 'text');
}

function hide() {
    var p = document.getElementById('id_password');
    p.setAttribute('type', 'password');
}

var pwShown = 0;
document.getElementById("eye").addEventListener("click", function () {
    if (pwShown == 0) {
        pwShown = 1;
        show();
    } else {
        pwShown = 0;
        hide();
    }
}, false);

