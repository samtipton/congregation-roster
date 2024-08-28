document.addEventListener("DOMContentLoaded", (event) => {
  var dragSrcEl = null;
  var saveTimer = null;
  var dirty = false;
  var lastValue = "";
  var toastEl = document.getElementById("toast");

  function hideToast() {
    toastEl.style.opacity = "0.0";
  }

  function showToast(message) {
    if (this.toastTimer) {
      window.clearTimeout(this.toastTimer);
      this.toastTimer = null;
    }
    toastEl.innerText = message;
    toastEl.style.opacity = "0.95";

    this.toastTimer = setTimeout(function () {
      hideToast();
      this.toastTimer = null;
    }, 1000);
  }

  async function commit() {
    await fetch("/commit", {
      method: "PUT",
    }).then((res) => {
      if (res.status === 200 || res.status === 304) {
        setTimeout(() => showToast("Committed"), 1000);
      }
    });
    showToast("Committing...");
  }

  function saveAfterDelay() {
    if (this.saveTimer) {
      window.clearTimeout(saveTimer);
      this.saveTimer = null;
    }

    this.saveTimer = setTimeout(async function () {
      await fetch("/save", {
        method: "POST",
        body: document.documentElement.innerHTML,
      }).then((res) => {
        if (res.status === 204) {
          showToast("Saved");
        }
      });
    }, 2000);
    showToast("Saving...");
  }

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
      console.log("drop");
      saveAfterDelay();
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

  function filerOnValueOrPlaceholder(el, value) {
    let placeholder = el.getAttribute("placeholder");
    return (
      el.value.trim() == value || (placeholder && placeholder.trim() == value)
    );
  }

  function addMouseOverListener(input) {
    input.addEventListener("mouseover", (event) => {
      // find all inputs with same value and change background
      let mouseoverValue = input.getAttribute("value");
      $(".assignment-input")
        .filter((_, el) => filerOnValueOrPlaceholder(el, mouseoverValue))
        .addClass("search-highlight");
    });
  }

  function addMouseoutListener(input) {
    input.addEventListener("mouseout", (event) => {
      // find all inputs with same value and change background
      let mouseoverValue = input.getAttribute("value").trim();
      $(".assignment-input")
        .filter((_, el) => filerOnValueOrPlaceholder(el, mouseoverValue))
        .removeClass("search-highlight");
    });
  }

  function clearHighlights() {
    $(".assignment-input").removeClass("search-highlight");
  }

  function setupInput(input) {
    input.setSelectionRange(-1, -1);
    addInputListener(input);
    addMouseOverListener(input);
    addMouseoutListener(input);
  }

  let inputs = document.querySelectorAll("input");
  inputs.forEach(function (input) {
    setupInput(input);
  });

  document.getElementById("download-pdf").onclick = async function () {
    window.location = "/pdf";
  };

  document.getElementById("commit-schedule").onclick = commit;

  keepDatalistOptions(".month");
  keepDatalistOptions(".keep-datalist");

  function keepDatalistOptions(selector = "") {
    // select all input fields by datalist attribute or by class/id
    selector = !selector ? "input[list]" : selector;
    let datalistInputs = document.querySelectorAll(selector);
    if (datalistInputs.length) {
      for (let i = 0; i < datalistInputs.length; i++) {
        let input = datalistInputs[i];
        input.addEventListener("input", function (e) {
          // e.target.setAttribute("placeholder", e.target.value);
          // lastValue = e.target.value;
        });
        input.addEventListener("change", function (e) {
          // console.log("changed");
          e.target.setAttribute("placeholder", e.target.value);
          dirty = lastValue !== e.target.value;
        });
        input.addEventListener("focus", function (e) {
          // console.log("focus");
          e.target.setAttribute("placeholder", e.target.value);
          lastValue = e.target.value;
          e.target.value = "";
        });
        input.addEventListener("blur", function (e) {
          e.target.value = e.target.getAttribute("placeholder");
          if (dirty) {
            // console.log("dirty blur: {}", e.target.value);
            dirty = false;
            saveAfterDelay();
          }
        });
        input.addEventListener("keyup", function (e) {
          console.log(`keyup: ${e.key}`);
          if (e.key === "Enter" || e.keyCode === 13) {
            // autocomplete using first option in list
            autocompleteDatalist(input);
            // activate blur to save
            document.activeElement.blur();
            // reset highlights
          }
        });
      }
    }
  }

  function autocompleteDatalist(input) {
    const datalist = input.getAttribute("list");
    const options = Array.from(
      document.querySelector(`datalist#${datalist}`).options
    ).map(function (el) {
      return el.value;
    });
    var relevantOptions = options.filter(function (option) {
      return option.toLowerCase().includes(input.value.toLowerCase());
    });
    if (relevantOptions.length > 0) {
      input.placeholder = relevantOptions.shift();
      input.innerHTML = input.placeholder;
      input.setAttribute("value", input.placeholder);
      console.log(`setting ${input.placeholder}`);
    }
  }
});
