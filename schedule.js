document.addEventListener("DOMContentLoaded", (event) => {
  var dragSrcEl = null;

  function handleDragStart(e) {
    this.style.opacity = "0.4";

    dragSrcEl = this;

    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/html", this.innerHTML);
  }

  function handleDragOver(e) {
    if (e.preventDefault) {
      e.preventDefault();
    }

    e.dataTransfer.dropEffect = "move";

    return false;
  }

  function handleDragEnter(e) {
    this.classList.add("over");
  }

  function handleDragLeave(e) {
    this.classList.remove("over");
  }

  function handleDrop(e) {
    if (e.stopPropagation) {
      e.stopPropagation(); // stops the browser from redirecting.
    }

    if (dragSrcEl != this) {
      dragSrcEl.innerHTML = this.innerHTML;
      this.innerHTML = e.dataTransfer.getData("text/html");
      setupInput(dragSrcEl.querySelector("input"));
      setupInput(this.querySelector("input"));
    }

    return false;
  }

  function handleDragEnd(e) {
    this.style.opacity = "1";

    items.forEach(function (item) {
      item.classList.remove("over");
    });
  }

  function addDragAndDropEventListeners(item) {
    item.addEventListener("dragstart", handleDragStart, false);
    item.addEventListener("dragenter", handleDragEnter, false);
    item.addEventListener("dragover", handleDragOver, false);
    item.addEventListener("dragleave", handleDragLeave, false);
    item.addEventListener("drop", handleDrop, false);
    item.addEventListener("dragend", handleDragEnd, false);
  }

  let items = document.querySelectorAll("td.duty-cell");
  items.forEach(function (item) {
    addDragAndDropEventListeners(item);
  });

  function addInputListener(input) {
    input.addEventListener("input", function (e) {
      input.setAttribute("value", e.target.value);
    });
  }

  function addMouseOverListener(input) {
    input.addEventListener("mouseover", (event) => {
      // find all inputs with same value and change background
      let mouseoverValue = input.getAttribute("value");
      $(".assignment-input")
        .filter((i, el) => {
          console.log(`found ${el.value.trim()}`);
          return el.value.trim() == mouseoverValue;
        })
        .addClass("search-highlight");
    });
  }

  function addMouseLeaveListener(input) {
    input.addEventListener("mouseleave", (event) => {
      // find all inputs with same value and change background
      let mouseoverValue = input.getAttribute("value");
      $(".assignment-input")
        .filter((i, el) => {
          return el.value.trim() == mouseoverValue;
        })
        .removeClass("search-highlight");
    });
  }

  function setupInput(input) {
    input.setSelectionRange(-1, -1);
    addInputListener(input);
    addMouseOverListener(input);
    addMouseLeaveListener(input);
  }

  let inputs = document.querySelectorAll("input");
  inputs.forEach(function (input) {
    setupInput(input);
  });
});
