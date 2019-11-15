document.addEventListener('DOMContentLoaded', function() {
    var sidenav_elems = document.querySelectorAll(".sidenav");
    var dropdown_elems = document.querySelectorAll(".dropdown-trigger");
    var collapsible_elems = document.querySelectorAll(".collapsible");

    var dropdown_options = {
        "alignment": "right",
        "autoTrigger": false,
        "constrainWidth": false,
        "coverTrigger": false,
        "hover": true,
        "inDuration": 100,
        "outDuration": 125
    };

    var sidenav_instances = M.Sidenav.init(sidenav_elems);
    var dropdown_instances = M.Dropdown.init(dropdown_elems, dropdown_options);
    var collapsible_instances = M.Collapsible.init(collapsible_elems);
  });
