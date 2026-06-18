const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
      }
    });
  },
  { threshold: 0.12 }
);

document.querySelectorAll(".section-reveal").forEach((section) => {
  revealObserver.observe(section);
});

document.querySelectorAll(".timeline li").forEach((item) => {
  const button = item.querySelector(".timeline-step");
  button.addEventListener("click", () => {
    document.querySelectorAll(".timeline li").forEach((other) => {
      other.classList.remove("active");
    });
    item.classList.add("active");
  });
});

const sourceFiles = window.CITRUS_SOURCE_FILES ?? [];
const sourceTree = document.querySelector("[data-source-tree]");
const sourceBrowser = document.querySelector("[data-source-browser]");
const sourceCount = document.querySelector("[data-source-count]");

function groupSourceFiles(files) {
  return files.reduce((groups, file) => {
    if (!groups.has(file.group)) {
      groups.set(file.group, []);
    }
    groups.get(file.group).push(file);
    return groups;
  }, new Map());
}

function createSymbolList(symbols) {
  const list = document.createElement("span");
  list.className = "source-symbols";

  symbols.slice(0, 6).forEach((symbol) => {
    const item = document.createElement("span");
    item.textContent = symbol;
    list.appendChild(item);
  });

  if (symbols.length > 6) {
    const more = document.createElement("span");
    more.textContent = `+${symbols.length - 6}`;
    list.appendChild(more);
  }

  return list;
}

