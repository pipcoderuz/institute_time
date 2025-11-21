document.addEventListener('DOMContentLoaded', function () {
    userImage = document.getElementById("userImage");
    userDropdown = document.getElementById("userDropdown");

    userImage.addEventListener("click", function () {
        userDropdown.classList.toggle("hidden");
    });
    
    // Document click event
    document.addEventListener('click', function (event) {
        const isClickInsideDropdown = userDropdown.contains(event.target);
        const isClickOnToggle = userImage && userImage.contains(event.target);

        if (!isClickInsideDropdown && !isClickOnToggle && !userDropdown.classList.contains('hidden')) {
            userDropdown.classList.add('hidden');
        }
    });
    
});

