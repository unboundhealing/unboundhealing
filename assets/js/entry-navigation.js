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
    // Determine current page + section
    // ------------------------------------------

    let current = window.location.pathname;

    if (!current.endsWith("/"))
        current += "/";

    const parts = current.split("/");

    const section = parts[1];


    if (!section) {
        nextLink.href = "/";
        return;
    }


    // ------------------------------------------
    // Load section order
    // ------------------------------------------

    let order;

    try {

        const response = await fetch(
            `/assets/navigation/${section}.json`
        );

        order = await response.json();

    } catch (err) {

        console.warn(
            `Navigation unavailable for section: ${section}`
        );

        nextLink.href = `/${section}/`;

        return;

    }


    // ------------------------------------------
    // Find current page
    // ------------------------------------------

    const index = order.indexOf(current);


    if (index === -1) {

        // Not an ordered entry page

        nextLink.href = `/${section}/`;

        return;

    }


    // ------------------------------------------
    // Next page
    // ------------------------------------------

    if (index === order.length - 1) {

        nextLink.href = `/${section}/`;

    } else {

        nextLink.href = order[index + 1];

    }


})();