function buildSourceTree(files) {
  const groups = groupSourceFiles(files);

  groups.forEach((items, groupName) => {
    const group = document.createElement("div");
    group.className = "source-group";

    const title = document.createElement("div");
    title.className = "source-group-title";
    title.textContent = groupName;
    group.appendChild(title);

    items.forEach((file) => {
      const button = document.createElement("button");
      button.className = "source-link";
      button.type = "button";
      button.textContent = file.path.replace("src/citrus/", "");
      button.addEventListener("click", () => {
        const panel = document.getElementById(sourcePanelId(file.path));
        if (!panel) return;

        document.querySelectorAll(".source-link").forEach((link) => {
          link.classList.remove("active");
        });
        button.classList.add("active");
        panel.open = true;
        panel.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      group.appendChild(button);
    });

    sourceTree.appendChild(group);
  });
}

function sourcePanelId(path) {
  return `source-${path.replace(/[^a-zA-Z0-9]+/g, "-")}`;
}

function buildSourcePanels(files) {
  sourceBrowser.replaceChildren();

  files.forEach((file, index) => {
    const panel = document.createElement("details");
    panel.className = "source-file-panel";
    panel.id = sourcePanelId(file.path);
    panel.open = index < 2;

    const summary = document.createElement("summary");
    const copy = document.createElement("span");
    const path = document.createElement("span");
    const description = document.createElement("span");
    const code = document.createElement("code");
    const pre = document.createElement("pre");

    path.className = "source-path";
    path.textContent = file.path;
    description.className = "source-description";
    description.textContent = file.description;
    copy.append(path, description);

    summary.append(copy, createSymbolList(file.symbols));

    pre.className = "source-code";
    code.className = "language-python";
    code.textContent = "Loading source...";
    pre.appendChild(code);

    panel.append(summary, pre);
    sourceBrowser.appendChild(panel);

    loadSourceCode(file.path, code, file.content);
  });
}

async function loadSourceCode(path, codeElement, embeddedContent) {
  if (typeof embeddedContent === "string") {
    renderSourceCode(codeElement, embeddedContent, path);
    return;
  }

  try {
    const response = await fetch(`../${path}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    renderSourceCode(codeElement, await response.text(), path);
  } catch (error) {
    if (typeof embeddedContent === "string") {
      renderSourceCode(codeElement, embeddedContent, path);
      return;
    }

    codeElement.textContent =
      `无法加载 ${path}

` +
      "当前浏览器阻止了本地源码读取。请在项目根目录运行静态服务器：" +
      "python3 -m http.server 8765，然后打开 http://127.0.0.1:8765/site/。\n\n" +
      `错误详情：${error.message}`;
  }
}

function renderSourceCode(codeElement, source, path) {
  codeElement.classList.toggle("language-python", path.endsWith(".py"));
  codeElement.innerHTML = path.endsWith(".py")
    ? highlightPython(source)
    : escapeHtml(source);
}

function highlightPython(source) {
  const keywords = new Set([
    "and",
    "as",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
  ]);
  const constants = new Set(["False", "None", "True"]);
  const builtins = new Set([
    "Any",
    "BaseModel",
    "Field",
    "Literal",
    "Protocol",
    "Sequence",
    "dict",
    "getattr",
    "isinstance",
    "json",
    "list",
    "object",
    "str",
  ]);

  return source
    .split("\n")
    .map((line) => highlightPythonLine(line, { keywords, constants, builtins }))
    .join("\n");
}

function highlightPythonLine(line, vocabulary) {
  let html = "";
  let index = 0;
  let expectDefinitionName = false;

  while (index < line.length) {
    const char = line[index];
    const stringStart = readPythonStringStart(line, index);

    if (char === "#") {
      html += token("comment", line.slice(index));
      break;
    }

    if (stringStart) {
      const end = findStringEnd(line, stringStart);
      html += token("string", line.slice(index, end));
      index = end;
      continue;
    }

    if (char === "@" && isIdentifierStart(line[index + 1])) {
      const end = readIdentifierEnd(line, index + 1);
      html += token("decorator", line.slice(index, end));
      index = end;
      continue;
    }

    if (/\d/.test(char)) {
      const match = line.slice(index).match(/^\d[\d_]*(?:\.\d[\d_]*)?/);
      html += token("number", match[0]);
      index += match[0].length;
      continue;
    }

    if (isIdentifierStart(char)) {
      const end = readIdentifierEnd(line, index);
      const word = line.slice(index, end);

      if (expectDefinitionName) {
        html += token("definition", word);
        expectDefinitionName = false;
      } else if (word === "def" || word === "class") {
        html += token("keyword", word);
        expectDefinitionName = true;
      } else if (vocabulary.keywords.has(word)) {
        html += token("keyword", word);
      } else if (vocabulary.constants.has(word)) {
        html += token("constant", word);
      } else if (vocabulary.builtins.has(word)) {
        html += token("builtin", word);
      } else {
        html += escapeHtml(word);
      }

      index = end;
      continue;
    }

    html += escapeHtml(char);
    index += 1;
  }

  return html;
}

function readPythonStringStart(line, index) {
  let prefixEnd = index;
  while (/[rRuUbBfF]/.test(line[prefixEnd] ?? "") && prefixEnd - index < 3) {
    prefixEnd += 1;
  }

  const quote = line[prefixEnd];
  if (quote !== "'" && quote !== '"') return null;
  if (prefixEnd > index && index > 0 && isIdentifierPart(line[index - 1])) return null;

  const triple = line.slice(prefixEnd, prefixEnd + 3) === quote.repeat(3);
  return {
    start: index,
    contentStart: prefixEnd,
    quote,
    delimiterLength: triple ? 3 : 1,
  };
}

function findStringEnd(line, stringStart) {
  const delimiter = stringStart.quote.repeat(stringStart.delimiterLength);
  let index = stringStart.contentStart + stringStart.delimiterLength;

  while (index < line.length) {
    if (
      stringStart.delimiterLength === 1 &&
      line[index] === "\\" &&
      index + 1 < line.length
    ) {
      index += 2;
      continue;
    }

    if (line.slice(index, index + stringStart.delimiterLength) === delimiter) {
      return index + stringStart.delimiterLength;
    }

    index += 1;
  }

  return line.length;
}

function readIdentifierEnd(line, index) {
  let end = index + 1;
  while (isIdentifierPart(line[end])) {
    end += 1;
  }
  return end;
}

function isIdentifierStart(char) {
  return /[A-Za-z_]/.test(char ?? "");
}

function isIdentifierPart(char) {
  return /[A-Za-z0-9_]/.test(char ?? "");
}

function token(type, value) {
  return '<span class="tok-' + type + '">' + escapeHtml(value) + "</span>";
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

if (sourceTree && sourceBrowser && sourceCount) {
  sourceCount.textContent = `${sourceFiles.length} files`;
  buildSourceTree(sourceFiles);
  buildSourcePanels(sourceFiles);
}
