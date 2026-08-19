(function () {
  "use strict";

  function button(label, action) {
    const element = document.createElement("button");
    element.type = "button";
    element.className = "btn btn-sm";
    element.textContent = label;
    element.addEventListener("click", action);
    return element;
  }

  function byteSize(value) {
    return new TextEncoder().encode(value).length;
  }

  function initialize(textarea) {
    if (textarea.dataset.jsonEditorInitialized === "true") {
      return;
    }
    textarea.dataset.jsonEditorInitialized = "true";

    const toolbar = document.createElement("div");
    toolbar.className = "json-editor-toolbar";

    const status = document.createElement("span");
    status.className = "json-editor-status";
    status.setAttribute("aria-live", "polite");

    textarea.parentNode.insertBefore(toolbar, textarea);

    const editor = window.CodeMirror.fromTextArea(textarea, {
      autoCloseBrackets: true,
      foldGutter: true,
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
      indentUnit: 2,
      indentWithTabs: false,
      lineNumbers: true,
      lineWrapping: false,
      matchBrackets: true,
      mode: { name: "javascript", json: true },
      tabSize: 2,
    });
    editor.getWrapperElement().dataset.jsonCodeEditor = "true";
    textarea.jsonEditor = editor;

    function parse() {
      editor.save();
      try {
        const value = JSON.parse(editor.getValue());
        status.dataset.state = "valid";
        status.textContent = `Valid JSON · ${byteSize(editor.getValue())} B`;
        return value;
      } catch (error) {
        status.dataset.state = "invalid";
        status.textContent = error.message;
        return undefined;
      }
    }

    toolbar.appendChild(
      button("Format", function () {
        const value = parse();
        if (value !== undefined) {
          editor.setValue(JSON.stringify(value, null, 2));
          editor.focus();
        }
      }),
    );
    toolbar.appendChild(
      button("Minify", function () {
        const value = parse();
        if (value !== undefined) {
          editor.setValue(JSON.stringify(value));
          editor.focus();
        }
      }),
    );
    toolbar.appendChild(status);

    editor.on("change", parse);
    parse();

    if (textarea.form) {
      textarea.form.addEventListener("submit", function (event) {
        if (parse() === undefined) {
          event.preventDefault();
          editor.focus();
        }
      });
    }
  }

  document.querySelectorAll("textarea[data-json-editor]").forEach(initialize);
})();
