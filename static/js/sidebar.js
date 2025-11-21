document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const mobileToggle = document.getElementById('mobileToggle');
    const mainContent = document.querySelector('.main-content');
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);

    // Load sidebar state from localStorage
    function loadSidebarState() {
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true' && window.innerWidth > 768) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        }
    }

    // Toggle sidebar
    mobileToggle.addEventListener('click', function () {
        if (window.innerWidth <= 768) {
            // Mobile behavior
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        } else {
            // Desktop behavior
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');

            // Save sidebar state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);

            if (isCollapsed) {
                // Close all submenus when collapsing
                document.querySelectorAll('.menu-item.has-submenu.expanded').forEach(item => {
                    item.classList.remove('expanded');
                    const submenu = item.nextElementSibling;
                    if (submenu && submenu.classList.contains('submenu')) {
                        submenu.classList.remove('expanded');
                    }
                });
            }
        }
    });

    // Close sidebar when clicking on overlay
    overlay.addEventListener('click', function () {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });

    // Submenu functionality
    const menuItemsWithSubmenu = document.querySelectorAll('.menu-item.has-submenu');

    menuItemsWithSubmenu.forEach(item => {
        item.addEventListener('click', function (e) {
            // For mobile devices, always allow submenu toggling
            if (window.innerWidth <= 768 || !sidebar.classList.contains('collapsed')) {
                e.preventDefault();
                e.stopPropagation();
                
                const submenu = this.nextElementSibling;
                const isExpanded = this.classList.contains('expanded');

                // Close all other submenus
                document.querySelectorAll('.menu-item.has-submenu.expanded').forEach(expandedItem => {
                    if (expandedItem !== this) {
                        expandedItem.classList.remove('expanded');
                        const otherSubmenu = expandedItem.nextElementSibling;
                        if (otherSubmenu && otherSubmenu.classList.contains('submenu')) {
                            otherSubmenu.classList.remove('expanded');
                        }
                    }
                });
                
                // Toggle current submenu
                this.classList.toggle('expanded');
                if (submenu && submenu.classList.contains('submenu')) {
                    submenu.classList.toggle('expanded');
                }
            }
        });
    });

    // Close sidebar when clicking on menu items (mobile)
    const menuItems = document.querySelectorAll('.menu-item:not(.has-submenu)');
    menuItems.forEach(item => {
        item.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            }

            // Remove active class from all items
            document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
            document.querySelectorAll('.submenu-item').forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
        });
    });

    // Handle clicks on submenu items
    const submenuItems = document.querySelectorAll('.submenu-item');
    submenuItems.forEach(item => {
        item.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            }
            
            // Remove active class from all items
            document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
            document.querySelectorAll('.submenu-item').forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Also activate parent menu item
            const parentMenu = this.closest('.submenu').previousElementSibling;
            if (parentMenu && parentMenu.classList.contains('menu-item')) {
                parentMenu.classList.add('active');
            }
        });
    });

    // Close submenus when clicking outside
    document.addEventListener('click', function (e) {
        const isClickInsideSidebar = sidebar.contains(e.target);
        const isClickOnMobileToggle = mobileToggle.contains(e.target);
        
        if (!isClickInsideSidebar && !isClickOnMobileToggle) {
            // Close mobile sidebar
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
            }
            
            // Close submenus in collapsed mode
            if (sidebar.classList.contains('collapsed')) {
                document.querySelectorAll('.menu-item.has-submenu.expanded').forEach(item => {
                    item.classList.remove('expanded');
                    const submenu = item.nextElementSibling;
                    if (submenu && submenu.classList.contains('submenu')) {
                        submenu.classList.remove('expanded');
                    }
                });
            }
        }
    });

    // Handle window resize
    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            // Desktop
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            
            // Restore saved state
            loadSidebarState();
        } else {
            // Mobile
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        }
    });

    // Initialize sidebar state
    function initSidebar() {
        if (window.innerWidth > 768) {
            loadSidebarState();
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    }

    initSidebar();


    // set initial active menu item based on URL
    const currentPath = window.location.pathname;
    let activeSet = false;

    menuItems.forEach(item => {
        const link = item.querySelector('a');
        if (link && link.getAttribute('href') === currentPath) {
            item.classList.add('active');
            activeSet = true;
        }
    });

    if (!activeSet) {
        submenuItems.forEach(item => {
            const link = item.querySelector('a');
            if (link && link.getAttribute('href') === currentPath) {
                item.classList.add('active');
                const parentMenu = item.closest('.submenu').previousElementSibling;
                if (parentMenu && parentMenu.classList.contains('menu-item')) {
                    parentMenu.classList.add('active');
                    parentMenu.classList.add('expanded');
                    const submenu = parentMenu.nextElementSibling;
                    if (submenu && submenu.classList.contains('submenu')) {
                        submenu.classList.add('expanded');
                    }
                }
            }
        });
    }
});