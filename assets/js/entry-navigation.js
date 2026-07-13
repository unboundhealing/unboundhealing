(async function () {

    const nextLink = document.getElementById("entry-next");
    const backLink = document.getElementById("entry-back");

    if (!nextLink || !backLink) return;

    // ------------------------------------------
    // Back button
    // ------------------------------------------

    backLink.addEventListener("click", function (e) {
        e.preventDefault();
        history.back();
    });

    // ------------------------------------------
    // Determine current page
    // ------------------------------------------

    let current = window.location.pathname;

    if (!current.endsWith("/"))
        current += "/";

    // ------------------------------------------
    // Load opening order
    // ------------------------------------------

    let order;

    try {

        const response = await fetch("/assets/opening-order.json");

        order = await response.json();

    } catch (err) {

        console.warn("Opening navigation unavailable.");

        return;

    }

    // ------------------------------------------
    // Find ourselves
    // ------------------------------------------

    const index = order.indexOf(current);

    if (index === -1) {

        // Not an Opening page

        nextLink.href = "/opening/";

        return;

    }

    // ------------------------------------------
    // Last page?
    // ------------------------------------------

    if (index === order.length - 1) {

        nextLink.href = "/opening/";

    } else {

        nextLink.href = order[index + 1];

    }

})();
