userImage = document.getElementById("userImage");
userDropdown = document.getElementById("userDropdown");

userImage.addEventListener("click", function () {
    userDropdown.classList.toggle("hidden");
});

langBtn = document.getElementById("langBtn");
langDropdown = document.getElementById("langDropdown");

langBtn.addEventListener("click", function(){
    langDropdown.classList.toggle("hidden");
});

