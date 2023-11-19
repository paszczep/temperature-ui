document.addEventListener("DOMContentLoaded", function () {
    var coll = document.querySelector(".collapsible");
    var content = document.querySelector(".content");

    coll.addEventListener("click", function () {
        if (content.style.display === "block") {
            content.style.display = "none";
        } else {
            content.style.display = "block";
        }
    });
});