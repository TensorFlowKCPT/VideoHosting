    function toggleEdit() {
    var textarea = document.getElementById("myTextarea");
    var editButton = document.getElementById("editButton");

    if (textarea.readOnly) {
        textarea.readOnly = false;
        editButton.innerHTML = "Сохранить";
    } else {
        textarea.readOnly = true;
        editButton.innerHTML = "Изменить";
    }
}


